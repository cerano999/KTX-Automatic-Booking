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

# 환경 변수에서 계정 정보 불러오기
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
    DPT_STATION_NAME = "나주"      # 출발역 이름
    ARR_STATION_NAME = "용산"      # 도착역 이름
    
    DPT_STATION_CODE = "0245"      # 나주역 코드
    ARR_STATION_CODE = "0002"      # 용산역 코드
    
    DATE_STR = "20260727"         # 출발 날짜 (2026년 7월 27일)
    BASE_TIME_STR = "060000"      # 조회 기준 시간 (06시)
    
    START_HOUR = 6                # 검색 시작 시간 (6시)
    END_HOUR = 8                  # 검색 종료 시간 (8시)
    
    MAX_RETRIES = 40              # 반복 조회 횟수
    RETRY_DELAY = 2               # 재시도 딜레이 (초)
    # ---------------------------------------------------------

    print("크롬 브라우저 초기화 및 강력한 안티보안 우회 설정 중...")
    chrome_options = Options()
    
    # 헤드리스 및 봇 탐지 우회 옵션
    chrome_options.add_argument("--headless=new") # 최신 헤드리스 모드 사용
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 자연스러운 User-Agent 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # Webdriver 속성 숨기기 (핵심 우회 로직)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })

    try:
        wait = WebDriverWait(driver, 10)

        print("1단계: 코레일 로그인 페이지 접속 중...")
        driver.get("https://www.letskorail.com/korail/ivb/ivb.do")
        time.sleep(2)

        try:
            # 안전하게 로그인 요소 대기 후 입력
            id_input = wait.until(EC.presence_of_element_located((By.ID, "txtMember")))
            pw_input = wait.until(EC.presence_of_element_located((By.ID, "txtPwd")))
            
            id_input.clear()
            id_input.send_keys(KID)
            pw_input.clear()
            pw_input.send_keys(KPW)

            login_btn = driver.find_element(By.XPATH, "//img[@alt='확인']/parent::a")
            login_btn.click()
            time.sleep(3)
            print("로그인 완료.")
        except Exception as login_err:
            print(f"로그인 예외 발생 (이미 세션이 있거나 페이지 구조 다름): {login_err}")

        print(f"2단계: {DPT_STATION_NAME} -> {ARR_STATION_NAME} ({DATE_STR} {START_HOUR}~{END_HOUR}시) 안전 감시 시작...")
        
        # 일반실 기준 URL (000: 전체, 011: 일반실)
        seat_code = "011" 

        target_url = (
            f"https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do?"
            f"txtGoStart={DPT_STATION_CODE}&txtGoEnd={ARR_STATION_CODE}"
            f"&txtDptRsStnCd={DPT_STATION_CODE}&txtArrRsStnCd={ARR_STATION_CODE}"
            f"&txtSeatAttCd={seat_code}&txtTraintype=00&txtStrtDt={DATE_STR}&txtStrtTm={BASE_TIME_STR}"
        )

        booked_success = False

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"[{attempt}/{MAX_RETRIES}] 승차권 조회 페이지 렌더링 대기 중...")
            driver.get(target_url)
            
            # 페이지 데이터가 완전히 렌더링되도록 충분한 대기 시간 부여
            time.sleep(5.0)

            try:
                # 결과 테이블 내 '예약하기' 이미지 버튼 찾기
                buttons = driver.find_elements(By.XPATH, "//img[contains(@alt, '예약하기')]/parent::a")
                
                for btn in buttons:
                    try:
                        # 해당 버튼이 속한 행(tr)의 텍스트 가져오기
                        row = btn.find_element(By.XPATH, "./ancestor::tr")
                        row_text = row.text
                        
                        # 지정한 시간대(6시~8시)에 해당하는지 확인
                        if any(f"{h:02d}:" in row_text for h in range(START_HOUR, END_HOUR)):
                            print(f"🎯 {START_HOUR}시~{END_HOUR}시 시간대 열차 예매 버튼 포착! 클릭 진행 중...")
                            
                            btn.click()
                            time.sleep(4) # 예약 처리 대기

                            success_msg = (
                                f"🎉 *KTX {START_HOUR}~{END_HOUR}시 시간대 예매 성공!* 🎉\n\n"
                                f"구간: {DPT_STATION_NAME} -> {ARR_STATION_NAME}\n"
                                f"일시: {DATE_STR}\n"
                                f"코레일 앱(코레일톡) 장바구니/예약내역에서 결제를 진행해 주세요!"
                            )
                            send_telegram_message(success_msg)
                            print("✅ 예매 완료 및 텔레그램 알림 전송 성공!")
                            booked_success = True
                            break
                    except Exception as inner_e:
                        continue
            except Exception as e:
                print(f"테이블 파싱 중 오류 발생: {e}")

            if booked_success:
                break
            else:
                print(f"조건 범위 내 잔여석 없음. {RETRY_DELAY}초 후 재시도합니다.")
                time.sleep(RETRY_DELAY)

        if not booked_success:
            print("설정된 최대 재시도 횟수 동안 범위 내 예약 가능한 잔여석이 발견되지 않았습니다.")

    except Exception as e:
        print(f"실행 중 치명적 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
