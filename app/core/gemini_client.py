from google import genai
import os
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"), http_options=types.HttpOptions(timeout=60000)
)
