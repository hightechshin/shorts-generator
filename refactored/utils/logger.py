# utils/logger.py

import logging

# 로그 포맷 설정
FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)

# 공통 log() 함수 정의
def log(msg, level="info"):
    """
    사용 예:
    log("시작됨")
    log("오류 발생", level="error")
    """
    if level == "info":
        logging.info(msg)
    elif level == "warning":
        logging.warning(msg)
    elif level == "error":
        logging.error(msg)
    elif level == "debug":
        logging.debug(msg)
    else:
        logging.info(msg)  # fallback
