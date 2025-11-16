# cleaner.py
import datetime

def should_delete(email, categories_selected):
    """
    categories_selected = list of categories user wants to auto-delete
    """

    category = email["category"]
    size = email["size"]
    now = datetime.datetime.now()
    age_days = (now - email["datetime"]).days

    # If user chose to delete this category → delete
    if category in categories_selected:
        return True, f"User selected auto-clean for {category}"

    # Default rules (optional)
    if category == "Spam":
        return True, "Spam Email"

    if category == "Newsletter" and age_days > 60:
        return True, f"Old Newsletter ({age_days} days)"

    if size > 5 * 1024 * 1024:
        return True, f"Large Email ({size/1_000_000:.1f}MB)"

    return False, None
