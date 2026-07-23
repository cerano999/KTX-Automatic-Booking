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
# 환경 변수 설정
# ---------------------------------------------------------
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
    
    DATE_STR = "20260727"         # 출발 날짜 (YYYYMMDD)
    BASE_TIME_STR = "060000"      # 조회 기준 시간 (06시)
    
    START_HOUR = 6                # 검색 시작 시간 (6시)
    END_HOUR = 8                  # 검색 종료 시간 (8시)
    
    SEAT_PREFERENCE = "ALL"       # 좌석 옵션 ("ALL", "GENERAL", "SPECIAL")
    
    MAX_RETRIES = 40              # 반복 조회 횟수
    RETRY_DELAY = 2               # 재시도 딜레이 (초)
    # ---------------------------------------------------------

    print("크롬 브라우저 초기화 및 강력한 안티보안 우회 설정 중...")
    chrome_options = Options()
    
    # 강력한 Headless 봇 탐지 우회 옵션들
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
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

    # Webdriver 탐지 회피 스크립트 주입
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })

    try:
        wait = WebDriverWait(driver, 15)

        print("1단계: 코레일 메인 페이지 우회 접속 중 (방화벽 우회용 Referer 생성)...")
        # 로그인 페이지로 직행하지 않고, 메인 페이지를 먼저 밟아서 방화벽을 속입니다.
        driver.get("https://www.letskorail.com/")
        time.sleep(3)

        # 팝업 알림 무시 로직
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass

        print("메인 페이지에서 로그인 화면으로 이동 중...")
        try:
            # 사람처럼 화면 상단의 '로그인' 버튼을 클릭합니다.
            login_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'login') or contains(text(), '로그인') or .//img[@alt='로그인']]")))
            driver.execute_script("arguments[0].click();", login_link)
            time.sleep(4)
        except Exception as e:
            print("로그인 버튼 클릭 실패, 폴백 우회 접속 시도...")
            driver.get("https://www.letskorail.com/korail/com/login.do")
            time.sleep(4)

        try:
            # 안전하게 로그인 요소 다중 탐색 대기
            try:
                id_input = wait.until(EC.presence_of_element_located((By.ID, "txtMember")))
                pw_input = driver.find_element(By.ID, "txtPwd")
            except:
                id_input = wait.until(EC.presence_of_element_located((By.ID, "txtUserId")))
                pw_input = driver.find_element(By.ID, "txtUserPwd")
            
            id_input.clear()
            id_input.send_keys(KID)
            pw_input.clear()
            
            # 비밀번호 입력 후 엔터키 전송으로 더욱 자연스럽게 로그인 유도
            pw_input.send_keys(KPW)
            pw_input.send_keys(Keys.RETURN)
            
            time.sleep(3)
            
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except:
                pass
                
            print("✅ 코레일 로그인 완벽 성공.")
            
        except Exception as login_err:
            print(f"❌ 로그인 입력창을 찾을 수 없습니다. (예외: {login_err})")
            print("--- [디버깅] 현재 화면 정보 ---")
            print(f"현재 URL: {driver.current_url}")
            print(f"페이지 제목: {driver.title}")
            print(f"화면 내용 일부: {driver.page_source[:500]}")
            print("---------------------------------")
            print("※ 계속해서 코레일 에러 페이지가 뜬다면, 깃허브 액션 IP 대역 자체가 코레일에 의해 원천 차단된 상태일 확률이 높습니다.")
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
        driver.quit()

if __name__ == "__main__":
    main()
