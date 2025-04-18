import requests
import json
from typing import List, Dict, Optional
import os
from datetime import datetime

class GeminiParser:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """Initialize Gemini parser with API key."""
        self.api_key = api_key
        self.model_name = model_name
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        self.headers = {
            "Content-Type": "application/json",
        }
        
    def extract_events(self, text: str) -> List[Dict]:
        """
        Extract quiz events from text using Gemini API.
        Returns list of event dictionaries.
        """
        if not self.api_key:
            print("Error: Gemini API key not provided")
            return []
            
        try:
            # Refined prompt focusing on strict ISO date and 24-hour time
            prompt = f"""
            Extract quiz event details from the following WhatsApp message content:

            {text}
            
            INSTRUCTIONS:
            - current date is {datetime.now().strftime('%Y-%m-%d')}
            - Focus only on quiz or competition announcements
            - Ignore system messages or personal conversations
            - Find specific, detailed information about quiz events
            - All fields must preserve Unicode and be valid UTF-8 JSON
            - Date must be in strict ISO 8601 format: YYYY-MM-DD (e.g., 2025-04-21). If year is missing, use the current year.
            - messages cannot be older than a month recheck dates accordingly.
            - If the date is not of 30 days in future or prior recheck for correct dates.
            - Time must be in strict 24-hour format: HH:MM (e.g., 13:30). If AM/PM is given, convert to 24-hour.
            -In case of venue being college auditorium, or room numbers or similar, please mention the college name also.
            For each quiz event you identify, extract:
            - title: The complete name of the quiz (preserve Unicode)
            - date: Strict ISO 8601 format (YYYY-MM-DD)
            - time: Strict 24-hour format (HH:MM)
            - venue: The exact location where the quiz will be held (preserve Unicode)
            - registration_link: The URL for registration (full URL only)
            Return a valid JSON object with these exact field names. Do not include any explanatory text.
            
            Example output format:
            {{
              "title": "राजनीति मंथन '25 – An Indian Politics Quiz",
              "date": "2025-04-21",
              "time": "13:30",
              "venue": "Hindu College",
              "registration_link": "https://forms.gle/example"
            }}
            
            If multiple quiz events are found, return an array of objects.
            """
            
            # Prepare the request with slightly higher temperature for more flexibility
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,  # Increased from 0.1 for better date handling
                    "topK": 40,
                    "topP": 0.95,  # Increased for more diversity
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make the API request
            response = requests.post(
                f"{self.url}?key={self.api_key}",
                headers=self.headers,
                json=data
            )
            
            # Debug info
            print(f"Using model: {self.model_name}")
            print(f"API URL: {self.url}")
            
            # Check for errors
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                print(f"Gemini API error: {response.status_code} - {error_msg}")
                print("Available models: gemini-1.5-flash, gemini-1.5-pro, gemini-pro")
                # Try alternative model if first attempt fails
                if self.model_name == "gemini-1.5-flash":
                    print("Attempting with fallback model: gemini-pro")
                    self.model_name = "gemini-pro"
                    self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
                    return self.extract_events(text)
                return []
                
            # Parse the response
            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                print("No valid response from Gemini API")
                return []
                
            # Extract the text content
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            
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
                
                # Normalize and strictly format date/time fields
                normalized_events = []
                current_year = datetime.now().year
                for event in events:
                    normalized_event = {}
                    for key, value in event.items():
                        k = key.lower()
                        if k in ["registration_link", "reg_link", "form_link", "link"]:
                            normalized_event["registration_link"] = value
                        else:
                            normalized_event[k] = value

                    # Strict date normalization
                    date_str = normalized_event.get("date", "")
                    # Try to parse date, add year if missing
                    try:
                        # Acceptable formats: YYYY-MM-DD, DD-MM, DD/MM, etc.
                        if date_str:
                            # If year missing, append current year
                            if len(date_str.split("-")) == 2 or len(date_str.split("/")) == 2:
                                date_str = date_str.replace("/", "-")
                                date_str = f"{current_year}-{date_str.zfill(5)}"
                            # Try parsing
                            dt = datetime.strptime(date_str, "%Y-%m-%d")
                            normalized_event["date"] = dt.strftime("%Y-%m-%d")
                        else:
                            normalized_event["date"] = datetime.now().strftime("%Y-%m-%d")
                    except Exception:
                        normalized_event["date"] = datetime.now().strftime("%Y-%m-%d")

                    # Strict time normalization
                    time_str = normalized_event.get("time", "")
                    try:
                        if time_str:
                            # Try parsing 24-hour or 12-hour with AM/PM
                            try:
                                t = datetime.strptime(time_str.strip(), "%H:%M")
                            except ValueError:
                                t = datetime.strptime(time_str.strip(), "%I:%M %p")
                            normalized_event["time"] = t.strftime("%H:%M")
                        else:
                            normalized_event["time"] = "09:00"
                    except Exception:
                        normalized_event["time"] = "09:00"

                    normalized_events.append(normalized_event)
                    
                return normalized_events
                
            except json.JSONDecodeError:
                print(f"Error parsing Gemini API response as JSON: {content}")
                return []
                
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return []