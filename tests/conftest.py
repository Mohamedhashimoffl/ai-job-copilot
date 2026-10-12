import os
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("SUPABASE_URL", "https://dummy-test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummy-test-key")
os.environ.setdefault("GEMINI_API_KEY", "dummy-gemini-key")
