# pages/1_Fetch_Jobs.py

import streamlit as st
import json
import pandas as pd
from database import create_job, get_oldest_datetime, get_all_emails
import datetime

st.title("🔎 Fetch & Classify Emails")

# --- Navigation ---
col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 Go to Main Dashboard"):
        st.switch_page("app.py")
with col2:
    if st.button("🧹 Go to Clean & Delete"):
        st.switch_page("pages/2_Clean_Jobs.py")

st.divider()

# --- Smart Date Fetcher ---
oldest_date_str = get_oldest_datetime()
if oldest_date_str:
    oldest_date = datetime.datetime.fromisoformat(oldest_date_str).date()
    # Format date as "18 April 2023"
    formatted_date = oldest_date.strftime("%d %B %Y")
    st.success(f"You have already fetched all emails as old as: **{formatted_date}**")
    st.write("You can now fetch even older emails.")
    default_date = oldest_date
else:
    st.warning("You haven't fetched any emails yet.")
    default_date = datetime.date.today()

st.divider()

st.subheader("Fetch all emails older than a specific date")
custom_date = st.date_input(
    "Fetch all emails created before:",
    default_date
)

if st.button("Start Background Fetch Job", type="primary"):
    
    query = f"before:{custom_date.strftime('%Y/%m/%d')}"
    params = json.dumps({"query": query})
    job_id = create_job("FETCH", params)
    
    st.success(f"Successfully created 'FETCH' job (ID: {job_id}).")
    st.write(f"The worker is now fetching all emails matching: '{query}'.")
    st.info("You can go to the Main Dashboard to monitor its progress.")
    
st.divider()

# --- VIEW ALL FETCHED EMAILS (Moved here) ---
st.subheader("📧 All Fetched Emails")
emails = get_all_emails()

if len(emails) == 0:
    st.info("No emails fetched yet.")
else:
    with st.expander(f"Click to view all {len(emails)} fetched emails in your database"):
        df = pd.DataFrame(emails, columns=[
            "id", "subject", "sender", "body", "category", "size", "datetime"
        ])
        st.dataframe(df[['datetime', 'subject', 'sender', 'category', 'size']], use_container_width=True)