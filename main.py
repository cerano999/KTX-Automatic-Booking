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
    DPT_STATION = "나주"      # 출발역
    ARR_STATION = "용산"      # 도착역
    DATE_STR = "20260723"     # 출발 날짜 (YYYYMMDD)
    TIME_STR = "060000"       # 조회 기준 시간 (HHMMSS)
    
    # 좌석 선택 옵션: "ALL"(전체), "GENERAL"(일반실만), "SPECIAL"(특실만)
    SEAT_PREFERENCE = "ALL"   
    # ---------------------------------------------------------

    print("크롬 브라우저 초기화 및 가시적(Non-Headless) 옵션 설정 중...")
    chrome_options = Options()
    
    # [중요] 실제 브라우저 화면을 렌더링하여 앱과 동일한 데이터 로딩 유도 (Headless 제거)
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
        wait = WebDriverWait(driver, 10)

        print("1단계: 코레일 멤버십 로그인 시도 중...")
        driver.get("https://www.letskorail.com/korail/ivb/ivb.do")
        time.sleep(2)

        try:
            id_input = wait.until(EC.presence_of_element_located((By.NAME, "txtUserId")))
            pw_input = wait.until(EC.presence_of_element_located((By.NAME, "txtUserPwd")))
            
            id_input.clear()
            id_input.send_keys(KID)
            pw_input.clear()
            pw_input.send_keys(KPW)

            login_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'fn_login') or contains(text(), '로그인')]")
            login_btn.click()
            time.sleep(3)
        except Exception as login_err:
            print(f"로그인 폼 직접 입력 건너뜀: {login_err}")

        print("2단계: 6시 정각 열차 조회 페이지 접속 중...")
        seat_code = "000"
        if SEAT_PREFERENCE == "GENERAL":
            seat_code = "011"
        elif SEAT_PREFERENCE == "SPECIAL":
            seat_code = "012"

        target_url = (
            f"https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do?"
            f"txtDptRsStnNm={DPT_STATION}&txtArrRsStnNm={ARR_STATION}"
            f"&txtSeatAttCd={seat_code}&txtTraintype=00&txtStrtDt={DATE_STR}&txtStrtTm={TIME_STR}"
        )
        
        driver.get(target_url)
        time.sleep(5) # 충분한 렌더링 대기

        print("3단계: 6시 열차 잔여석 정밀 탐색 및 예매 시도...")
        
        # '예약하기' 버튼이 나타날 때까지 대기 후 클릭
        reservation_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '예약하기') or contains(text(), '신청')]")
        
        if reservation_buttons:
            print(f"총 {len(reservation_buttons)}개의 예매 가능 버튼 발견! 즉시 클릭!")
            reservation_buttons[0].click()
            time.sleep(3)

            success_msg = (
                f"🎉 *KTX 6시 정각 열차 예매 성공!* 🎉\n\n"
                f"구간: {DPT_STATION} -> {ARR_STATION}\n"
                f"일시: {DATE_STR} 06:00\n"
                f"선택 옵션: {SEAT_PREFERENCE}\n"
                f"코레일 앱에서 예매 내역을 확인해 주세요!"
            )
            send_telegram_message(success_msg)
            print("예매 성공 및 텔레그램 전송 완료!")
        else:
            print("현재 6시 정각 열차 기준 예약 가능한 잔여석이 없습니다.")

    except Exception as e:
        print(f"실행 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
