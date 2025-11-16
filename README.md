# 📧 AI-Inbox-Curator

A smart email assistant built with Streamlit and Groq. It uses an AI agent to automatically fetch, classify, and clean your Gmail inbox using a background worker.

## ✨ Features

* **Smart Fetching:** Fetches all emails older than a specific date.
* **AI Classification:** Uses the Groq API (Llama 3.1) to classify emails into categories like "Promotional," "Work," "Spam," etc.
* **Background Jobs:** A multi-threaded worker handles all heavy tasks, so the UI is always fast.
* **Simple UI:** A multi-page app to create "Fetch" and "Clean" jobs.
* **Safe Deletion:** Deletes emails in small, safe batches to avoid API rate limits.

## 🚀 How to Run This Project Locally

This app requires you to get your own API keys from Google and Groq.

### 1. Prerequisites

* Python 3.9+
* Git
* A Google Account
* A Groq AI Account

### 2. Setup Instructions

**Step 1: Clone the Repository**
```bash
git clone [https://github.com/Akzz06/Email-AI-Intelligence-Cleaner.git](https://github.com/Akzz06/Email-AI-Intelligence-Cleaner.git)
cd AI-Inbox-Curator
````

**Step 2: Install Dependencies**

```bash
pip install -r requirements.txt
```

**Step  3: Get Google API Credentials**
This app needs permission to read your email.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/welcome).
2.  Create a new project.
3.  Go to **APIs & Services \> Library** and enable the **Gmail API**.
4.  Go to **APIs & Services \> OAuth consent screen**.
      * Choose **Desktop app**.
      * Give it an app name (e.g., "My Streamlit Cleaner").
      * Add your email as a "Test User."
5.  Go to **APIs & Services \> Credentials**.
      * Click **Create Credentials \> OAuth client ID**.
      * Select **Desktop app** for the application type.
      * Click "Create."
      * Click "Download JSON" and save this file in your project folder as `credentials.json`.

**Step 4: Get Groq AI API Key**

1.  Go to [GroqCloud](https://console.groq.com/keys).
2.  Create a new API key.
3.  Copy the key.

**Step 5: Configure the App (Important)**

1.  In your terminal, **set the environment variable** for your key. This is safer than editing the code.
      * **Windows (Command Prompt):** `set GROQ_API_KEY=YOUR_KEY_HERE`
      * **macOS/Linux (Bash):** `export GROQ_API_KEY=YOUR_KEY_HERE`

**Step 6: Run the App**

1.  In your terminal (after setting the API key), run:
    ```bash
    streamlit run app.py
    ```
2.  The app will open. The **first time you use it**, it will pop open a Google login screen in your browser.
3.  Log in and grant the app permission.
4.  This will create a private `token.json` file, and the app will start working.

<!-- end list -->

```
```
