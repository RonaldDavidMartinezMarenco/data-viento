import os
from dotenv import load_dotenv
from pathlib import Path
import google.generativeai as genai
import pprint

config_dir = Path(__file__).parent 
env_path = config_dir.parent / '.env'

load_dotenv(env_path)
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("The api_key dont exist, review your .env file")
    
try:
    genai.configure(api_key=api_key)
    print("Gemini configured")
except Exception as e:
    print(f"Error{e}")
    
try: 
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("Modelo initialized")
    
except Exception as e:
    print("Error initializing model{e}")
    
try:
    prompt = "explain me in 4 lines how to care the weather"
    response = model.generate_content(prompt)
    if response and response.text:
        print(response.text)
    else:
        print("No response text received")
except Exception as e:
    print(f"ERROR generating content: {e}")
    
    

     