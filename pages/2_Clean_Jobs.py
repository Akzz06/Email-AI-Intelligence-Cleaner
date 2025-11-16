# pages/2_Clean_Jobs.py

import streamlit as st
import pandas as pd
import json
from database import create_job, get_all_emails

st.title("🧹 Clean & Delete Emails")

# --- Navigation ---
col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 Go to Main Dashboard"):
        st.switch_page("app.py")
with col2:
    if st.button("🔎 Go to Fetch & Classify"):
        st.switch_page("pages/1_Fetch_Jobs.py")

st.divider()

st.info("Schedule a job to delete emails *that are already in your database*.")

def load_data():
    emails = get_all_emails()
    if not emails:
        return None
    df = pd.DataFrame(emails, columns=[
        "id", "subject", "sender", "body", "category", "size", "datetime"
    ])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

df = load_data()

if df is None:
    st.error("No emails found in the database. Please run a 'Fetch Job' first.")
    st.stop()

# --- Job Creation UI ---
all_categories = sorted(list(df['category'].unique()))
selected_categories = st.multiselect(
    "Select categories to delete (will delete ALL emails in category):",
    all_categories
)

# --- Live Calculation ---
if selected_categories:
    target_emails = df[df['category'].isin(selected_categories)].copy()
    total_emails_to_delete = len(target_emails)
    total_size_to_save = target_emails['size'].sum() / 1_000_000
    
    st.subheader("Deletion Preview")
    st.warning(f"This job will delete **{total_emails_to_delete}** emails, saving **{total_size_to_save:.2f} MB**.")
    
    with st.expander("Click to see full list of emails to be deleted"):
        st.dataframe(target_emails[['datetime', 'subject', 'sender', 'category']], use_container_width=True)
else:
    st.info("Select categories to see a deletion preview.")

# --- Button to create job ---
if st.button("Schedule Background Delete Job", type="primary"):
    if not selected_categories:
        st.error("Please select at least one category.")
    else:
        params = json.dumps({
            "categories": selected_categories
        })
        job_id = create_job("DELETE", params)
        st.success(f"Successfully created 'DELETE' job (ID: {job_id}).")
        st.info("You can go to the Main Dashboard to monitor its progress.")