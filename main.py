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
        wait = WebDriverWait(driver, 15)
        
        print("코레일 승차권 예조회 페이지 접속 중...")
        # 로그인이 풀려있거나 세션이 필요할 때를 대비해 예매 페이지 직접 접속
        driver.get("https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do")
        time.sleep(2)

        # 출발역 입력란 찾기 및 값 입력
        print(f"출발역({DPT_STATION}) 및 도착역({ARR_STATION}) 설정 중...")
        
        # 코레일 웹페이지의 출발역 입력 상자 (ID 또는 Name 셀렉터 활용)
        dpt_input = wait.until(EC.presence_of_element_located((By.NAME, "txtDptRsStnCd")))
        dpt_input.clear()
        dpt_input.send_keys(DPT_STATION)

        # 도착역 입력 상자
        arr_input = wait.until(EC.presence_of_element_located((By.NAME, "txtArrRsStnCd")))
        arr_input.clear()
        arr_input.send_keys(ARR_STATION)

        # 조회하기 버튼 클릭 (또는 조회 함수 호출)
        # 렛츠코레일 웹 표준 조회 버튼 실행
        print("열차 조회 버튼 실행 중...")
        driver.execute_script("fn_search();") # 코레일 웹사이트 내부 조회 자바스크립트 함수 호출
        
        time.sleep(3)
        print("열차 조회 결과 페이지 진입 완료.")

        # 향후 잔여석 테이블을 파싱하여 예매 버튼을 누르는 로직 구현 단계로 이어집니다.
        success_msg = "🎉 *KTX 셀레니움 매크로 실행 중* 🎉\n조건에 맞는 열차 조회를 시도했습니다."
        # 필요시 텔레그램 테스트 전송 가능
        
    except Exception as e:
        print(f"셀레니움 실행 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
