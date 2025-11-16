# worker.py
import time
import sqlite3
import json
from database import (
    DB_NAME, get_next_job, update_job_progress,
    mark_job_done, mark_job_failed,
    save_email, delete_email_from_db, get_all_emails
)
from fetch_emails import gmail_connect, get_email_details, fetch_all_emails
from classifier import classify_email

import pandas as pd

SLEEP_WHEN_EMPTY = 10 # Check for new jobs every 10 seconds

# --- Helper to make terminal output clear ---
def worker_log(message):
    print(f"[WORKER] {message}")
# -------------------------------------------

def run_fetch_job(service, job):
    job_id = job['id']
    try:
        params = json.loads(job['parameters'])
        query = params.get('query', '')
        worker_log(f"Job {job_id} (FETCH) started. Query: '{query}'")
        update_job_progress(job_id, f"Fetching email list for query: '{query}'...")
        
        email_ids = fetch_all_emails(service, gmail_query=query)
        total_to_fetch = len(email_ids)
        if total_to_fetch == 0:
            mark_job_done(job_id, "No new emails found for this query.")
            worker_log(f"Job {job_id} (FETCH) done. No new emails found.")
            return

        update_job_progress(job_id, f"Found {total_to_fetch} new emails. Fetching details...")

        for i, email_id in enumerate(email_ids):
            try:
                data = get_email_details(service, email_id)
                data["category"] = classify_email(data["subject"], data["body"], data["sender"])
                save_email(data)
                
                if (i + 1) % 10 == 0:
                    update_job_progress(job_id, f"Processed {i+1} / {total_to_fetch} emails.")
            
            except Exception as e:
                worker_log(f"Failed to process email {email_id}: {e}")

        mark_job_done(job_id, f"Successfully fetched and classified {total_to_fetch} emails.")
        worker_log(f"Job {job_id} (FETCH) finished. Processed {total_to_fetch} emails.")

    except Exception as e:
        worker_log(f"Job {job_id} (FETCH) failed: {e}")
        mark_job_failed(job_id, str(e))


def run_delete_job(service, job):
    job_id = job['id']
    try:
        params = json.loads(job['parameters'])
        categories = params.get('categories', [])
        
        if not categories:
            mark_job_failed(job_id, "No categories specified for deletion.")
            return
        
        worker_log(f"Job {job_id} (DELETE) started. Categories: {categories}")
        update_job_progress(job_id, f"Finding all emails in categories: {categories}")

        all_emails = get_all_emails()
        df = pd.DataFrame(all_emails, columns=[
            "id", "subject", "sender", "body", "category", "size", "datetime"
        ])
        
        target_emails = df[df['category'].isin(categories)].copy()
        
        emails_to_delete = []
        for _, row in target_emails.iterrows():
            emails_to_delete.append({"id": row["id"], "size": row["size"]})
        
        total_to_delete = len(emails_to_delete)
        if total_to_delete == 0:
            mark_job_done(job_id, "No emails found matching the criteria.")
            worker_log(f"Job {job_id} (DELETE) done. No emails found to delete.")
            return

        update_job_progress(job_id, f"Found {total_to_delete} emails to delete. Starting batches...")
        
        BATCH_SIZE = 25
        SLEEP_BETWEEN_BATCHES = 10
        deleted_count = 0

        for i in range(0, total_to_delete, BATCH_SIZE):
            batch = emails_to_delete[i:i+BATCH_SIZE]
            
            for email in batch:
                try:
                    service.users().messages().delete(
                        userId="me",
                        id=email["id"]
                    ).execute()
                    delete_email_from_db(email["id"])
                    deleted_count += 1
                except Exception as e:
                    worker_log(f"Failed to delete email {email['id']}: {e}")
            
            update_job_progress(job_id, f"Deleted {deleted_count} / {total_to_delete} emails...")
            worker_log(f"Job {job_id} (DELETE): Batch complete. {deleted_count}/{total_to_delete} done. Sleeping...")
            time.sleep(SLEEP_BETWEEN_BATCHES)

        mark_job_done(job_id, f"Successfully deleted {deleted_count} emails.")
        worker_log(f"Job {job_id} (DELETE) finished. Deleted {deleted_count} emails.")
    
    except Exception as e:
        worker_log(f"Job {job_id} (DELETE) failed: {e}")
        mark_job_failed(job_id, str(e))


def run_worker():
    """The main loop for the background worker."""
    worker_log("Starting background job worker...")
    try:
        service = gmail_connect()
        worker_log("Gmail connection successful.")
    except Exception as e:
        worker_log(f"CRITICAL: Could not connect to Gmail. {e}")
        worker_log("Worker will not run.")
        return

    worker_log("Worker is now running. Checking for jobs...")
    
    while True:
        try:
            job = get_next_job()
            
            if not job:
                # No pending jobs, wait a bit
                time.sleep(SLEEP_WHEN_EMPTY)
                continue
                
            worker_log(f"Found new job (ID: {job['id']}, Type: {job['job_type']}). Processing...")

            if job['job_type'] == "FETCH":
                run_fetch_job(service, job)
            elif job['job_type'] == "DELETE":
                run_delete_job(service, job)
            else:
                worker_log(f"Unknown job type: {job['job_type']}. Failing job.")
                mark_job_failed(job['id'], f"Unknown job type: {job['job_type']}")
            
            worker_log(f"Job {job['id']} finished. Looking for next job...")

        except KeyboardInterrupt:
            worker_log("Shutdown signal received. Exiting worker...")
            break
        except Exception as e:
            worker_log(f"An unexpected error occurred in the main loop: {e}")
            worker_log("Restarting loop in 30 seconds...")
            time.sleep(30)

if __name__ == "__main__":
    # This allows you to still run `python worker.py` manually if you want
    run_worker()