## job_application_generator.py
import openai
from utils import load_api_key_from_file

def generate_job_application(prompt):
    """Generates the job application using OpenAI's API."""
    api_key = load_api_key_from_file()
    if not api_key:
        raise ValueError("API Key is missing!")
    
    openai.api_key = api_key
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du bist ein professioneller Assistent, der auf Deutsch (Schweizer Rechtschreibung) antwortet."},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message['content']
