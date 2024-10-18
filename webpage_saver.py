# webpage_saver.py
import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
import base64
from urllib.parse import urljoin
import re
import aiohttp
import sys
import PyPDF2
import requests
from io import BytesIO


if sys.platform == 'win32':
    print("webpage_saver: Platform is windows, setting event loop policy to WindowsProactorEventLoopPolicy")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


async def fetch_rendered_page(url):
    """
    Fetches the fully rendered HTML content of a webpage using a headless browser.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        tuple: A tuple containing the rendered HTML content as a string and an error message (if any).
    """
    try:
        # Launch a headless browser instance using pyppeteer
        print("webpage_saver.fetch_rendered_page: launching headless browser")
        browser = await launch(
            headless=True,
            # Update the executablePath to point to your Chrome or Chromium executable if necessary
            executablePath=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        )

        # Create a new page in the browser
        print("webpage_saver.fetch_rendered_page: creating new page in browser")
        page = await browser.newPage()

        # Set a more human-like user agent
        page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

        # Navigate to the specified URL
        print(f"webpage_saver.fetch_rendered_page: navigate to {url}")
        await page.goto(url, {
            'timeout': '10000',
            'waitUntil': 'networkidle0'
        })

        # Get the page content after rendering
        print("webpage_saver.fetch_rendered_page: saving content to variable 'content'")
        content = await page.content()

        # Close the browser instance
        print("webpage_saver.fetch_rendered_page: closing browser")
        await browser.close()

        print("webpage_saver.fetch_rendered_page: returning content")
        return content, None
    except Exception as e:
        # Return None and the error message if an exception occurs
        return None, f"Error fetching rendered page: {e}"


async def inline_css_resources(css_content, css_base_url, session):
    """
    Inlines resources referenced within CSS content by converting them to data URIs.

    Args:
        css_content (str): The CSS content containing resource references.
        css_base_url (str): The base URL for resolving relative resource paths.
        session (aiohttp.ClientSession): The HTTP session for making requests.

    Returns:
        str: The CSS content with resources inlined as data URIs.
    """
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
            # Fetch the resource asynchronously using the session
            async with session.get(full_url) as res:
                res.raise_for_status()
                # Get the MIME type from the response headers
                mime_type = res.headers.get('Content-Type', 'application/octet-stream')
                # Read the content of the resource
                content = await res.read()
                # Encode the content in base64
                encoded = base64.b64encode(content).decode('utf-8')
                # Create a data URI with the MIME type and encoded content
                data_uri = f'data:{mime_type};base64,{encoded}'
                # Replace the original URL in the CSS with the data URI
                original_url_pattern = re.compile(re.escape(f'url({url})'))
                css_content = original_url_pattern.sub(f'url({data_uri})', css_content)
        except aiohttp.ClientError:
            # Print a message if the resource cannot be fetched
            print(f"Failed to fetch CSS resource: {full_url}")
    return css_content


async def inline_resources(html_content, base_url, session):
    """
    Processes the HTML content to inline all external resources such as CSS, images, and iframes.
    Also removes specified elements and styles.

    Args:
        html_content (str): The HTML content of the webpage.
        base_url (str): The base URL for resolving relative paths.
        session (aiohttp.ClientSession): The HTTP session for making requests.

    Returns:
        str: The processed HTML content with resources inlined.
    """
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
                # Fetch the CSS file asynchronously
                async with session.get(css_url) as css_response:
                    css_response.raise_for_status()
                    # Read the CSS content
                    css_content = await css_response.text()
                    # Inline any resources referenced within the CSS content
                    css_content = await inline_css_resources(css_content, css_url, session)
                    # Create a new <style> tag with the inlined CSS content
                    new_tag = soup.new_tag('style')
                    new_tag.string = css_content
                    # Replace the original <link> tag with the new <style> tag
                    link_tag.replace_with(new_tag)
            except aiohttp.ClientError:
                # Print a message if the CSS file cannot be fetched
                print(f"Failed to fetch CSS: {css_url}")

    # Inline <img> tags by converting their sources to data URIs
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src:
            # Resolve the full URL of the image
            img_url = urljoin(base_url, src)
            try:
                # Fetch the image asynchronously
                async with session.get(img_url) as img_response:
                    img_response.raise_for_status()
                    # Get the MIME type from the response headers
                    mime_type = img_response.headers.get('Content-Type', 'image/png')
                    # Read the image content
                    content = await img_response.read()
                    # Encode the image content in base64
                    encoded_string = base64.b64encode(content).decode('utf-8')
                    # Set the 'src' attribute to the data URI
                    img_tag['src'] = f'data:{mime_type};base64,{encoded_string}'
            except aiohttp.ClientError:
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
                iframe_content, error = await fetch_rendered_page(iframe_url)
                if error:
                    # Print an error message if fetching fails
                    print(f"Failed to fetch iframe content: {iframe_url}. Error: {error}")
                    continue
                # Process the iframe content to inline its resources
                inlined_iframe_content = await inline_resources(iframe_content, iframe_url, session)
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
                pdf_text = await extract_text_from_pdf(pdf_url)
                # Erstelle ein neues <div>-Tag für den PDF-Inhalt
                new_tag = soup.new_tag('div')
                new_tag.string = f"PDF-Inhalt von {pdf_url}:\n\n{pdf_text}"
                # Füge den PDF-Inhalt direkt nach dem <a>-Tag ein
                a_tag.insert_after(new_tag)
            except Exception as e:
                print(f"Failed to fetch PDF content from: {pdf_url}. Error: {e}")

    # Return the modified HTML content as a string
    return str(soup)


async def extract_text_from_pdf(pdf_url):
    """
    Fetches and extracts text from a PDF at the given URL.
    
    Args:
        pdf_url (str): The URL of the PDF file.

    Returns:
        str: Extracted text from the PDF.
    """
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


async def async_save_webpage(url, output_file):
    """
    Asynchronously saves a webpage by fetching, processing, and writing its content to a file.

    Args:
        url (str): The URL of the webpage to save.
        output_file (str): The local file path (including filename) to save the webpage.

    Returns:
        tuple: A tuple containing a success flag (bool) and an error message (if any).
    """
    try:
        # Create an asynchronous HTTP session with a custom User-Agent header
        async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
            # Fetch the rendered HTML content of the webpage
            rendered_html, error = await fetch_rendered_page(url)
            if error:
                # Return failure and the error message if fetching fails
                return False, error
            # Use the original URL as the base URL for resolving relative paths
            base_url = url

            # Process the HTML content to inline resources
            inlined_html = await inline_resources(rendered_html, base_url, session)

            # Write the processed HTML content to the specified output file
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(inlined_html)

            # Return success
            return True, None

    except Exception as e:
        # Return failure and the error message if an exception occurs
        return False, f"Failed to save the webpage: {e}"

# Make save_webpage an async function
async def save_webpage(url, output_file):
    """
    Asynchronously saves a webpage by fetching, processing, and writing its content to a file.
    
    Args:
        url (str): The URL of the webpage to save.
        output_file (str): The local file path (including filename) to save the webpage.
    
    Returns:
        tuple: A tuple containing a success flag (bool) and an error message (if any).
    """
    try:
        # Call async_save_webpage and await its completion
        success, error = await async_save_webpage(url, output_file)
        return success, error
    except Exception as e:
        return False, f"Failed to save the webpage: {e}"
