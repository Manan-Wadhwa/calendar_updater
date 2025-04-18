

# Quiz Event Extractor (Tkinter)

**Quiz Event Extractor** is a local Python application that allows you to extract quiz event details from exported WhatsApp chat files, parse them, and add them to your Google Calendar. The app supports both a local fallback parser using regular expressions and an optional Gemini-powered parser.

---

## Features

- **WhatsApp Chat Parsing**: Extract event details from exported WhatsApp chat files (.txt).
- **Gemini API Integration** (optional): Use the Gemini API for more accurate event extraction.
- **Google Calendar Integration**: Automatically add events to Google Calendar using the Google Calendar API.
- **Simple GUI**: User-friendly interface built with `tkinter`.

---

## Setup Instructions

### 1. Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/yourusername/quiz-event-extractor.git
cd quiz-event-extractor
```

### 2. Install Dependencies

Install all required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

This will install:
- `requests` (for making API requests)
- `dateparser` (for parsing dates from text)
- `google-api-python-client` and `google-auth` (for interacting with Google Calendar API)

### 3. Google Calendar Setup

To use Google Calendar integration, you'll need to set up a **Google Service Account** and obtain the credentials JSON file.

- Go to the [Google Developer Console](https://console.developers.google.com/).
- Create a new project.
- Enable the **Google Calendar API** for your project.
- Create a **Service Account** and download the **credentials JSON file**.
- Share your calendar with the service account email (found in the credentials file).

### 4. Optional: Gemini API Key

If you want to use the Gemini-powered event extraction, you'll need to provide your **Gemini API Key**:

- Replace the `GEMINI_URL` placeholder in `parser_gemini.py` with the actual Gemini API endpoint URL.
- Obtain an API key from Gemini (or whichever service you're using).

### 5. Running the Application

Once everything is set up, you can run the app by executing:

```bash
python main.py
```

This will open a graphical interface where you can:

- Select your **WhatsApp exported chat file** (a `.txt` file).
- Provide your **Gemini API key** (optional).
- Provide the **Google Calendar credentials JSON file**.
- Parse events from the chat.
- Add the parsed events to your Google Calendar.

---

## Usage Guide

### 1. Export WhatsApp Chat

To export your WhatsApp chat:

- Open your WhatsApp group chat.
- Tap on the group name, scroll down, and choose **Export Chat**.
- Select **Without Media** to save the text-only version of the chat.
- Save the `.txt` file on your machine.

### 2. Provide API Keys and Files

- **Gemini API Key (optional)**: Paste the API key in the Gemini key input field in the app. If you don’t have the key, the local parser will be used instead.
- **Google Calendar Credentials**: Select the `credentials.json` file you downloaded earlier from the Google Developer Console.

### 3. Parse the Events

Once you’ve provided the necessary files:

1. **Click "Parse Events"**: The app will analyze the chat file and extract any quiz-related events.
2. If the app finds quiz events, it will display them in the table below.

### 4. Add Events to Google Calendar

- **Click "Add All to Calendar"**: This will add all extracted events to your Google Calendar.
- Events will be created with the following details:
  - **Title**: Automatically extracted from the message (e.g., "Quiz Event").
  - **Date and Time**: Parsed from the message's date and time.
  - **Venue**: If a venue is mentioned, it will be included.
  - **Form Link**: If a form link is found, it will be included in the event description.

### 5. Calendar Sync

- The events will be added to your **primary Google Calendar** in the **Asia/Kolkata** time zone (you can modify this in the code if needed).

---

## Example Workflow

1. **WhatsApp Chat**: You have a WhatsApp chat that contains quiz event information like:

```
19/04/2025, 9:00 AM - Quiz Event on AI
Venue: Online
Link: https://forms.gle/quiz-form-link
```

2. **Export the Chat**: Export the chat as a `.txt` file.

3. **Parse the Events**: Open the app, browse and select the chat file, then click "Parse Events".

4. **Add to Google Calendar**: Once the events are parsed, click "Add All to Calendar" to sync them to your Google Calendar.

---

## File Structure

```
quiz_event_extractor/
├── parser_local.py             # Local fallback event parsing (regex and dateparser)
├── parser_gemini.py            # Gemini API event extraction
├── calendar_utils.py           # Google Calendar API functions
├── main.py                     # The main Tkinter GUI application
├── requirements.txt            # List of Python dependencies
├── README.md                   # This documentation
├── .gitignore                  # Files/folders to ignore in Git
```

---

## Notes

- **Time Zone**: The application assumes the events are in the **Asia/Kolkata** time zone. Modify the `calendar_utils.py` if needed.
- **Date Parsing**: The `dateparser` library is used to handle date parsing, but it may not be 100% accurate. The Gemini API may provide better accuracy.
- **API Integration**: If you don't have a Gemini API key, the local parser will be used instead. You can always update the app to include other parsing logic or APIs.

---

## Troubleshooting

- **Invalid API Key**: If the Gemini API key is invalid or not working, the app will fall back to the local parser.
- **Google Calendar**: Ensure your service account has the correct permissions and that you've shared the calendar with the service account email.
- **File Parsing**: If the WhatsApp chat file doesn’t contain recognizable event details, the parser might not find any events.

---

## Contributing

Feel free to open issues or pull requests if you encounter bugs or have suggestions for improvements!

---

## License

This project is open-source and released under the MIT License.