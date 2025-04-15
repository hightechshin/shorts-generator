from datetime import datetime, timedelta
import re

DATE_KEYWORDS = {
    "오늘": 0,
    "내일": 1,
    "모레": 2,
    "내일모레": 2,
    "글피": 3,
    "어제": -1,
    "그제": -2,
    "그저께": -2,
}

HOUR_KEYWORDS = {
    "새벽": 3,
    "아침": 8,
    "오전": 10,
    "점심": 12,
    "정오": 12,
    "오후": 15,
    "저녁": 18,
    "밤": 21,
    "자정": 0,
}

RELATIVE_KEYWORDS = {
    "지금": 0,
    "곧": 30,
    "이따가": 60,
    "조금 전": -10,
    "방금": -5,
    "한 시간 뒤": 60,
    "두 시간 뒤": 120,
    "30분 뒤": 30,
}

def parse_natural_time(text: str) -> str:
    now = datetime.now()
    text = text.strip()

    # 상대 시간 우선 처리
    for key, minutes in RELATIVE_KEYWORDS.items():
        if key in text:
            target = now + timedelta(minutes=minutes)
            return target.strftime("%Y-%m-%dT%H:%M:%S")

    # 날짜 처리
    base_date = now
    for key, delta in DATE_KEYWORDS.items():
        if key in text:
            base_date += timedelta(days=delta)
            break

    # 시간대 + 시각 조합
    hour = None
    for key, base_hour in HOUR_KEYWORDS.items():
        if key in text:
            hour = base_hour
            break

    # 숫자 시각 파싱 (예: "7시")
    match = re.search(r"(\d{1,2})시", text)
    if match:
        parsed_hour = int(match.group(1))
        if hour is not None:
            # 예: "오후 3시" → base 15시 + 3시 → 최종 15시 (덮어씀)
            hour = parsed_hour if hour < 12 else parsed_hour + 12 if parsed_hour < 12 else parsed_hour
        else:
            hour = parsed_hour

    if hour is None:
        hour = 9  # 기본값: 오전 9시

    target = base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
    return target.strftime("%Y-%m-%dT%H:%M:%S")
