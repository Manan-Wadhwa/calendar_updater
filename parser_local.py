import re
from dateparser import parse as dp
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def extract_events_local(msg: str) -> List[Dict]:
    """
    Fallback local parser: looks for quiz events in text.
    Returns list of event dicts with title, date (YYYY-MM-DD), time (HH:MM), venue, form_link.
    """
    events = []
    if not msg or "quiz" not in msg.lower():
        return []

    # Normalize text: replace newlines with spaces and clean up
    text = " ".join(msg.splitlines())
    text = re.sub(r'\s+', ' ', text).strip()
    print(f"Processing text: {text}")  # Debug output

    # Look for date patterns
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # DD Month YYYY
        r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',  # DD FullMonth YYYY
        r'(\d{1,2}(?:st|nd|rd|th)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # DDst Month YYYY
    ]
    
    date_match = None
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            print(f"Found date: {date_match.group(1)}")  # Debug output
            break
    
    # Look for time patterns
    time_patterns = [
        r'(\d{1,2}:\d{2}\s?[APMapm]{2})',  # 9:00 AM or 09:00AM
        r'(\d{1,2}\s?[APMapm]{2})',        # 9 AM or 9AM
        r'(\d{1,2}:\d{2})',                # 9:00 (assume 24h format)
    ]
    
    time_match = None
    for pattern in time_patterns:
        time_match = re.search(pattern, text, re.IGNORECASE)
        if time_match:
            print(f"Found time: {time_match.group(1)}")  # Debug output
            break

    if not date_match or not time_match:
        print("No date or time found in message")  # Debug output
        return []

    try:
        # Parse date and time
        dt_str = f"{date_match.group(1)} {time_match.group(1)}"
        print(f"Parsing datetime: {dt_str}")  # Debug output
        dt = dp(dt_str)
        if not dt:
            print("Failed to parse datetime")  # Debug output
            return []
            
        # Get title (text up to the word 'quiz')
        title_match = re.search(r'(.*?quiz)', text, re.IGNORECASE)
        title = title_match.group(1).strip().title() if title_match else "Quiz Event"
        print(f"Found title: {title}")  # Debug output

        # Get venue (after 'Venue:' or 'Location:')
        venue_patterns = [
            r'Venue[:\-]\s*([^.\n]+)',
            r'Location[:\-]\s*([^.\n]+)',
            r'at\s+([^.\n]+?)(?:\s+(?:on|at|from)\s+\d|$)',
            r'in\s+([^.\n]+?)(?:\s+(?:on|at|from)\s+\d|$)',
        ]
        
        venue = ""
        for pattern in venue_patterns:
            venue_match = re.search(pattern, text, re.IGNORECASE)
            if venue_match:
                venue = venue_match.group(1).strip()
                print(f"Found venue: {venue}")  # Debug output
                break

        # Get form link (any URL)
        link_match = re.search(r'(https?://\S+)', text)
        link = link_match.group(1) if link_match else ""
        if link:
            print(f"Found link: {link}")  # Debug output

        events.append({
            "title": title,
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "venue": venue,
            "form_link": link
        })
        print(f"Created event: {events[-1]}")  # Debug output
        
    except Exception as e:
        print(f"Error parsing event: {e}")
        return []

    return events
