import os
from dotenv import load_dotenv

# Load real environment variables from .env
load_dotenv()

# Fallback fake values for unit tests so they never crash if .env is missing
os.environ.setdefault("SUPABASE_URL", "https://dummy-test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummy-test-key")
os.environ.setdefault("GEMINI_API_KEY", "dummy-gemini-key")
