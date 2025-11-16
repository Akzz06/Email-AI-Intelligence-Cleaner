# fetch_emails.py

from __future__ import print_function
import os.path
import base64
import datetime
from datetime import timedelta # Add this

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from database import email_exists

print("Token path:", os.path.abspath("token.json"))

SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify"
]

# --- (gmail_connect and safe_list_request are unchanged) ---

def gmail_connect():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def safe_list_request(service, **kwargs):
    try:
        return service.users().messages().list(**kwargs).execute()
    except HttpError:
        return None
    except Exception:
        return None

def get_total_email_count(service):
    try:
        res = safe_list_request(
            service,
            userId="me",
            maxResults=1
        )
        if res is None:
            return None
        return res.get("resultSizeEstimate", 0)
    except:
        return None


# --- (get_email_details is unchanged) ---
def get_email_details(service, msg_id):
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    headers = msg["payload"].get("headers", [])
    subject = sender = date = "Unknown"
    internal_date = msg.get("internalDate")
    size_estimate = msg.get("sizeEstimate", 0)

    for h in headers:
        if h["name"] == "Subject":
            subject = h["value"]
        elif h["name"] == "From":
            sender = h["value"]
        elif h["name"] == "Date":
            date = h["value"]

    try:
        dt = datetime.datetime.fromtimestamp(int(internal_date) / 1000)
        dt_iso = dt.isoformat()
    except:
        dt_iso = datetime.datetime.utcnow().isoformat()

    body = ""
    try:
        parts = msg["payload"].get("parts", [])
        for p in parts:
            if p.get("mimeType") == "text/plain":
                raw = p.get("body", {}).get("data")
                if raw:
                    body = base64.urlsafe_b64decode(raw).decode("utf-8", errors="ignore")
                    break
        if not body:
            raw = msg["payload"].get("body", {}).get("data")
            if raw:
                body = base64.urlsafe_b64decode(raw).decode("utf-8", errors="ignore")
    except:
        pass

    return {
        "id": msg_id,
        "subject": subject,
        "sender": sender,
        "date": date,
        "datetime": dt_iso,
        "size": size_estimate,
        "body": body[:800]
    }

# --- THIS FUNCTION IS HEAVILY EDITED ---
def fetch_all_emails(service, gmail_query="", limit=10000):
    """
    Fetches all email IDs matching a given Gmail query.
    Stops when 'limit' is reached.
    Returns a list of message IDs.
    """
    collected = []
    page_token = None

    while True:
        response = safe_list_request(
            service,
            userId="me",
            q=gmail_query,  # Use the query
            maxResults=100, # Fetch 100 at a time
            pageToken=page_token
        )

        if response is None:
            print("Error: Safe list request returned None. Stopping fetch.")
            break

        msgs = response.get("messages", [])
        if msgs:
            collected.extend(msgs)
        
        page_token = response.get("nextPageToken")

        if not page_token or len(collected) >= limit:
            break
            
    # We return the list to the worker, which will get details
    # We only skip emails that are *already in the DB*
    return [m['id'] for m in collected if not email_exists(m['id'])]


# --- ADD THIS NEW HELPER FUNCTION ---
def get_query_from_date(option, custom_date=None):
    """
    Generates a Gmail 'before:' query string from a date option.
    """
    today = datetime.date.today()
    query = ""
    
    if option == "Older than 2 months":
        target_date = today - timedelta(days=60)
        query = f"before:{target_date.strftime('%Y/%m/%d')}"
    
    elif option == "Older than 1 year":
        target_date = today - timedelta(days=365)
        query = f"before:{target_date.strftime('%Y/%m/%d')}"
    
    elif option == "Custom" and custom_date:
        query = f"before:{custom_date.strftime('%Y/%m/%d')}"
    
    return query