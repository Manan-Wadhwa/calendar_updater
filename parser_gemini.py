import requests
import json
from typing import List, Dict, Optional

# Updated to use Gemini 1.5 Flash
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def extract_events_gemini(msg: str, api_key: str) -> List[Dict]:
    """
    Uses Gemini API to extract events from text.
    Returns list of event dicts with title, date, time, venue, form_link.
    """
    if not api_key:
        print("No Gemini API key provided")
        return []

    # Refined prompt focusing on Unicode and strict date extraction
    prompt = f"""
    TASK: Extract quiz event announcements from the following WhatsApp message.

    MESSAGE CONTENT:
    {msg}

    EXTRACTION RULES:
    - Focus only on formal quiz announcements, not casual conversations
    - All fields (title, venue, etc.) must preserve Unicode characters and be output as valid UTF-8 JSON
    - The date field MUST be in strict ISO 8601 format: YYYY-MM-DD (e.g., 2025-04-21)
    - Use 24-hour time format for clarity (e.g., 14:30 instead of 2:30 PM)
    - Include complete quiz titles exactly as written (preserve Unicode)
    - Extract only full, valid URLs for registration links

    EXTRACT THESE FIELDS:
    - title: The exact name of the quiz event (preserve Unicode)
    - date: In strict ISO 8601 format (YYYY-MM-DD)
    - time: In HH:MM format using 24-hour time
    - venue: The complete location information (preserve Unicode)
    - form_link: The full registration URL

    RESPONSE FORMAT:
    Return a JSON object with these exact fields. For multiple events, return an array.

    EXAMPLE:
    {{
      "title": "राजनीति मंथन '25 – An Indian Politics Quiz",
      "date": "2025-04-21",
      "time": "13:30",
      "venue": "Hindu College Auditorium",
      "form_link": "https://forms.gle/example"
    }}

    IMPORTANT: Return ONLY valid JSON (UTF-8, preserving all Unicode) without any explanations or additional text.
    """

    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.3,  # Slightly increased temperature for better field extraction
            "topK": 40,
            "topP": 0.95,  # Increased for more flexibility
            "maxOutputTokens": 1024,
        }
    }

    try:
        # Debug info
        print(f"Using Gemini API URL: {GEMINI_URL}")
        
        # Make API request
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            print(f"Gemini API error: {response.status_code} - {error_msg}")
            
            # Try fallback to gemini-pro if gemini-1.5-flash fails
            if "gemini-1.5-flash" in GEMINI_URL:
                print("Attempting with fallback model: gemini-pro")
                fallback_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
                fallback_response = requests.post(
                    f"{fallback_url}?key={api_key}",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if fallback_response.status_code == 200:
                    response = fallback_response
                else:
                    return []
            else:
                return []
        
        # Extract the response text
        response_data = response.json()
        if 'candidates' not in response_data or not response_data['candidates']:
            print("No candidates in Gemini response")
            return []
            
        content = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # Clean the content to extract just the JSON
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1]
            if "```" in content:
                content = content.split("```")[0]
        elif "```" in content:
            parts = content.split("```")
            if len(parts) >= 3:  # Has opening and closing ticks
                content = parts[1]
            else:
                content = parts[0]  # Use whatever is there
        content = content.strip()
        
        # Try to parse the JSON response
        try:
            events = json.loads(content)
            if isinstance(events, dict):
                events = [events]  # Convert single event to list
                
            # Normalize and validate event structure
            valid_events = []
            for event in events:
                normalized_event = {}
                
                # Normalize field names
                for key, value in event.items():
                    normalized_key = key.lower()
                    # Handle common key variations
                    if normalized_key in ["registration_link", "reg_link", "link", "registration"]:
                        normalized_event["form_link"] = value
                    elif normalized_key == "location":
                        normalized_event["venue"] = value
                    elif normalized_key == "name":
                        normalized_event["title"] = value
                    else:
                        normalized_event[normalized_key] = value
                
                # Check if event has required fields
                if all(k in normalized_event for k in ["title", "date", "time"]):
                    # Make sure venue exists
                    if "venue" not in normalized_event:
                        normalized_event["venue"] = ""
                    # Make sure form_link exists  
                    if "form_link" not in normalized_event:
                        normalized_event["form_link"] = ""
                        
                    valid_events.append(normalized_event)
                else:
                    print(f"Invalid event structure (missing required fields): {event}")
                    
            return valid_events
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from Gemini response: {e}")
            print(f"Response content: {content}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in Gemini parser: {e}")
        return []
