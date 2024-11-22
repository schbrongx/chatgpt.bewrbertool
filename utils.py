## utils.py
import json
import os
import sys
import requests
from bs4 import BeautifulSoup
import PyPDF2
import requests
from io import BytesIO
from urllib.parse import urljoin
from webpage_saver import fetch_rendered_page


# Constants for settings and API key file names
if getattr(sys, 'frozen', False):
    # PyInstaller .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Normales Python-Skript
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
API_KEY_FILE = os.path.join(BASE_DIR, "chatgpt.apikey.txt")


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        print(f"INFO: load_settings(): Trying to load settings from {SETTINGS_FILE}.")
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        return settings
    return {"job_query": "", "last_urls": [], "working_folder": None}


def save_settings(settings):
    if not os.path.exists(SETTINGS_FILE):
        print(f"WARNING: save_settings: file {SETTINGS_FILE} does not exist. Creating new settings file.")
    try:
        print(f"save_settings(): Trying to save settings to {SETTINGS_FILE}")
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except (OSError) as e:
        print(f"OSError: {e.errno} - {e.strerror}")
        print("Settings will not be saved.")
        pass

def api_key_file_present():
    print(f"api_key_file_present(): Checking if API key file {API_KEY_FILE} is present.")
    if not os.path.exists(API_KEY_FILE):
        print(f"  api_key_file_present(): API key file is missing.")
        return False
    print(f"  api_key_file_present(): API key file is present.")
    return True

def load_api_key_from_file():
    try:
        with open(API_KEY_FILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


def extract_job_ad_from_url(url):
    try:
        rendered_html, error = fetch_rendered_page(url)
        if error:
            raise RuntimeError(f"Failed to fetch job ad content from URL: {url}. Error: {error}")

        soup = BeautifulSoup(rendered_html, 'html.parser')
        main_page_content = soup.get_text()

        # Find all iframe elements and attempt to fetch their content
        iframes = soup.find_all('iframe')
        iframe_content_list = []

        for iframe in iframes:
            iframe_src = iframe.get('src')
            if iframe_src:
                # Some iframe URLs might be relative, so we need to join them with the base URL
                iframe_url = urljoin(url, iframe_src)

                # Fetch iframe content
                try:
                    iframe_response = requests.get(iframe_url)
                    iframe_response.raise_for_status()
                    iframe_soup = BeautifulSoup(iframe_response.content, 'html.parser')
                    iframe_content_list.append(iframe_soup.get_text())
                except requests.RequestException as iframe_err:
                    print(f"Failed to fetch iframe content from: {iframe_url}. Error: {iframe_err}")

        # Combine the main page text with all iframe contents
        full_page_text = main_page_content + "\n".join(iframe_content_list)

        # Find and process any linked PDFs
        pdf_links = soup.find_all('a', href=True)
        for link in pdf_links:
            if link['href'].endswith('.pdf'):
                pdf_url = urljoin(url, link['href'])
                pdf_text = extract_text_from_pdf(pdf_url)
                full_page_text += "\n\n" + pdf_text

        return full_page_text, rendered_html

    except Exception as e:
        raise RuntimeError(f"Failed to fetch job ad content from URL: {url}. Error: {str(e)}")


def extract_text_from_pdf(url):
    try:
        # Fetch the PDF file
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful

        # Read the PDF content using PyPDF2
        with BytesIO(response.content) as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()

        return text

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch PDF content from URL: {url}. Error: {str(e)}")
