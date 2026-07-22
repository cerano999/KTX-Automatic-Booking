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
    DPT_STATION = "나주"      # 출발역
    ARR_STATION = "용산"      # 도착역
    DATE_STR = "20260723"     # 출발 날짜 (YYYYMMDD)
    TIME_STR = "060000"       # 조회 시간 (HHMMSS)
    
    # 좌석 옵션: "ALL"(전체), "GENERAL"(일반실만), "SPECIAL"(특실만)
    SEAT_PREFERENCE = "ALL"
    # ---------------------------------------------------------

    print("코레일 모바일 API 직접 통신 모듈을 통한 예매 감시 시작...")

    # 최신 코레일 톡 앱 환경을 모방하는 세션 및 헤더 설정
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918N Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 KorailTalk/2.5.0",
        "Referer": "https://www.letskorail.com/",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    })

    try:
        # 1단계: 로그인 API 요청 (코레일 멤버십 인증)
        login_url = "https://www.letskorail.com/korail/ivb/ivb.do"
        login_data = {
            "txtUserId": KID,
            "txtUserPwd": KPW,
            "selMenu": "1",
            "rad-stl": "0"
        }
        
        res_login = session.post(login_url, data=login_data)
        print("코레일 멤버십 인증 세션 생성 완료.")

        # 2단계: 승차권 조회 API 요청
        search_url = "https://www.letskorail.com/ebizprd/EbizPrdTicketPr111_i1.do"
        params = {
            "txtDptRsStnNm": DPT_STATION,
            "txtArrRsStnNm": ARR_STATION,
            "txtStrtDt": DATE_STR,
            "txtStrtTm": TIME_STR,
            "txtSeatAttCd": "000"
        }

        response = session.get(search_url, params=params)
        
        if response.status_code == 200:
            html_content = response.text
            
            # 6시 정각 열차 및 예약 가능 여부 확인
            if "06:00" in html_content and "예약하기" in html_content:
                print("🎉 [성공] 6시 정각 열차 잔여석 포착!")
                
                success_msg = (
                    f"🎉 *KTX 6시 정각 열차 예매 가능 포착!* 🎉\n\n"
                    f"구간: {DPT_STATION} -> {ARR_STATION}\n"
                    f"일시: {DATE_STR} 06:00\n"
                    f"코레일 앱에서 즉시 결제를 진행해 주세요!"
                )
                send_telegram_message(success_msg)
                print("텔레그램 알림 전송 완료!")
            else:
                print("현재 6시 정각 열차 기준 예약 가능한 잔여석이 없습니다.")
        else:
            print(f"서버 응답 오류 코드: {response.status_code}")

    except Exception as e:
        print(f"처리 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
