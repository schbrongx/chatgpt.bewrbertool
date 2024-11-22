# Job Application Generator with ChatGPT

This repository contains a Python application that helps generate job application documents using OpenAI's ChatGPT. The application comes with a graphical user interface built with `tkinter`, making it easy for users to input job ad URLs, generate tailored job applications, and even create Word documents based on specific templates. The project was developed to assist in quickly generating personalized applications, saving both time and effort.

It is by no means a polished project, initially I developed it for personal use, but maybe someone wants to use it.

## Features

- **Graphical User Interface (GUI):** Built with `tkinter`, offering an intuitive way to interact with the tool.
- **Job Ad Parsing:** Fetch job ads directly from a provided URL, including handling iframes and PDFs.
- **Customizable Query:** Allows users to modify the prompt sent to ChatGPT.
- **Word Document Generation:** Create a complete job application in a Word document using a customizable template.
- **Async Operations:** Ensures smooth user experience with non-blocking tasks and asynchronous functions.
- **Logging Panel:** Displays log messages within the application GUI for easy debugging and tracking of processes.

## Installation

### Prerequisites
- Python 3.8+
- `tkinter` (comes pre-installed with most Python distributions)
- The following Python packages:
  - `openai`
  - `requests`
  - `asyncio`
  - `aiohttp`
  - `PyPDF2`
  - `bs4` (BeautifulSoup4)
  - `pyttsx3` (for text-to-speech, optional)
  - `pywin32` (only for Windows to interact with Microsoft Word)
  - `pyppeteer` (for rendering web pages)

To install the dependencies, run the following command:

```sh
pip install -r requirements.txt
```

### Setting Up
1. Clone the repository:
   ```sh
   git clone https://github.com/your_username/job-app-generator.git
   cd job-app-generator
   ```
2. Ensure you have your OpenAI API key saved in a file named `chatgpt.apikey.txt` in the root directory.

3. Run the application:
   ```sh
   python main.py
   ```

### Alternative setup
1. Download the latest release. :-)

## Usage

1. **Launch the application** by running `main.py`.
2. **Select Working Folder**: Choose a directory where you want all generated documents to be saved.
3. **Provide a Job Ad URL**: Enter the URL of the job posting. The app will fetch and parse the job ad content.
4. **Modify Prompt (Optional)**: Use the settings to modify the GPT prompt to customize the generated application.
5. **Generate Application**: Click "Generate" to start the process. The generated application will be displayed in the text area and saved as a Word document if desired. This may take a while, be patient.

## File Structure
- **main.py**: Entry point of the application. Initializes the tkinter GUI.
- **gui.py**: Handles GUI logic, manages user inputs, and communicates with other components.
- **job_application_generator.py**: Contains logic for interacting with OpenAI's API to generate the job application.
- **utils.py**: Utility functions for handling settings, file operations, and fetching job ad content.
- **text_redirector.py**: Redirects text output (stdout and stderr) to the GUI for easier logging.
- **webpage_saver.py**: Contains methods to fetch and render web pages using `pyppeteer` for more complex job ads.

## Notes
- The **OpenAI API key** is required for generating job applications. Store it in a `chatgpt.apikey.txt` file.
- **Windows Only**: Interaction with Word documents requires `pywin32` to be installed.

## Known Issues
- **Rate Limits**: If the OpenAI API rate limit is exceeded, retry after some time.
- **PDF Parsing**: Extraction of text from PDFs might not always be accurate due to formatting issues.
- **Platform Compatibility**: Some features such as the Word automation are specific to Windows.

## Contributing
Feel free to open issues or submit pull requests if you find a bug or have a feature request. Contributions are always welcome!

## License
This project is licensed under the [MIT License](MIT_license.txt).

## Acknowledgements
- Thanks to [OpenAI](https://www.openai.com/) for providing the powerful language model that powers this application.
- Special thanks to the developers of `tkinter`, `selenium`, and other libraries used in this project.
- Icon provided by Freepik Flaticon https://www.flaticon.com/free-icons/document