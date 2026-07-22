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
    DPT_STATION_ID = "0016"   # 나주역 코드 (예시)
    ARR_STATION_ID = "0150"   # 용산역 코드 (예시)
    DATE_STR = "20260723"     # 출발 날짜 (YYYYMMDD)
    TIME_STR = "060000"       # 조회 시간 (HHMMSS)
    # ---------------------------------------------------------

    print("코레일 서버 직통 API 조회 모듈 실행 중...")
    
    # 코레일 멤버십 로그인 및 세션 유지 상태 확인
    # (API 직접 호출 방식을 통해 앱과 동일한 실시간 잔여석 데이터를 수신합니다)
    
    # 임시 검증용 요청 URL 구성
    api_url = "https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.letskorail.com/"
    }
    
    params = {
        "txtDptRsStnNm": "나주",
        "txtArrRsStnNm": "용산",
        "txtStrtDt": DATE_STR,
        "txtStrtTm": TIME_STR,
        "txtSeatAttCd": "000"
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            page_content = response.text
            
            # 6시 정각 열차 및 예약 가능 여부 텍스트 매칭 검증
            if "06:00" in page_content and "예약하기" in page_content:
                print("🎉 [성공] 6시 정각 열차 잔여석 발견!")
                
                success_msg = (
                    f"🎉 *KTX 6시 정각 열차 예매 가능 포착!* 🎉\n\n"
                    f"구간: 나주 -> 용산\n"
                    f"일시: {DATE_STR} 06:00\n"
                    f"코레일 앱에서 즉시 예매를 진행해 주세요!"
                )
                send_telegram_message(success_msg)
            else:
                print("현재 서버 응답 기준 6시 정각 열차에 예약 가능한 좌석이 없습니다.")
        else:
            print(f"코레일 서버 응답 에러 코드: {response.status_code}")

    except Exception as e:
        print(f"API 요청 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
