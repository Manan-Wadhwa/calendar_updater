import spacy
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dateutil import parser

class EventExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

    def extract_date_time(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract date and time from text using NLP and pattern matching"""
        doc = self.nlp(text)
        
        # Find date entities
        dates = []
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                try:
                    parsed = parser.parse(ent.text, fuzzy=True)
                    if parsed > datetime.now():
                        dates.append(parsed)
                except:
                    continue
        
        # Sort dates chronologically
        dates.sort()
        
        if dates:
            date = dates[0].strftime("%Y-%m-%d")
            time = dates[0].strftime("%I:%M %p")
            return date, time
            
        # Fallback to regex patterns
        date_patterns = [
            r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",  # DD-MM-YYYY or DD/MM/YYYY
            r"\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}",  # 1st Jan 2024
        ]
        
        time_patterns = [
            r"\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?",  # 9:00 AM
            r"\d{1,2}\s*(?:AM|PM|am|pm)",  # 9 AM
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    parsed = parser.parse(match.group(), fuzzy=True)
                    if parsed > datetime.now():
                        date = parsed.strftime("%Y-%m-%d")
                        break
                except:
                    continue
        else:
            date = None
            
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    parsed = parser.parse(match.group(), fuzzy=True)
                    time = parsed.strftime("%I:%M %p")
                    break
                except:
                    continue
        else:
            time = None
            
        return date, time

    def extract_venue(self, text: str) -> Optional[str]:
        """Extract venue from text using NLP and pattern matching"""
        doc = self.nlp(text)
        
        # Common college-related keywords
        college_keywords = [
            "college", "university", "institute", "school", "academy",
            "campus", "department", "faculty", "hall", "building",
            "block", "room", "lab", "laboratory", "center", "centre"
        ]
        
        # Look for proper nouns and organizations that might be college names
        potential_venues = []
        current_venue = []
        
        for token in doc:
            # Check for proper nouns and organizations
            if token.pos_ in ["PROPN", "NOUN"] or token.ent_type_ in ["ORG", "GPE"]:
                current_venue.append(token.text)
            elif current_venue:
                # If we have a current venue and hit a non-venue word, save it
                potential_venues.append(" ".join(current_venue))
                current_venue = []
        
        # Add any remaining venue
        if current_venue:
            potential_venues.append(" ".join(current_venue))
        
        # Look for venue indicators and their context
        for token in doc:
            if token.text.lower() in college_keywords:
                # Get surrounding context
                venue_parts = []
                
                # Look back up to 3 tokens
                for i in range(1, 4):
                    if token.i - i >= 0:
                        prev_token = doc[token.i - i]
                        if prev_token.pos_ in ["PROPN", "NOUN"] or prev_token.ent_type_ in ["ORG", "GPE"]:
                            venue_parts.insert(0, prev_token.text)
                
                # Add the keyword
                venue_parts.append(token.text)
                
                # Look ahead up to 3 tokens
                for i in range(1, 4):
                    if token.i + i < len(doc):
                        next_token = doc[token.i + i]
                        if next_token.pos_ in ["PROPN", "NOUN"] or next_token.ent_type_ in ["ORG", "GPE"]:
                            venue_parts.append(next_token.text)
                
                if venue_parts:
                    potential_venues.append(" ".join(venue_parts))
        
        # Clean and prioritize venues
        cleaned_venues = []
        for venue in potential_venues:
            # Remove common stop words and clean up
            venue = re.sub(r'\b(the|a|an|at|in|on|of|for|and|or)\b', '', venue, flags=re.IGNORECASE)
            venue = re.sub(r'\s+', ' ', venue).strip()
            if venue and len(venue) > 3:  # Filter out very short strings
                cleaned_venues.append(venue)
        
        # Return the longest venue found (usually the most complete)
        if cleaned_venues:
            return max(cleaned_venues, key=len)
            
        return None

    def extract_registration_link(self, text: str) -> Optional[str]:
        """Extract registration link from text"""
        # Prioritize Google Forms links
        forms_pattern = r"https://forms\.gle/[A-Za-z0-9_-]+"
        match = re.search(forms_pattern, text)
        if match:
            return match.group()
            
        # Look for other URLs
        url_pattern = r"https?://(?:www\.)?[A-Za-z0-9-]+(?:\.[A-Za-z]{2,})+(?:/[^\s]*)?"
        match = re.search(url_pattern, text)
        if match:
            return match.group()
            
        return None

    def extract_quiz_title(self, text: str) -> Optional[str]:
        """Extract quiz title from text using NLP and pattern matching"""
        doc = self.nlp(text)
        
        # Look for quiz-related keywords
        quiz_keywords = ["quiz", "test", "exam", "competition", "event"]
        for token in doc:
            if token.text.lower() in quiz_keywords:
                # Get surrounding context for title
                title = []
                # Look back up to 3 tokens
                for i in range(1, 4):
                    if token.i - i >= 0:
                        prev_token = doc[token.i - i]
                        if prev_token.pos_ in ["NOUN", "PROPN", "ADJ"]:
                            title.insert(0, prev_token.text)
                # Add the keyword
                title.append(token.text)
                # Look ahead up to 3 tokens
                for i in range(1, 4):
                    if token.i + i < len(doc):
                        next_token = doc[token.i + i]
                        if next_token.pos_ in ["NOUN", "PROPN", "ADJ"]:
                            title.append(next_token.text)
                if title:
                    return " ".join(title)
                    
        # Fallback to regex pattern
        title_pattern = r"(?:quiz|test|exam|competition|event)\s+[A-Za-z0-9\s]+"
        match = re.search(title_pattern, text, re.IGNORECASE)
        if match:
            return match.group().strip()
            
        return None

    def extract_quiz_info(self, text: str) -> List[Dict]:
        """Extract quiz information from text"""
        events = []
        
        # Extract date and time
        date, time = self.extract_date_time(text)
        if not date or not time:
            return events
            
        # Extract title
        title = self.extract_quiz_title(text)
        if not title:
            return events
            
        # Extract venue
        venue = self.extract_venue(text)
        
        # Extract registration link
        form_link = self.extract_registration_link(text)
        
        # Create event dictionary
        event = {
            "title": title,
            "date": date,
            "time": time,
            "venue": venue,
            "form_link": form_link
        }
        
        events.append(event)
        return events 