## gui.py
import os
import re
import sys
import threading
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox, ttk
import webbrowser
import openai
from job_application_generator import generate_job_application
from utils import extract_job_ad_from_url, load_settings, save_settings
from webpage_saver import save_webpage
from datetime import datetime
import win32com.client as win32  # Für die Interaktion mit Word
from text_redirector import TextRedirector
import pythoncom
import win32com.client as win32

class JobAppGeneratorApp:
    HELP_URL = "https://github.com/schbrongx"  # Set the default help URL

    def __init__(self, root):
        print("gui.__init__: Initializing")
        self.root = root
        self.root.title("Bewerbungsgenerator mit ChatGPT")

        # Load settings from settings.json
        self.settings = load_settings()

        # Create the menu bar
        self.create_menu_bar()

        # Define the GUI elements (buttons, labels, text fields)
        self.working_folder_frame = tk.Frame(self.root)
        self.working_folder_frame.pack(anchor="w", pady=5)

        current_folder = self.settings.get("working_folder", None)
        self.working_folder_label = tk.Label(self.working_folder_frame, text=f"Working folder: {self._get_short_path(current_folder)}")
        self.working_folder_label.pack(side=tk.LEFT, padx=5)

        self.template_frame = tk.Frame(self.root)
        self.template_frame.pack(anchor="w", pady=5)

        current_template = self.settings.get("word_template", None)
        self.template_label = tk.Label(self.template_frame, text=f"Word-Vorlage: {self._get_short_path(current_template)}")
        self.template_label.pack(side=tk.LEFT, padx=5)


        self.job_ad_frame = tk.Frame(self.root)
        self.job_ad_frame.pack(anchor="w", pady=5)

        self.job_ad_label = tk.Label(self.job_ad_frame, text="Job Ad URL:")
        self.job_ad_label.pack(side=tk.LEFT, padx=5)

        self.job_ad_var = tk.StringVar()
        self.job_ad_entry = ttk.Combobox(self.job_ad_frame, textvariable=self.job_ad_var, width=50)
        self.job_ad_entry['values'] = self.settings.get("last_urls", [])
        self.job_ad_entry.pack(side=tk.LEFT, padx=5)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(anchor="w", pady=10)

        self.preview_button = tk.Button(self.button_frame, text="Preview Query", command=self.preview_query)
        self.preview_button.pack(side=tk.LEFT, padx=10)

        self.execute_button = tk.Button(self.button_frame, text="Generate", command=self.run_generate_thread)
        self.execute_button.pack(side=tk.LEFT, padx=10)

        # Checkbox: Open Word document after generating
        self.open_after_var = tk.BooleanVar()
        self.open_after_var.set(self.settings.get("open_word_after_generating", False))  # Load from settings
        self.open_after_checkbox = tk.Checkbutton(self.button_frame, text="Open Word document after generating",
                                                  variable=self.open_after_var, onvalue=True, offvalue=False,
                                                  command=self.save_checkbox_state)
        self.open_after_checkbox.pack(side=tk.LEFT, padx=10)

        self.output_text = tk.Text(self.root)
        self.output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Textausgabefeld für das Logging mit Scrollbar
        self.log_frame = tk.Frame(self.root)
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        self.scrollbar = tk.Scrollbar(self.log_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text = tk.Text(self.log_frame, height=10, font=tkFont.Font(family="Courier", size=10), wrap=tk.NONE, fg="white", bg="black", yscrollcommand=self.scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.log_text.yview)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # sys.stdout umleiten, um alle print-Ausgaben in das log_text-Feld zu schreiben
        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)


    def _get_short_path(self, path, max_length=30):
        """Shorten the path, showing the first 10 characters and also the parent folder."""
        if path and len(path) > max_length:
            parent_folder = os.path.basename(os.path.dirname(path))
            folder_name = os.path.basename(path)
            shortened_path = f"{path[:10]}...{parent_folder}{os.path.sep}{folder_name}"
            return shortened_path
        return path or "None"

    def open_help(self):
        """Open the Help URL in the default web browser."""
        webbrowser.open(self.HELP_URL)

    def create_menu_bar(self):
        """Create the menu bar with Settings and Help menus."""
        menu_bar = tk.Menu(self.root)

        # Settings Menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Modify GPT Query", command=self.modify_query_window)
        settings_menu.add_command(label="Working Folder", command=self.select_working_folder)
        settings_menu.add_command(label="Clear Working Folder", command=self.clear_working_folder)
        settings_menu.add_command(label="Select Word Template", command=self.select_word_template)
        settings_menu.add_command(label="Clear Word Template", command=self.clear_word_template)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        # Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.open_help)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def log_message(self, message):
        """Fügt eine Nachricht im Log-Ausgabefeld hinzu."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # Scrollt automatisch nach unten, wenn neue Nachrichten hinzugefügt werden

    def save_checkbox_state(self):
        """Save the state of the 'Open Word document after generating' checkbox to the settings."""
        self.settings["open_word_after_generating"] = self.open_after_var.get()  # Get the current state of the checkbox
        save_settings(self.settings)  # Save settings to settings.json
        print(f"Checkbox state saved: {self.settings['open_word_after_generating']}")

    def modify_query_window(self):
        """Open a new window to modify the job query."""
        print(f"gui.modify_query_window: Opening window for query modification.")
        self.query_window = tk.Toplevel(self.root)
        self.query_window.title("Modify Query")

        # Allow the window to be resizable
        self.query_window.geometry("600x400")
        self.query_window.rowconfigure(0, weight=1)
        self.query_window.columnconfigure(0, weight=1)

        # Bind the Escape key to close the window
        self.query_window.bind("<Escape>", lambda event: self.query_window.destroy())

        # Set focus on the window
        self.query_window.focus_set()

        # Create a Text widget where the user can modify the job query
        self.query_textbox = tk.Text(self.query_window)
        self.query_textbox.insert(tk.END, self.settings.get("job_query", ""))
        self.query_textbox.grid(row=0, column=0, sticky="nsew")

        # Add a scrollbar for the text box
        scrollbar = tk.Scrollbar(self.query_window, command=self.query_textbox.yview)
        self.query_textbox.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Button to save the modified query
        tk.Button(self.query_window, text="Save Query", command=self.save_query).grid(row=1, column=0, pady=5)

    def save_query(self):
        """Save the modified query to the settings file and close the window."""
        self.settings["job_query"] = self.query_textbox.get("1.0", tk.END).strip() 
        save_settings(self.settings)
        print(f"gui.save_query: Query saved.")
        self.query_window.destroy()

    def select_working_folder(self):
        """Allow the user to select a working folder and save it in the settings."""
        folder = filedialog.askdirectory(title="Select Working Folder")
        if folder:
            self.settings["working_folder"] = folder
            save_settings(self.settings)
            # Update the label with the short version of the path
            self.working_folder_label.config(text=f"Working folder: {self._get_short_path(folder)}")

    def clear_working_folder(self):
        """Clears the working folder setting."""
        self.settings["working_folder"] = None
        save_settings(self.settings)
        self.working_folder_label.config(text="Working folder: None")

    def select_word_template(self):
        """Allow the user to select a Word template and save it in the settings."""
        template_path = filedialog.askopenfilename(
            title="Select Word Template",
            filetypes=[("Word Templates", "*.dotx"), ("All Files", "*.*")]
        )
        if template_path:
            self.settings["word_template"] = template_path
            save_settings(self.settings)
            # Update the label with the short version of the template path
            self.template_label.config(text=f"Word-Vorlage: {self._get_short_path(template_path)}")

    def clear_word_template(self):
        """Clears the word template setting."""
        self.settings["word_template"] = None
        save_settings(self.settings)
        self.template_label.config(text="Word-Vorlage: None")

    def _generate_prompt(self, job_query, job_ad_content, job_ad_url):
        """Generate a structured prompt for ChatGPT to generate a job application in Swiss German spelling."""
        print("gui._generate_prompt: Setting prompt-variable")
        prompt = (
            f"Du bist ein hilfreicher Assistent, der eine Bewerbung verfassen soll.\n"
            f"Die erste Zeile deiner Antwort muss zwingend folgende Felder im TSV format (tab seperated values) enhalten:\n"
            f"- Heutiges Datum im Format dd.mm.yyyy\n"
            f"- Firmenname\n"
            f"- URL der ausgeschriebenen Stelle (Job Ad URL)\n"
            f"- Stellentitel/Job Titel\n"
            f"- Vorname, Nachname und Email der Kontaktperson bei der Firma\n\n"
            f"Bitte schreibe eine professionelle und überzeugende Bewerbung, die auf diese Stelle zugeschnitten ist."
            f"\n\nBefolge ausserdem unbedingt die folgenden zusätzlichen Anweisungen:\n"
            f"\n\n*** Zusätzliche Anweisungen***\n{job_query}"
            f"\n\n*** Hier ist die ursprüngliche URL der Stellenauschhreibung (Job Ad UR)L**\n{job_ad_url}"
            f"\n\n ** Hier ist der Inhalt des Inserates: (Job Ad Inhalt) **\n{job_ad_content}"
        )
        return re.sub(r'\n\s*\n+', '\n\n', prompt)

    def preview_query(self):
        """Preview the query that will be sent to ChatGPT."""
        print(f"gui.preview_query: Opening preview query window.")
        if not self.job_ad_var.get():
            messagebox.showerror("Error", "Please provide the job ad URL.")
            return

        job_ad_url = self.job_ad_var.get()
        job_ad_content, _ = extract_job_ad_from_url(job_ad_url)

        job_query = self.settings.get("job_query", "")
        prompt = self._generate_prompt(job_query, job_ad_content, job_ad_url)

        # Display the preview in a resizable window
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Query Preview")
        self.preview_window.geometry("600x400")
        self.preview_window.rowconfigure(0, weight=1)
        self.preview_window.columnconfigure(0, weight=1)

        # Bind the Escape key to close the window
        self.preview_window.bind("<Escape>", lambda event: self.preview_window.destroy())

        self.preview_window.focus_set()

        preview_textbox = tk.Text(self.preview_window)
        preview_textbox.insert(tk.END, prompt)
        preview_textbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(self.preview_window, command=preview_textbox.yview)
        preview_textbox.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")


    def run_generate_thread(self):
        """Run the generate_application in a separate thread to avoid blocking Tkinter main loop."""
        print("gui.run_generate_thread: Disabling buttons, starting thread")
        self.disable_buttons()
        self.clear_output_text("Generating... Please wait...")
        # Start the background task
        thread = threading.Thread(target=self.generate_application)
        thread.start()


    def generate_application(self):
        """Generate the job application asynchronously and save job ad content as a file."""
        print("gui.generate_application: Starting application generation...")

        job_ad_url = self.job_ad_var.get()
        if not job_ad_url:
            self.display_error("Please provide the job ad URL.")
            self.enable_buttons()
            print("gui.generate_application: Error: No job ad URL provided.")
            return

        print(f"Job Ad URL: {job_ad_url}")
        job_ad_content = self.fetch_job_ad_content(job_ad_url)
        if not job_ad_content:
            self.enable_buttons()
            print("gui.generate_application: Error: Failed to fetch job ad content.")
            return

        job_query = self.settings.get("job_query", "")
        print(f"gui.generate_application: Job Query: {job_query}")
        prompt = self._generate_prompt(job_query, job_ad_content, job_ad_url)
        print(f"gui.generate_application: Prompt generated: {prompt}")

        # Generate the job application with ChatGPT
        try:
            print("gui.generate_application: Sending request to ChatGPT API...")
            job_application = generate_job_application(prompt)
            print("gui.generate_application: Response from ChatGPT received.")
            # Update the UI with job application on the main thread
            self.clear_output_text(job_application)

        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        finally:
            self.enable_buttons()

        # Extract company_name and job_title from ChatGPT response
        company_name, job_title = self.extract_meta_information(job_application)
        print(f"gui.generate_application: Extracted company name: {company_name}, job title: {job_title}")

        # Construct filename: {company_name}_{job_title}.mhtml
        if company_name and job_title:
            filename = f"{company_name}_{job_title}.html".replace(' ', '_')
            filename = re.sub(r'[<>:"/\\|?*%#@!&$^]', '', filename)
            filepath = os.path.join(self.settings.get("working_folder", ""), filename)

        success, error = save_webpage(job_ad_url, filepath)
        if success:
            print(f"gui.save_webpage_in_main_thread: Webpage saved successfully as {filepath}.")
            self.create_word_document_from_template(filepath, job_application)
        else:
            print(f"gui.save_webpage_in_main_thread: Failed to save webpage: {error}")


    def create_word_document_from_template(self, html_filepath, generated_text):
        """Create a Word document from the template and replace placeholder text with generated content."""
        print(f"gui.create_word_document_from_template: Create word document in working path folder and insert GTP reply.")
 
        pythoncom.CoInitialize()

        working_folder = self.settings.get("working_folder")
        word_template = self.settings.get("word_template")
    
        if not working_folder or not word_template:
            print(f"\ngui.create_word_document_from_template: Error: No working folder or word template specified.\n")
            return
        
        if not os.path.exists(working_folder):
            print(f"\ngui.create_word_document_from_template: Error: Working folder does not exist.\n")
            return
    
        if not os.path.exists(word_template):
            print(f"\ngui.create_word_document_from_template: Error: Word template does not exist.\n")
            return
    
        html_filename = os.path.basename(html_filepath).replace('.html', '')
        word_docx_path = os.path.join(working_folder, f"{html_filename}.docx")
    
        if os.path.exists(word_docx_path):
            overwrite = messagebox.askyesno(
                "Datei existiert bereits",
                f"Die Datei {html_filename}.docx existiert bereits. Möchten Sie sie überschreiben?"
            )
            if not overwrite:
                print(f"gui.create_word_document_from_template: Skipped creating Word document: {word_docx_path}")
                return

        try:
            print("gui.create_word_document_from_template: Trying to generate word document.")
            word_app = win32.Dispatch("Word.Application")
            word_app.Visible = False  # Word im Hintergrund starten
    
            doc = word_app.Documents.Add(word_template)
    
            print("gui.create_word_document_from_template: Trying to Replace placeholder text in word document with ChatGPT's text.")
            self.replace_placeholder_in_word(doc, "[BEWERBUNGSTEXT]", generated_text)

            doc.SaveAs(word_docx_path)
            doc.Close()
    
            print(f"gui.create_word_document_from_template: Word document created: {word_docx_path}")

            if self.open_after_var.get():
                print(f"Opening Word document: {word_docx_path}")
                os.startfile(word_docx_path)  # This will open the Word document
    
        except Exception as e:
            print(f"gui.create_word_document_from_template: Error creating Word document: {str(e)}")
        finally:
            word_app.Quit()
            pythoncom.CoUninitialize()


    def replace_placeholder_in_word(self, doc, placeholder, replacement_text):
        """Replaces the placeholder text in a Word document with the given replacement text."""
        # Suche im gesamten Dokument nach dem Platzhalter
        find = doc.Content.Find
        find.Text = placeholder
    
        # Entferne den Platzhalter [BEWERBUNGSTEXT], wenn er gefunden wurde
        find.Execute(Replace=0)  # wdReplaceNone = 0    

        # Füge den generierten Text an der Position des Platzhalters ein
        if find.Found:
            range_obj = find.Parent
            # Lösche den Platzhalter
            range_obj.Text = ""
            # Füge den generierten Text in Abschnitten ein, um Längenbeschränkungen zu vermeiden
            for paragraph in replacement_text.split("\n"):
                range_obj.InsertAfter(paragraph + "\n")
        else:
            self.output_text.insert(tk.END, f"\nPlaceholder '{placeholder}' not found.\n")
   

    def run_generate_thread(self):
        """Run the generate_application in a separate thread."""
        print("gui.run_generate_thread: Disabling buttons, starting thread")

        job_ad_url = self.job_ad_var.get()
        
        # Add URL to the history if not already present
        if job_ad_url not in self.settings["last_urls"]:
            self.settings["last_urls"].append(job_ad_url)
            save_settings(self.settings)
        
        self.disable_buttons()
        self.clear_output_text("Generating... Please wait...")
        
        # Start the async application generation in a new thread using asyncio.run
        thread = threading.Thread(target=self.generate_application)
        thread.start()
    

    def extract_meta_information(self, job_application):
        """Extracts company_name and job_title from ChatGPT's job application response."""
        print(f"gui.extract_meta_information: Extracting TSV values from GPT response.")
        try:
            # Look for the TSV output
            tsv_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)', job_application)
            if tsv_match:
                # Extract the company name and job title from the matched TSV line
                company_name = tsv_match.group(2).strip()
                job_title = tsv_match.group(4).strip()
                return company_name, job_title
            else:
                # Return None if not found
                return None, None
        except Exception as e:
            print(f"gui.exract_meta_information: Failed to extract metadata: {str(e)}")
            return None, None


    def fetch_job_ad_content(self, job_ad_url):
        """Fetch and return job ad content."""
        try:
            job_ad_content, _ = extract_job_ad_from_url(job_ad_url)
            return job_ad_content
        except Exception as e:
            print(f"Failed to fetch job ad content: {str(e)}")
            return None


    def generate_application_and_display(self, prompt):
        """Generate and display the job application."""
        try:
            job_application = generate_job_application(prompt)
            self.clear_output_text(job_application)
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        finally:
            self.enable_buttons()


    def disable_buttons(self):
        """Disable buttons to prevent multiple clicks."""
        self.execute_button.config(state=tk.DISABLED)
        self.preview_button.config(state=tk.DISABLED)

    def enable_buttons(self):
        """Re-enable buttons after the process finishes."""
        self.execute_button.config(state=tk.NORMAL)
        self.preview_button.config(state=tk.NORMAL)

    def clear_output_text(self, message):
        """Clear the output text and insert a new message."""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, message)
