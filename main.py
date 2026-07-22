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
    TIME_STR = "060000"       # 조회 시간 (HHMMSS 형식)
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
        print("코레일 간편 조회 URL 직접 접속 중...")
        
        # 코레일 승차권 조회 페이지로 직접 파라미터를 전달하여 우회 접속
        # (역 이름 입력 오류를 방지하기 위한 다이렉트 URL 접근 방식)
        target_url = (
            f"https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do?"
            f"txtDptRsStnNm={DPT_STATION}&txtArrRsStnNm={ARR_STATION}"
            f"&txtSeatAttCd=000&txtTraintype=00&txtStrtDt={DATE_STR}&txtStrtTm={TIME_STR}"
        )
        
        driver.get(target_url)
        time.sleep(5) # 페이지 로딩 대기

        print("페이지 접속 및 조회 파라미터 전달 완료.")
        
        # 페이지 소스 확인 또는 잔여석 파싱 준비 단계
        page_title = driver.title
        print(f"현재 페이지 타이틀: {page_title}")

        success_msg = f"🎉 *KTX 셀레니움 조회 테스트 성공* 🎉\n구간: {DPT_STATION} -> {ARR_STATION} ({DATE_STR})"
        send_telegram_message(success_msg)

    except Exception as e:
        print(f"셀레니움 실행 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
