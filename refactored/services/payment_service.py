import requests
import os

SUPABASE_REST = os.getenv("SUPABASE_REST")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE")

def update_user_paid_status(user_id: str) -> bool:
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"is_paid": True}
    url = f"{SUPABASE_REST}/users?user_id=eq.{user_id}"

    res = requests.patch(url, headers=headers, json=payload)
    return res.status_code in [200, 204]
