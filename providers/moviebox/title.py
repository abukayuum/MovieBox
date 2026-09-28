"""
Title sanitizer and formatter for MovieBox media items.
"""
import re

def clean_moviebox_title(raw_title: str) -> str:
    """Removes bracketed audio tags and cleans up extra whitespace."""
    if not raw_title:
        return "Unknown"
    # Remove tags like [Hindi], [Dual Audio], [Eng-Sub]
    cleaned = re.sub(r"\[.*?\]", "", raw_title)
    # Remove excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else raw_title.strip()

def extract_year(date_str: str) -> str:
    """Extracts a 4-digit year from date string or release date."""
    if not date_str:
        return ""
    match = re.search(r"\b(19\d\d|20\d\d)\b", str(date_str))
    return match.group(1) if match else ""
