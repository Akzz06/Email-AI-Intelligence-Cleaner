# classifier.py
from groq import Groq
import os # Add this to the top of your file

# This will read the key from your computer's "environment"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set. Please set this environment variable.")

client = Groq(api_key=GROQ_API_KEY)


NEWSLETTER_KEYWORDS = [
    "unsubscribe", "newsletter", "update", "digest"
]

PROMO_KEYWORDS = [
    "offer", "sale", "discount", "deal", "promo", "premium",
    "spotify", "dazn", "myntra", "swiggy", "zomato", "amazon sale"
]

SPAM_KEYWORDS = ["win", "lottery", "urgent", "claim", "credit card", "bitcoin"]


def rule_based_classify(subject, sender, body):
    text = f"{subject} {sender} {body}".lower()

    if any(k in text for k in SPAM_KEYWORDS):
        return "Spam"

    if any(k in text for k in PROMO_KEYWORDS):
        return "Promotional"

    if any(k in text for k in NEWSLETTER_KEYWORDS):
        return "Newsletter"

    return None


def llm_classify(subject, body, sender):
    prompt = f"""
Classify this email into ONE category:
Work, Personal, Priority, Newsletter, Promotional, Spam.

Subject: {subject}
Body: {body[:200]}
Sender: {sender}

Return only category name.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()


def classify_email(subject, body, sender):
    rule = rule_based_classify(subject, sender, body)
    if rule:
        return rule

    return llm_classify(subject, body, sender)
