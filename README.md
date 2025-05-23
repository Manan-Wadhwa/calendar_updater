# Quiz Event Extractor (Tkinter)

**Quiz Event Extractor** is a local Python application that extracts quiz event details from exported WhatsApp chat files, parses them using local regex/NLP and an optional Gemini-powered parser, and adds them to your Google Calendar. The app features a simple Tkinter GUI, secure configuration via environment variables, and built-in file filters using a .gitignore.

---

## Features

- **WhatsApp Chat Parsing**: Extract quiz event details from exported WhatsApp chat files (.txt).
- **Gemini API Integration (Optional)**: Use the Gemini API for enhanced event extraction.
- **Google Calendar Integration**: Automatically add events to your Google Calendar using the Google Calendar API.
- **Secure Configuration**: Sensitive credentials (e.g. Calendar ID, API keys) are loaded via environment variables.
- **Graphical Interface**: User-friendly GUI built with `tkinter` and `tkcalendar` for selecting cutoff dates and files.
- **File Ignorance**: Chat files and example message files are ignored in version control via .gitignore.

---

## Setup Instructions

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/quiz-event-extractor.git
cd quiz-event-extractor
```

### 2. Create a Virtual Environment (Recommended)

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

Install the required dependencies with:

```bash
pip install -r requirements.txt
```

This installs:
- Google API libraries (`google-auth`, `google-api-python-client`, etc.)
- NLP packages (`spacy`, `dateparser`, `python-dateutil`)
- HTTP & GUI libraries (`requests`, `tkcalendar`)
- Development tools (`python-dotenv`)

### 4. Configure Environment Variables

Create a `.env` file in the project root (this file is in .gitignore) and add your sensitive credentials. For example:

```properties
# .env file
CALENDAR_ID=YOUR_CALENDAR_ID_HERE
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
```

Your application will load these values at runtime using `python-dotenv`.

### 5. Google Calendar Setup

To enable calendar integration:
- Create a **Google Service Account** and download the credentials JSON file.
- Enable the **Google Calendar API** in your project.
- Share your target Google Calendar with the service account email.
- Use the file browser in the app to load the service account credentials.

### 6. Git Ignore Sensitive Files

Ensure that your `.gitignore` file includes sensitive and non-essential files (such as chat text files and example messages). For example, your .gitignore should list:

```ignore
__pycache__/
*.py[cod]
*.env
whatsapp_chat.txt
gemini_events.json
example_message.txt
```

---

## Usage

1. **Run the Application**:

   ```bash
   python main.py
   ```

2. **Using the GUI**:
   - **Select Chat File**: Choose your exported WhatsApp chat file (a `.txt` file).  
   - **Enter Gemini API Key**: Optionally provide your Gemini API key (if you want to enable Gemini-based parsing).
   - **Select Google Creds JSON**: Browse and select your service account JSON file.
   - **Force Add Events**: Check this option to ignore duplicate checks.
   - **Select Cutoff Date**: Use the DateEntry widget to set a cutoff date; messages before that date are filtered out.
   - **Parse Events**: Click the “Parse Events” button to extract quiz events from your chat file.
   - **Add to Calendar**: Click “Add All to Calendar” to upload the events to your Google Calendar.

---

## Example Workflow

1. **Export WhatsApp Chat**: Export the chat (without media) from your WhatsApp group.
2. **Open the App**: Run `python main.py` to load the GUI.
3. **Load Files & API Keys**: Provide your chat file, service account credentials, and (if available) the Gemini API key.
4. **Set Cutoff Date**: Choose the last update date using the calendar widget so that older messages are ignored.
5. **Parse and Add**: Parse the events and add them to your Google Calendar.

---

## Troubleshooting

- **Environment Variables**: Ensure your `.env` file is present and correctly formatted.
- **Google Access**: Confirm your service account has proper access to your Google Calendar.
- **Parsing Issues**: Check that your chat file follows the correct export format and that the messages contain quiz-related information.
- **Dependencies**: If any dependency issues arise, reinstall using `pip install -r requirements.txt`.

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open issues or submit pull requests.

---

## License

This project is open-source and released under the MIT License.

---

## Acknowledgements

- Python and Tkinter for the GUI.
- spaCy for NLP.
- Google API Client Libraries for calendar integration.
- tkcalendar for a user-friendly date picker.
- python-dotenv for environment variable management.