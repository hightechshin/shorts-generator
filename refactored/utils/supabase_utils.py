# 📁 utils/supabase_utils.py
import os
import requests
from config import SUPABASE_UPLOAD, SUPABASE_SERVICE_KEY, SUPABASE_STORAGE, SUPABASE_BUCKET, SUPABASE_REST, TTL_SECONDS
from datetime import datetime, timedelta

def fix_url(url):
    return url if url and url.startswith("http") else f"https:{url}" if url else None

def upload_to_supabase(file_content, file_name, file_type):
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": file_type
    }
    upload_url = f"{SUPABASE_UPLOAD}/{file_name}"
    res = requests.post(upload_url, headers=headers, data=file_content)
    return res.status_code in [200, 201]

def get_signed_url(file_name):
    if file_name.startswith("uploads/"):
        file_name = file_name.replace("uploads/", "", 1)

    url = f"{SUPABASE_STORAGE}/object/sign/{SUPABASE_BUCKET}/{file_name}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    res = requests.post(url, headers=headers, json={"expiresIn": TTL_SECONDS})
    if res.status_code == 200:
        signed_path = res.json().get("signedURL")
        return f"{SUPABASE_STORAGE}{signed_path}"
    return None

def delete_expired_signed_urls():
    cutoff = datetime.utcnow() - timedelta(hours=1)
    cutoff_iso = cutoff.isoformat()

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    payload = {
        "video_signed_url": None,
        "audio_signed_url": None,
        "image_signed_url": None,
        "signed_created_at": None
    }

    url = f"{SUPABASE_REST}/videos?signed_created_at=lt.{cutoff_iso}"
    res = requests.patch(url, headers=headers, json=payload)

    if res.status_code in [200, 204]:
        print("✅ TTL cleanup 완료")
    else:
        print("❌ TTL cleanup 실패:", res.text)

def supabase_get_video_by_uuid(uuid):
    res = requests.get(
        f"{SUPABASE_REST}/videos?uuid=eq.{uuid}",
        headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
    )
    return res.json()[0] if res.status_code == 200 and res.json() else None

def supabase_update_signed_urls(uuid, data: dict):
    res = requests.patch(
        f"{SUPABASE_REST}/videos?uuid=eq.{uuid}",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        },
        json=data
    )
    return res.status_code in [200, 204]
