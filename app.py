# app.py

import streamlit as st
import threading
import time
from database import init_db
from worker import run_worker # Import the worker's main function
import pandas as pd
import sqlite3
from database import DB_NAME
import json
import re
import datetime

st.set_page_config(page_title="Email Intelligence", layout="centered")

# --- Auto-start the Background Worker ---
@st.cache_resource
def start_worker_thread():
    print("--- Starting background worker thread ---")
    # Create a thread to run the worker function
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    return worker_thread

# Initialize the DB (will create 'jobs' table if not exists)
init_db()

# Start the worker (this will only run once)
start_worker_thread()
# ----------------------------------------

st.title("📬 Welcome to Email Intelligence")
st.write("Your smart assistant to fetch, classify, and clean your inbox.")

st.divider()

st.header("What would you like to do?")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔎 Fetch & Classify New Emails", use_container_width=True):
        st.switch_page("pages/1_Fetch_Jobs.py")

with col2:
    if st.button("🧹 Clean & Delete Old Emails", use_container_width=True):
        st.switch_page("pages/2_Clean_Jobs.py")

st.divider()

st.subheader("🤖 Background Job Status")

# --- Function to get raw job data ---
def get_job_status():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10") # Show 10 recent
    jobs = c.fetchall()
    conn.close()
    return [dict(job) for job in jobs]

# --- NEW Function to clean up the data for display ---
def process_jobs_for_display(jobs):
    processed_jobs = []
    for job in jobs:
        
        display_job = {
            "ID": job['id'],
            "Job Type": job['job_type'],
            "Status": job['status'],
        }

        # --- Parse Parameters for Date ---
        date_str = "N/A" # Default
        try:
            params = json.loads(job['parameters'])
            if 'query' in params and 'before:' in params['query']:
                # Extract '2025/05/01' from '{"query": "before:2025/05/01"}'
                date_val = params['query'].split(':')[-1]
                # Convert '2025/05/01' to '01-May-25'
                date_obj = datetime.datetime.strptime(date_val, "%Y/%m/%d").date()
                date_str = date_obj.strftime("%d-%b-%y")
        except Exception:
            pass # Keep "N/A" if parsing fails
        
        display_job['Fetched Before'] = date_str

        # --- Parse Progress Message for Count ---
        count = 0 # Default
        try:
            # Extract '259' from 'Successfully fetched... 259 emails.'
            match = re.search(r"\d+", job['progress_message'])
            if match:
                count = int(match.group(0))
        except Exception:
            pass # Keep 0 if parsing fails
            
        display_job['Email Count'] = count
        
        processed_jobs.append(display_job)
        
    return processed_jobs
# --- END OF NEW FUNCTION ---


jobs = get_job_status()

if not jobs:
    st.write("No background jobs have been run yet.")
else:
    # Process the data to make it clean
    clean_jobs_data = process_jobs_for_display(jobs)
    
    # Display the clean data
    st.dataframe(pd.DataFrame(clean_jobs_data), use_container_width=True)

    # Add a refresh button for the job list
    if st.button("Refresh Job List"):
        st.rerun()