import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------
# 계정 정보 설정 (로컬 실행 시 여기에 직접 입력하세요)
# ---------------------------------------------------------
KID = os.getenv("KID", "여기에_코레일_아이디_입력")
KPW = os.getenv("KPW", "여기에_코레일_비밀번호_입력")
TG_TOKEN = os.getenv("TG_TOKEN", "여기에_텔레그램_토큰_입력")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "여기에_텔레그램_챗아이디_입력")

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
    
    DATE_STR = "20260727"         # 출발 날짜 (YYYYMMDD)
    BASE_TIME_STR = "060000"      # 조회 기준 시간 (06시)
    
    START_HOUR = 6                # 검색 시작 시간 (6시)
    END_HOUR = 8                  # 검색 종료 시간 (8시)
    
    SEAT_PREFERENCE = "ALL"       # 좌석 옵션 ("ALL", "GENERAL", "SPECIAL")
    
    MAX_RETRIES = 40              # 반복 조회 횟수
    RETRY_DELAY = 2               # 재시도 딜레이 (초)
    # ---------------------------------------------------------

    print("크롬 브라우저 초기화 중 (로컬 PC 환경)...")
    chrome_options = Options()
    
    # 개인 PC에서 화면을 직접 보기 위해 headless 옵션 비활성화
    # chrome_options.add_argument("--headless=new")
    
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })

    try:
        wait = WebDriverWait(driver, 15)

        print("1단계: 코레일 로그인 페이지 접속 중...")
        driver.get("https://www.letskorail.com/korail/com/login.do")
        time.sleep(3)

        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass

        try:
            id_input = wait.until(EC.presence_of_element_located((By.ID, "txtMember")))
            pw_input = wait.until(EC.presence_of_element_located((By.ID, "txtPwd")))
            
            id_input.clear()
            id_input.send_keys(KID)
            pw_input.clear()
            pw_input.send_keys(KPW)
            pw_input.send_keys(Keys.RETURN)
            
            time.sleep(4)
            
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except:
                pass
                
            print("✅ 코레일 로그인 완벽 성공.")
            
        except Exception as login_err:
            print(f"❌ 로그인 입력창을 찾을 수 없습니다. (예외: {login_err})")
            return

        print(f"2단계: {DPT_STATION_NAME} -> {ARR_STATION_NAME} ({DATE_STR} {START_HOUR}~{END_HOUR}시) 안전 감시 시작...")
        
        seat_code = "000"
        if SEAT_PREFERENCE == "GENERAL":
            seat_code = "011"
        elif SEAT_PREFERENCE == "SPECIAL":
            seat_code = "012"

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
            time.sleep(4.0)

            try:
                alert = driver.switch_to.alert
                alert.accept()
            except:
                pass

            try:
                buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '예약하기') or contains(text(), '신청') or contains(@alt, '예약하기') or contains(@alt, '신청하기')]")
                
                for btn in buttons:
                    try:
                        if btn.tag_name.lower() == 'img':
                            click_target = btn.find_element(By.XPATH, "./parent::a")
                        else:
                            click_target = btn

                        row = click_target.find_element(By.XPATH, "./ancestor::tr")
                        row_text = row.text
                        
                        if any(f"{h:02d}:" in row_text for h in range(START_HOUR, END_HOUR)):
                            print(f"🎯 {START_HOUR}시~{END_HOUR}시 시간대 열차 예매 버튼 포착! 클릭 진행 중...")
                            
                            driver.execute_script("arguments[0].click();", click_target)
                            time.sleep(4) 
                            
                            try:
                                alert = driver.switch_to.alert
                                alert.accept()
                            except:
                                pass

                            success_msg = (
                                f"🎉 *KTX {START_HOUR}~{END_HOUR}시 시간대 예매 성공!* 🎉\n\n"
                                f"구간: {DPT_STATION_NAME} -> {ARR_STATION_NAME}\n"
                                f"일시: {DATE_STR} ({START_HOUR}:00 ~ {END_HOUR}:00)\n"
                                f"코레일톡 앱에서 장바구니/예약내역을 신속하게 확인해 주세요!"
                            )
                            send_telegram_message(success_msg)
                            print("✅ 예매 완료 및 텔레그램 알림 전송 성공!")
                            booked_success = True
                            break
                    except Exception:
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
        # 예매 성공 시 결과를 직접 확인할 수 있도록 창을 10분간 열어둡니다.
        if booked_success:
            time.sleep(600)
        driver.quit()

if __name__ == "__main__":
    main()
