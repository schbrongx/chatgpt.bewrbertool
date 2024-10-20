# webpage_saver.py
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import base64
from urllib.parse import urljoin
import re
import sys
import PyPDF2
import requests
from io import BytesIO


def fetch_rendered_page(url):
    try:
        # Launch a headless browser instance using pyppeteer
        print("webpage_saver.fetch_rendered_page: launching headless browser")
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Headless mode
        chrome_options.add_argument("--disable-gpu")  # Optional, disable GPU acceleration
    
        driver = webdriver.Chrome(service=Service("static\\chromedriver.exe"), options=chrome_options)

        print(f"webpage_saver.fetch_rendered_page: Loading {url}")
        # Öffne die URL
        driver.get(url)
        time.sleep(1)
        rendered_html = driver.page_source
        driver.quit()
    
        print("webpage_saver.fetch_rendered_page: returning content")
        return rendered_html, None
    
    except Exception as e:
        # Return None and the error message if an exception occurs
        return None, f"Error fetching rendered page: {e}"


def inline_css_resources(css_content, css_base_url):
    # Regular expression to find all url(...) patterns in the CSS
    url_pattern = re.compile(r'url\(([^)]+)\)')
    # Find all matches of the pattern
    matches = url_pattern.findall(css_content)
    for url in matches:
        # Clean up the URL by removing quotes and whitespace
        url = url.strip('\'" \n\t\r')
        # Resolve the full URL relative to the CSS base URL
        full_url = urljoin(css_base_url, url)
        try:
            # Fetch the resource synchronously using requests
            res = requests.get(full_url)
            res.raise_for_status()  # Ensure the request was successful
            # Get the MIME type from the response headers
            mime_type = res.headers.get('Content-Type', 'application/octet-stream')
            # Read the content of the resource
            content = res.content
            # Encode the content in base64
            encoded = base64.b64encode(content).decode('utf-8')
            # Create a data URI with the MIME type and encoded content
            data_uri = f'data:{mime_type};base64,{encoded}'
            # Replace the original URL in the CSS with the data URI
            original_url_pattern = re.compile(re.escape(f'url({url})'))
            css_content = original_url_pattern.sub(f'url({data_uri})', css_content)
        except requests.RequestException:
            # Print a message if the resource cannot be fetched
            print(f"Failed to fetch CSS resource: {full_url}")
    return css_content


def inline_resources(html_content, base_url):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove <div> elements with specific IDs
    for id_to_remove in ['cmpbox', 'cmpbox2']:
        div_to_remove = soup.find('div', id=id_to_remove)
        if div_to_remove:
            # Remove the element from the soup
            div_to_remove.decompose()

    # Remove all <script> tags to disable JavaScript execution
    for script_tag in soup.find_all('script'):
        script_tag.decompose()

    # Inline external CSS files
    for link_tag in soup.find_all('link', rel='stylesheet'):
        href = link_tag.get('href')
        if href:
            # Resolve the full URL of the CSS file
            css_url = urljoin(base_url, href)
            try:
                # Fetch the CSS file synchronously using requests
                css_response = requests.get(css_url)
                css_response.raise_for_status()
                # Read the CSS content
                css_content = css_response.text
                # Inline any resources referenced within the CSS content
                css_content = inline_css_resources(css_content, css_url)
                # Create a new <style> tag with the inlined CSS content
                new_tag = soup.new_tag('style')
                new_tag.string = css_content
                # Replace the original <link> tag with the new <style> tag
                link_tag.replace_with(new_tag)
            except requests.RequestException:
                # Print a message if the CSS file cannot be fetched
                print(f"Failed to fetch CSS: {css_url}")

    # Inline <img> tags by converting their sources to data URIs
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src:
            # Resolve the full URL of the image
            img_url = urljoin(base_url, src)
            try:
                # Fetch the image synchronously using requests
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                # Get the MIME type from the response headers
                mime_type = img_response.headers.get('Content-Type', 'image/png')
                # Read the image content
                content = img_response.content
                # Encode the image content in base64
                encoded_string = base64.b64encode(content).decode('utf-8')
                # Set the 'src' attribute to the data URI
                img_tag['src'] = f'data:{mime_type};base64,{encoded_string}'
            except requests.RequestException:
                # Print a message if the image cannot be fetched
                print(f"Failed to fetch Image: {img_url}")

    # Inline iframe content by fetching and processing it recursively
    for iframe_tag in soup.find_all('iframe'):
        src = iframe_tag.get('src')
        if src:
            # Resolve the full URL of the iframe
            iframe_url = urljoin(base_url, src)
            try:
                # Fetch the rendered content of the iframe
                iframe_content, error = fetch_rendered_page(iframe_url)
                if error:
                    # Print an error message if fetching fails
                    print(f"Failed to fetch iframe content: {iframe_url}. Error: {error}")
                    continue
                # Process the iframe content to inline its resources
                inlined_iframe_content = inline_resources(iframe_content, iframe_url)
                # Create a new <div> tag with the inlined iframe content
                new_tag = soup.new_tag('div')
                new_tag.append(BeautifulSoup(inlined_iframe_content, 'html.parser'))
                # Replace the original <iframe> tag with the new <div> tag
                iframe_tag.replace_with(new_tag)
            except Exception as e:
                # Print a message if processing fails
                print(f"Failed to process iframe content: {iframe_url}. Error: {e}")

    # Remove 'overflow: hidden' styles from <body> tags
    for body_tag in soup.find_all('body'):
        if 'style' in body_tag.attrs:
            # Split the style attribute into individual styles
            styles = body_tag['style'].split(';')
            # Clean up and filter out 'overflow: hidden' styles
            styles = [s.strip() for s in styles if s.strip() != '']
            new_styles = []
            for style in styles:
                if not re.match(r'overflow\s*:\s*hidden', style, re.IGNORECASE):
                    new_styles.append(style)
            if new_styles:
                # Update the style attribute with the remaining styles
                body_tag['style'] = '; '.join(new_styles)
            else:
                # Remove the style attribute if empty
                del body_tag['style']

    # Inline PDF content
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.endswith('.pdf'):
            pdf_url = urljoin(base_url, href)
            try:
                # Extrahiere den PDF-Text und füge ihn in die HTML ein
                pdf_text = extract_text_from_pdf(pdf_url)
                # Erstelle ein neues <div>-Tag für den PDF-Inhalt
                new_tag = soup.new_tag('div')
                new_tag.string = f"PDF-Inhalt von {pdf_url}:\n\n{pdf_text}"
                # Füge den PDF-Inhalt direkt nach dem <a>-Tag ein
                a_tag.insert_after(new_tag)
            except Exception as e:
                print(f"Failed to fetch PDF content from: {pdf_url}. Error: {e}")

    # Return the modified HTML content as a string
    return str(soup)


def extract_text_from_pdf(pdf_url):
    try:
        # Download the PDF content
        response = requests.get(pdf_url)
        response.raise_for_status()

        # Load the PDF content into PyPDF2
        with BytesIO(response.content) as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            # Extract text from each page
            for page in reader.pages:
                text += page.extract_text()
        return text

    except requests.RequestException as e:
        print(f"Failed to download PDF from {pdf_url}. Error: {e}")
        return "Error: Could not fetch PDF."

    except Exception as e:
        print(f"Error while processing PDF from {pdf_url}. Error: {e}")
        return "Error: Could not process PDF."


def save_webpage(url, output_file):
    try:
        rendered_html, error = fetch_rendered_page(url)
        if error:
            return False, error
        
        # Process the HTML content to inline resources
        rendered_html = inline_resources(rendered_html, url)

        # Write the processed HTML content to the specified output file
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(rendered_html)
        # Return success
        return True, None

    except Exception as e:
        return False, f"Failed to save the webpage: {e}"
