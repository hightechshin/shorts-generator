import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from .utils.supabase_utils import delete_expired_signed_urls

def scheduled_cleanup():
    print(f"🧹 TTL cleanup 시작 at {datetime.utcnow().isoformat()}")
    try:
        delete_expired_signed_urls()
        print("✅ TTL cleanup 완료\n")
    except Exception as e:
        print(f"❌ TTL cleanup 실패: {e}\n")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_cleanup, 'interval', hours=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    print("📅 TTL 스케줄러가 시작되었습니다.")
