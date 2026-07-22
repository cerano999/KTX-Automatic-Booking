import os
import time
import requests

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
    
    DATE_STR = "20260727"         # 출발 날짜 (YYYYMMDD) - 2026년 7월 27일로 수정됨
    BASE_TIME_STR = "060000"      # 조회 기준 시간 (06시)
    
    START_HOUR = 6                # 검색 시작 시간 (6시)
    END_HOUR = 8                  # 검색 종료 시간 (8시)
    
    MAX_RETRIES = 40              # 반복 조회 횟수
    RETRY_DELAY = 2               # 재시도 딜레이 (초)
    # ---------------------------------------------------------

    print("코레일 서버 직접 통신을 통한 6~8시 실시간 잔여석 감시 시작...")

    # 모바일 앱 통신 규격을 모사하는 세션 설정
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 KorailTalk",
        "Referer": "https://www.letskorail.com/"
    })

    try:
        # 1단계: 로그인 세션 획득
        login_url = "https://www.letskorail.com/korail/ivb/ivb.do"
        login_data = {
            "txtUserId": KID,
            "txtUserPwd": KPW,
            "selMenu": "1",
            "rad-stl": "0"
        }
        session.post(login_url, data=login_data)
        print("로그인 세션 연결 완료.")

        # 2단계: 승차권 조회 API 반복 요청
        api_url = "https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do"

        booked_success = False

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"[{attempt}/{MAX_RETRIES}] 6시~8시 열차 잔여석 API 조회 중 (날짜: {DATE_STR})...")
            
            params = {
                "txtGoStart": DPT_STATION_CODE,
                "txtGoEnd": ARR_STATION_CODE,
                "txtDptRsStnCd": DPT_STATION_CODE,
                "txtArrRsStnCd": ARR_STATION_CODE,
                "txtStrtDt": DATE_STR,
                "txtStrtTm": BASE_TIME_STR,
                "txtTraintype": "00",
                "txtSeatAttCd": "000"
            }

            response = session.get(api_url, params=params)

            if response.status_code == 200:
                html_text = response.text
                
                # 6시부터 8시 사이 시간대와 '예약하기' 혹은 '신청' 키워드 검사
                found_target = False
                for h in range(START_HOUR, END_HOUR):
                    time_pattern = f"{h:02d}:"
                    if time_pattern in html_text and ("예약하기" in html_text or "신청" in html_text):
                        print(f"🎉 [성공] {START_HOUR}시~{END_HOUR}시 시간대 내 예매 가능 표 포착!")
                        
                        success_msg = (
                            f"🎉 *KTX {START_HOUR}~{END_HOUR}시 시간대 예매 가능 포착!* 🎉\n\n"
                            f"구간: {DPT_STATION_NAME} -> {ARR_STATION_NAME}\n"
                            f"일시: {DATE_STR} ({START_HOUR}:00 ~ {END_HOUR}:00)\n"
                            f"코레일 앱에서 즉시 결제를 진행해 주세요!"
                        )
                        send_telegram_message(success_msg)
                        print("텔레그램 알림 전송 완료!")
                        booked_success = True
                        found_target = True
                        break

                if booked_success:
                    break
                else:
                    print(f"조건 범위 내 잔여석 없음. {RETRY_DELAY}초 후 재시도합니다.")
                    time.sleep(RETRY_DELAY)
            else:
                print(f"서버 응답 오류 코드: {response.status_code}, {RETRY_DELAY}초 후 재시도...")
                time.sleep(RETRY_DELAY)

        if not booked_success:
            print("설정된 최대 재시도 횟수 동안 범위 내 예약 가능한 잔여석이 발견되지 않았습니다.")

    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
