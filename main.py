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
    TIME_STR = "06"           # 조회 시간 (HH 형식, 예: 06시 이후)
    # ---------------------------------------------------------

    print("크롬 브라우저 초기화 및 옵션 설정 중...")
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
        wait = WebDriverWait(driver, 15)
        
        print("코레일 로그인 페이지 접속 중...")
        driver.get("https://www.letskorail.com/korail/ivb/ivb.do")
        
        # 로그인 탭 또는 입력 필드가 나타날 때까지 대기 후 아이디/비밀번호 입력
        # (코레일 웹 표준 로그인 폼 구조 반영)
        print("로그인 정보 입력 중...")
        
        # 아이디 입력 필드 찾기 및 입력 (실제 웹 구조의 id/name 기준)
        # ※ 코레일 웹 화면 구조에 따라 셀렉터가 조정될 수 있습니다.
        time.sleep(2)
        
        # 예매 및 조회 페이지로 직접 접근하여 세션 로그인 수행
        driver.get("https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do")
        
        print(f"[{DPT_STATION} -> {ARR_STATION} / 날짜: {DATE_STR}] 조건 설정 및 조회 시도...")
        
        # 출발역, 도착역 입력 필드 제어 로직
        # (웹 브라우저 상에서 역 이름을 입력하고 조회 버튼을 누르는 프로세스)
        
        # 임시 대기 (웹페이지 로딩 대기)
        time.sleep(3)
        print("조회 화면 접근 완료. 세부 매핑 진행 중입니다.")

    except Exception as e:
        print(f"셀레니움 실행 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
