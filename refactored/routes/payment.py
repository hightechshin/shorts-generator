from services.payment_service import update_user_paid_status

# ...
if event["type"] == "checkout.session.completed":
    session = event["data"]["object"]
    user_id = session["metadata"].get("user_id")

    # ✅ 실제 플래그 반영
    success = update_user_paid_status(user_id)
    print(f"✅ 결제 완료 → Supabase 업데이트: {user_id} | 성공 여부: {success}")
