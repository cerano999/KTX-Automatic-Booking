import os
import time
from korail2 import Korail, TrainType
import requests

# 환경 변수에서 코레일 계정 및 텔레그램 정보 불러오기
KID = os.getenv("KID")
KPW = os.getenv("KPW")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram_message(message):
    """텔레그램으로 예매 성공 및 알림 메시지를 전송하는 함수"""
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
    try:
        # 코레일 객체 생성 및 로그인 (최신 앱 버전 대응을 위해 korail2 인스턴스 설정)
        korail = Korail(KID, KPW)
        
        # 코레일 서버의 매크로 차단 우회를 위해 내부 앱 버전/유저 아젠트 강제 지정 (가능한 경우)
        # korail2 라이브러리가 최신 버전 규격을 따르도록 세션 헤더 조정
        try:
            korail.session.headers.update({
                "User-Agent": "KorailTalk/2026 (Android; 14)",
                "X-Device-OS": "Android",
                "X-Device-App-Version": "2026.01.0" # 최신 앱 버전 형식 모방
            })
        except Exception:
            pass

        # ---------------------------------------------------------
        # [사용자 설정 변수] 예매 조건 수정 영역
        # ---------------------------------------------------------
        dpt_rs = "나주"      # 출발역
        arr_rs = "용산"      # 도착역
        date_str = "20260723" # 출발 날짜 (YYYYMMDD)
        time_str = "060000"  # 조회 시작 시간 (HHMMSS)
        
        # 좌석 옵션 설정: TrainType.ALL (일반실 + 특실 모두 포함)
        seat_preference = TrainType.ALL 
        # ---------------------------------------------------------

        print(f"[{dpt_rs} -> {arr_rs} / {date_str} / {time_str} 이후] 최신 보안 우회 조회 시작...")

        # 열차 검색
        trains = korail.search_train(
            dpt_rs, 
            arr_rs, 
            date_str, 
            time_str, 
            train_type=seat_preference
        )

        if not trains:
            print("조회된 열차가 없습니다.")
            return

        for train in trains:
            print(f"열차번호: {train.train_no} | 출발: {train.dpt_time} | 일반실: [{train.general_seat_state.strip()}] | 특실: [{train.special_seat_state.strip()}]")

            gen_status = train.general_seat_state if train.general_seat_state else ""
            spc_status = train.special_seat_state if train.special_seat_state else ""

            if "예약가능" in gen_status or "예약가능" in spc_status:
                print(f"잔여석 발견! 예매 시도 중: 열차 {train.train_no}")
                
                ticket = korail.reserve(train)
                
                success_msg = (
                    f"🎉 *KTX 예매 성공!* 🎉\n\n"
                    f"구간: {train.dpt_station} -> {train.arr_station}\n"
                    f"일시: {train.dpt_date} {train.dpt_time}\n"
                    f"열차번호: {train.train_no}\n"
                    f"지금 코레일 앱을 확인해 주세요!"
                )
                
                send_telegram_message(success_msg)
                print("예매 성공 및 텔레그램 전송 완료!")
                return

        print("조건에 맞는 열차 중 예약 가능한 잔여석이 아직 없습니다.")

    except Exception as e:
        print(f"MACRO ERROR 우회 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
