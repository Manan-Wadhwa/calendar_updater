import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from calendar_utils import load_calendar_service, add_events_to_calendar, save_gemini_output, load_gemini_output
from message_utils import extract_messages
from gemini_utils import GeminiParser
from event_utils import EventExtractor
from typing import List, Dict
import datetime

class QuizExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Event Extractor")
        self.geometry("900x700")
        
        # Initialize extractors
        self.gemini_parser = None
        self.event_extractor = EventExtractor()
        
        # Initialize GUI elements
        self.setup_gui()
        self.events = []

    def setup_gui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # Chat file chooser
        ttk.Label(frm, text="WhatsApp Chat File (.txt):").grid(row=0, column=0, sticky=tk.W)
        self.chat_path = tk.StringVar()
        ttk.Entry(frm, textvariable=self.chat_path, width=50).grid(row=0, column=1, sticky=tk.W)
        ttk.Button(frm, text="Browse...", command=self.browse_chat).grid(row=0, column=2)

        # Gemini key
        ttk.Label(frm, text="Gemini API Key (optional):").grid(row=1, column=0, sticky=tk.W)
        self.gemini_key = tk.StringVar()
        ttk.Entry(frm, textvariable=self.gemini_key, width=50).grid(row=1, column=1, columnspan=2, sticky=tk.W)

        # Selective processing checkbox
        self.selective_processing = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Selective Gemini Processing", variable=self.selective_processing).grid(row=2, column=0, columnspan=3, sticky=tk.W)

        # Calendar creds chooser
        ttk.Label(frm, text="Google Creds JSON:").grid(row=3, column=0, sticky=tk.W)
        self.creds_path = tk.StringVar()
        ttk.Entry(frm, textvariable=self.creds_path, width=50).grid(row=3, column=1, sticky=tk.W)
        ttk.Button(frm, text="Browse...", command=self.browse_creds).grid(row=3, column=2)
        
        # Force-add duplicates checkbox
        self.reset_duplicates = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Force add events (ignore duplicates)", variable=self.reset_duplicates).grid(row=4, column=0, columnspan=3, sticky=tk.W)
        
        # Cutoff Date widget to filter out messages before this date.
        ttk.Label(frm, text="Cutoff Date for Messages:").grid(row=5, column=0, sticky=tk.W)
        # Default to today's date
        self.cutoff_date = tk.StringVar(value=datetime.date.today().isoformat())
        self.date_entry = DateEntry(frm, textvariable=self.cutoff_date, date_pattern='yyyy-mm-dd')
        self.date_entry.grid(row=5, column=1, sticky=tk.W)
        
        # Parse & Add buttons (shifted down by one row)
        ttk.Button(frm, text="Parse Events", command=self.parse_events).grid(row=6, column=1, pady=10)
        ttk.Button(frm, text="Add All to Calendar", command=self.push_to_calendar).grid(row=6, column=2)

        # Progress bar & status label
        self.progress = ttk.Progressbar(frm, length=300, mode='determinate')
        self.progress.grid(row=7, column=0, columnspan=3, pady=10, sticky="ew")
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(frm, textvariable=self.status_var).grid(row=8, column=0, columnspan=3, pady=5)

        # Treeview to display events
        cols = ("Title", "Date", "Time", "Venue", "Link")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120 if c != "Title" else 200)
        self.tree.grid(row=9, column=0, columnspan=3, sticky="nsew")

        # JSON output frames
        json_frame = ttk.Frame(frm)
        json_frame.grid(row=10, column=0, columnspan=3, sticky="nsew", pady=(10,0))
        
        # Local NLP JSON
        ttk.Label(json_frame, text="Local NLP JSON:").grid(row=0, column=0, sticky=tk.W)
        self.local_json = tk.Text(json_frame, height=6, width=80)
        self.local_json.grid(row=1, column=0, sticky="nsew")
        
        # Gemini JSON
        ttk.Label(json_frame, text="Gemini JSON:").grid(row=2, column=0, sticky=tk.W, pady=(10,0))
        self.gemini_json = tk.Text(json_frame, height=6, width=80)
        self.gemini_json.grid(row=3, column=0, sticky="nsew")

        frm.rowconfigure(10, weight=1)
        frm.columnconfigure(1, weight=1)
        json_frame.columnconfigure(0, weight=1)

    def browse_chat(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.chat_path.set(path)

    def browse_creds(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            self.creds_path.set(path)

    def parse_events(self):
        path = self.chat_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid chat .txt file.")
            return

        try:
            self.status_var.set("Reading chat file...")
            self.update_idletasks()
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read chat file: {e}")
            return

        # Use the GUI cutoff date to determine the last update date.
        try:
            cutoff = datetime.datetime.strptime(self.cutoff_date.get(), "%Y-%m-%d").date()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid cutoff date: {e}")
            return

        self.status_var.set("Extracting messages...")
        self.update_idletasks()
        messages = extract_messages(text)    # Expected to return a list of (datetime, message_text)
        if not messages:
            messagebox.showwarning("Warning", 
                "No recent messages found in the chat file.\n\n"
                "Possible reasons:\n"
                "1. The chat file is empty\n"
                "2. The messages are older than 30 days\n"
                "3. The file format doesn't match WhatsApp export\n"
                "4. Incorrect file encoding (should be UTF-8)")
            return
            
        # Filter out messages before the chosen cutoff date.
        filtered_messages = [(dt, msg) for dt, msg in messages if dt.date() >= cutoff]
        self.status_var.set(f"Found {len(filtered_messages)} recent messages on/after {cutoff}")
        self.update_idletasks()
        
        self.progress['value'] = 0
        self.progress['maximum'] = len(filtered_messages)
        self.update_idletasks()

        local_events = []
        gemini_events = []
        
        gemini_key = self.gemini_key.get().strip()
        use_gemini = bool(gemini_key)
        if use_gemini:
            try:
                self.gemini_parser = GeminiParser(gemini_key)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize Gemini: {e}")
                return
        
        for i, (dt, msg) in enumerate(filtered_messages):
            self.status_var.set(f"Processing message {i+1}/{len(filtered_messages)}")
            self.update_idletasks()
            local_quiz_events = self.event_extractor.extract_quiz_info(msg)
            local_events.extend(local_quiz_events)
            if use_gemini and (not self.selective_processing.get() or local_quiz_events):
                try:
                    gemini_quiz_events = self.gemini_parser.extract_events(msg)
                    gemini_events.extend(gemini_quiz_events)
                except Exception as e:
                    print(f"Gemini processing failed for message: {e}")
            self.progress['value'] = i + 1
            self.update_idletasks()

        for row in self.tree.get_children():
            self.tree.delete(row)
        for ev in local_events:
            self.tree.insert("", tk.END, values=(
                ev.get("title", "N/A"), ev.get("date", "N/A"), ev.get("time", "N/A"),
                ev.get("venue", ""), ev.get("form_link", "")
            ))
            
        self.local_json.delete("1.0", tk.END)
        self.local_json.insert(tk.END, json.dumps(local_events, indent=2))
        self.gemini_json.delete("1.0", tk.END)
        self.gemini_json.insert(tk.END, json.dumps(gemini_events, indent=2))
            
        self.status_var.set(f"Found {len(local_events)} local events, {len(gemini_events)} Gemini events")
        if not local_events and not gemini_events:
            messagebox.showinfo("Info", 
                "No quiz events found in the chat.\n\n"
                "Possible reasons:\n"
                "1. No quiz announcements were made in the last 30 days\n"
                "2. The quiz announcements don't match the expected format\n"
                "3. The messages don't contain quiz-related information")

    def push_to_calendar(self):
        gemini_str = self.gemini_json.get("1.0", tk.END).strip()
        if not gemini_str:
            messagebox.showwarning("No events", "Gemini JSON is empty. Please parse events first.")
            return

        try:
            gemini_events = json.loads(gemini_str)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse Gemini JSON: {e}")
            return

        # Save Gemini output to file
        output_filename = "gemini_events.json"
        save_gemini_output(gemini_events, output_filename)
        events = load_gemini_output(output_filename)
        if not events:
            messagebox.showwarning("No events", "No events found in the saved Gemini JSON file.")
            return

        # Validate that each event contains minimal required keys
        valid_events = []
        for ev in events:
            if "title" in ev and "date" in ev and "time" in ev:
                valid_events.append(ev)
            else:
                print(f"Skipping event missing required fields: {ev}")

        if not valid_events:
            messagebox.showwarning("No valid events", "None of the events have the required title, date, and time fields.")
            return

        creds = self.creds_path.get().strip()
        if not creds or not os.path.isfile(creds):
            messagebox.showerror("Error", "Please select your Google service‑account JSON.")
            return

        try:
            self.status_var.set("Connecting to Google Calendar...")
            self.update_idletasks()
            service = load_calendar_service(creds)
            self.status_var.set("Adding events to calendar...")
            self.update_idletasks()
            # Use the calendar ID you provided (update if needed)
            calendar_id = "9b7516b49f5e5ea66d05295f2830fa04ed95cb124d03f554beddaa3950e8f045@group.calendar.google.com"
            created = add_events_to_calendar(
                valid_events,
                service,
                calendar_id=calendar_id,
                ignore_duplicates=self.reset_duplicates.get()
            )
            messagebox.showinfo("Success", f"Added {len(created)} event(s) to Calendar.")
            self.status_var.set(f"Added {len(created)} events to calendar")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error adding events to calendar")

if __name__ == "__main__":
    app = QuizExtractorApp()
    app.mainloop()
