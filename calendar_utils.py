import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from event_utils import EventExtractor

def save_gemini_output(events: List[Dict], filename: str = "gemini_events.json") -> None:
    """Save Gemini output (list of event dicts) to a JSON file (UTF-8, Unicode-safe)."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def load_gemini_output(filename: str = "gemini_events.json") -> List[Dict]:
    """Load Gemini output from a JSON file."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def load_calendar_service(creds_path: str):
    """
    Loads Google Calendar API service using service account credentials.
    
    Args:
        creds_path: Path to service-account JSON file
        
    Returns:
        Google Calendar API service object
        
    Raises:
        FileNotFoundError: If creds_path doesn't exist
        ValueError: If JSON file is invalid
        Exception: For other errors
    """
    if not os.path.isfile(creds_path):
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")
        
    try:
        with open(creds_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
            
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        
        return build("calendar", "v3", credentials=creds)
        
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in credentials file")
    except Exception as e:
        raise Exception(f"Failed to load calendar service: {e}")

def event_exists(service, calendar_id: str, title: str, start_datetime: datetime) -> bool:
    """
    Check if an event with the same title and start time already exists in the calendar.
    """
    iso_start = start_datetime.isoformat() + "+05:30"  # Asia/Kolkata offset
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=iso_start,
            timeMax=(start_datetime + timedelta(minutes=1)).isoformat() + "+05:30",
            q=title,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        for event in events:
            if event.get('summary', '').strip() == title.strip():
                return True
        return False
    except Exception as e:
        print(f"Error checking for duplicate event: {e}")
        return False

def add_events_to_calendar(events: List[Dict], service, calendar_id: str = 'primary', ignore_duplicates: bool = False) -> List[str]:
    """
    Add events to Google Calendar from Gemini output JSON.
    Returns list of created event IDs.
    When ignore_duplicates is False, it checks for duplicates before adding.
    """
    created_events = []
    for event in events:
        try:
            # Parse date and time (expects strict ISO and 24-hour time from Gemini)
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            event_time = datetime.strptime(event['time'], '%H:%M').time()
            start_datetime = datetime.combine(event_date, event_time)
            end_datetime = start_datetime + timedelta(hours=1)  # Default 1 hour duration

            # Check for duplicates unless ignoring duplicates
            if not ignore_duplicates and event_exists(service, calendar_id, event['title'], start_datetime):
                print(f"Skipping duplicate event: {event['title']} at {start_datetime}")
                continue

            # Compose description with venue and registration link if present
            description = event.get('description', '')
            if event.get('venue'):
                description += f"\nVenue: {event['venue']}"
            if event.get('registration_link'):
                description += f"\nRegistration Link: {event['registration_link']}"

            event_body = {
                'summary': event['title'],
                'location': event.get('venue', ''),
                'description': description.strip(),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': True,
                },
            }

            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()
            created_events.append(created_event['id'])
        except Exception as e:
            print(f"Failed to add event {event.get('title', '')}: {str(e)}")
            continue
    return created_events

# Example usage:
# 1. Save Gemini output to file after parsing
# save_gemini_output(gemini_events, "gemini_events.json")
#
# 2. Later, load and add to calendar:
# events = load_gemini_output("gemini_events.json")
# service = load_calendar_service("path/to/credentials.json")
# add_events_to_calendar(events, service)
