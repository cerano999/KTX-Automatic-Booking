import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 환경 변수 불러오기
KID = os.getenv("KID")
KPW = os.getenv("KPW")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram_message(message):
    """텔레그램 알림 전송 함수"""
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def main():
    # ---------------------------------------------------------
    # [사용자 설정 변수] 예매 조건 설정 영역
    # ---------------------------------------------------------
    DPT_STATION = "나주"      # 출발역
    ARR_STATION = "용산"      # 도착역
    DATE_STR = "20260723"     # 출발 날짜 (YYYYMMDD)
    TIME_STR = "06"           # 조회 시간 (HH 형식)
    # ---------------------------------------------------------

    print("크롬 브라우저 초기화 및 헤드리스 옵션 설정 중...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 화면 없이 백그라운드 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1920x1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        wait = WebDriverWait(driver, 20)
        
        print("코레일 승차권 조회 페이지 접속 중...")
        driver.get("https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do")
        
        # 페이지가 완전히 로드될 때까지 충분히 대기
        time.sleep(3)

        print(f"출발역({DPT_STATION}) 및 도착역({ARR_STATION}) 설정 시도 중...")
        
        # 자바스크립트를 이용해 출발역 및 도착역 입력값 강제 설정 (요소 탐색 오류 방지)
        driver.execute_script(f"document.getElementById('start').value = '{DPT_STATION}';")
        driver.execute_script(f"document.getElementById('arv').value = '{ARR_STATION}';")
        
        print("역 이름 설정 완료. 조회 함수 실행 중...")
        
        # 코레일 조회 함수 실행
        driver.execute_script("fn_search();")
        
        time.sleep(4)
        print("열차 조회 프로세스 정상 수행 완료.")

    except Exception as e:
        print(f"셀레니움 실행 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
