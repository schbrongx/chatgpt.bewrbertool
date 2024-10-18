## utils.py

import asyncio
import json
import os
import tkinter as tk
from bs4 import BeautifulSoup
import PyPDF2
import requests
from io import BytesIO
from urllib.parse import urljoin
from webpage_saver import fetch_rendered_page


# Constants for settings and API key file names
SETTINGS_FILE = "settings.json"
API_KEY_FILE = "chatgpt.apikey.txt"

def load_settings():
    """
    Load application settings from a JSON file.

    If the settings file exists, it reads and parses the JSON data from it.
    If the file doesn't exist, a default settings dictionary is returned.

    Returns:
    --------
    dict:
        A dictionary containing application settings. Default values include:
        - "job_query": an empty string
        - "last_urls": an empty list
        - "working_folder": None
    """
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {"job_query": "", "last_urls": [], "working_folder": None}

def save_settings(settings):
    """
    Save application settings to a JSON file.

    The settings dictionary is saved to the specified JSON file with
    an indentation level of 2 to ensure a readable format.

    Parameters:
    -----------
    settings : dict
        The settings to be saved in JSON format.
    """
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def load_api_key_from_file():
    """
    Load the OpenAI API key from a file.

    Reads the API key from the specified file and returns it as a string.
    If the file does not exist, None is returned.

    Returns:
    --------
    str or None:
        The API key as a string if found, otherwise None.
    """
    try:
        with open(API_KEY_FILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def extract_job_ad_from_url(url):
    """
    Fetch and extract the content of a job advertisement from a given URL, including iframe and PDF content.

    This function fetches the HTML content of the main page, extracts and combines all text content 
    from iframes present on the page, and searches for any linked PDFs, extracting text from those as well.

    Parameters:
    -----------
    url : str
        The URL of the job advertisement page.

    Returns:
    --------
    tuple:
        A tuple containing:
        - full_page_text (str): Combined text from the main page, iframes, and any PDF content.
        - raw_html (str): The raw HTML content of the main page.

    Raises:
    -------
    RuntimeError:
        If there is an issue with fetching the page or any iframe or PDF content.
    """
    try:
        '''
        # Fetch the main page content
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise error if the request failed
        '''

        rendered_html, error = asyncio.run(fetch_rendered_page(url))

        # Parse the main page using BeautifulSoup
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

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch job ad content from URL: {url}. Error: {str(e)}")

def extract_text_from_pdf(url):
    """
    Extract text content from a PDF located at a given URL.

    This function downloads the PDF file from the specified URL and uses PyPDF2 to extract
    the text content from the PDF.

    Parameters:
    -----------
    url : str
        The URL of the PDF file.

    Returns:
    --------
    str:
        The extracted text content from the PDF.

    Raises:
    -------
    RuntimeError:
        If there is an issue fetching or processing the PDF file.
    """
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
