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
        print("코레일 간편 조회 URL 접속 중...")
        target_url = (
            f"https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do?"
            f"txtDptRsStnNm={DPT_STATION}&txtArrRsStnNm={ARR_STATION}"
            f"&txtSeatAttCd=000&txtTraintype=00&txtStrtDt={DATE_STR}&txtStrtTm={TIME_STR}"
        )
        
        driver.get(target_url)
        time.sleep(5) # 페이지 렌더링 대기

        print("조회 결과 페이지 분석 시작...")
        
        # 페이지 내의 열차 정보 테이블 행(Row) 탐색
        # 코레일 웹 조회 결과 테이블의 일반실/특실 잔여석 버튼 탐색
        # '예약하기' 또는 '예약가능' 텍스트가 포함된 요소를 찾습니다.
        
        page_text = driver.page_source
        
        if "예약하기" in page_text:
            print("잔여석 발견 가능성 있음! 상세 예약 버튼 탐색 중...")
            
            # '예약하기' 버튼을 찾아 클릭하는 셀레니움 로직
            reservation_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '예약하기')]")
            
            if reservation_buttons:
                print(f"총 {len(reservation_buttons)}개의 예약 가능 버튼 발견. 첫 번째 좌석 예매 시도!")
                reservation_buttons[0].click()
                time.sleep(3)
                
                success_msg = f"🎉 *KTX 예매 버튼 클릭 성공!* 🎉\n구간: {DPT_STATION} -> {ARR_STATION} ({DATE_STR})\n앱에서 예매 내역을 확인해 주세요!"
                send_telegram_message(success_msg)
                print("예매 성공 알림 전송 완료.")
            else:
                print("텍스트는 존재하나 클릭 가능한 버튼을 특정하지 못했습니다.")
        else:
            print("현재 조건에 맞는 예약 가능한 잔여석이 없습니다.")

    except Exception as e:
        print(f"셀레니움 실행 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
