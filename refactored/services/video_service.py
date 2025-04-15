def handle_upload_and_generate(req):
    # 여기에 영상 생성 전체 흐름 넣기
    return {"status": "video 생성 구조 준비 완료"}

def handle_get_signed_urls(req):
    # signed URL 재생성
    return {"status": "signed URL 반환 구조 준비 완료"}

def handle_cleanup_ttl():
    # TTL 만료 데이터 삭제
    return {"status": "TTL 정리 구조 준비 완료"}, 200