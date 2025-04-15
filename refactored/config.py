import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

SUPABASE_BUCKET = "uploads"
SUPABASE_STORAGE = "https://your.supabase.co/storage/v1"
SUPABASE_BASE = f"{SUPABASE_STORAGE}/object"
SUPABASE_UPLOAD = f"{SUPABASE_BASE}/{SUPABASE_BUCKET}"
SUPABASE_SIGN = f"{SUPABASE_BASE}/sign/{SUPABASE_BUCKET}"
SUPABASE_REST = "https://your.supabase.co/rest/v1"
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE', '')
TTL_SECONDS = 3600
