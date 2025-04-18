import spacy
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import sys

def load_spacy_model() -> Optional[spacy.Language]:
    """Load spaCy model with proper error handling."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        try:
            print("Downloading spaCy model...")
            spacy.cli.download("en_core_web_sm")
            return spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"Error loading spaCy model: {e}")
            return None

def is_quiz_announcement(doc: spacy.tokens.Doc) -> bool:
    """
    Determine if a message is a quiz announcement using NLP.
    Returns True if the message is likely a quiz announcement.
    """
    # Check for essential entities
    has_date = any(ent.label_ == "DATE" for ent in doc.ents)
    has_location = any(ent.label_ == "GPE" or ent.label_ == "FAC" for ent in doc.ents)
    has_money = any(ent.label_ == "MONEY" for ent in doc.ents)
    
    # Check for quiz-related keywords using lemmatization
    quiz_keywords = {
        'quiz', 'register', 'participate', 'event', 'announce',
        'competition', 'contest', 'team', 'participant', 'venue',
        'prize', 'winner', 'certificate', 'guideline', 'rule',
        'society', 'fest', 'festival', 'competition', 'championship'
    }
    
    # Count quiz-related keywords
    keyword_count = sum(
        1 for token in doc
        if not token.is_stop and not token.is_punct
        and token.lemma_.lower() in quiz_keywords
    )
    
    # Check for registration-related patterns
    has_registration = any(
        token.text.lower() in {'registration', 'register', 'signup', 'sign up', 'reg', 'reg.'}
        for token in doc
    )
    
    # Check for date/time patterns
    has_time = any(
        token.text.lower() in {'am', 'pm', 'morning', 'afternoon', 'evening', 'night'}
        for token in doc
    )
    
    # Consider it a quiz announcement if it has multiple strong indicators
    return (
        (has_date and has_location) or  # Date + venue
        (has_date and has_money) or     # Date + prizes
        (has_date and has_registration) or  # Date + registration
        (keyword_count >= 2 and has_date) or  # Multiple quiz keywords + date
        (has_date and has_time and keyword_count >= 1)  # Date + time + at least one quiz keyword
    )

def parse_timestamp(line: str) -> Optional[datetime]:
    """Parse timestamp from WhatsApp message line."""
    try:
        # Handle WhatsApp export format: DD/MM/YYYY, HH:MM - Name: Message
        parts = line.split(' - ', 1)
        if len(parts) >= 1:
            dt_str = parts[0]
            if len(dt_str) >= 16 and dt_str[2] == '/' and dt_str[5] == '/':
                return datetime.strptime(dt_str, '%d/%m/%Y, %H:%M')
    except (ValueError, IndexError):
        pass
    return None

def extract_messages(text: str) -> List[Tuple[datetime, str]]:
    """
    Extract messages from WhatsApp chat text using NLP.
    Returns list of (datetime, message) tuples.
    """
    if not text.strip():
        return []

    # Load spaCy model
    nlp = load_spacy_model()
    if nlp is None:
        print("Error: Could not load spaCy model. Please check your installation.")
        return []

    # Get current date and 30 days ago
    now = datetime.now()
    month_ago = now - timedelta(days=30)
    
    messages = []
    current_msg = []
    current_dt = None
    
    # Process text line by line
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with a date
        dt = parse_timestamp(line)
        if dt is not None:
            # Process previous message if exists
            if current_msg and current_dt:
                msg_text = '\n'.join(current_msg)
                # Skip system messages and media
                if not any(x in msg_text.lower() for x in ['<media omitted>', 'this message was deleted']):
                    doc = nlp(msg_text)
                    if is_quiz_announcement(doc):
                        messages.append((current_dt, msg_text))
            
            # Start new message
            current_msg = []
            current_dt = dt
            
            # Skip if message is too old
            if current_dt < month_ago:
                current_dt = None
                continue
                
            # Add the message content (skip the timestamp and sender name)
            parts = line.split(' - ', 2)
            if len(parts) >= 3:
                msg_content = parts[2].strip()
                if msg_content:
                    current_msg.append(msg_content)
                
        elif current_dt and line:
            # Continue current message
            current_msg.append(line)
    
    # Process last message
    if current_msg and current_dt:
        msg_text = '\n'.join(current_msg)
        # Skip system messages and media
        if not any(x in msg_text.lower() for x in ['<media omitted>', 'this message was deleted']):
            doc = nlp(msg_text)
            if is_quiz_announcement(doc):
                messages.append((current_dt, msg_text))
    
    print(f"Found {len(messages)} quiz announcements in the last 30 days")
    return messages 