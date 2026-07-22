import os
import requests
from korail2 import Korail, TrainType

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

    print("korail2 모듈을 통한 KTX 자동 예매 감시 시작...")

    try:
        # 코레일 객체 생성 및 로그인
        korail = Korail(KID, KPW)
        print("코레일 멤버십 로그인 성공.")

        # 열차 조회 요청
        # 승차일자는 YYYYMMDD 형식, 시간은 HHMMSS 형식
        trains = korail.search_train(
            dpt=DPT_STATION,
            arr=ARR_STATION,
            date=DATE_STR,
            time=TIME_STR,
            train_type=TrainType.KTX  # KTX 지정
        )

        if not trains:
            print("조회된 열차가 없습니다.")
            return

        booked = False
        for train in trains:
            # 06시 정각 열차 매칭 (출발 시간이 '06'으로 시작하는지 확인)
            if train.dep_time.startswith("06"):
                print(f"6시 열차 발견: {train.dep_date} {train.dep_time} 출발 (열차번호: {train.train_no})")
                
                # 일반실/특실 잔여석 상태 확인
                # korail2 라이브러리는 일반실/특실 예약 가능 여부를 속성으로 제공합니다.
                general_seat = train.general_seat_state
                special_seat = train.special_seat_state
                
                print(f"일반실 상태: {general_seat} / 특실 상태: {special_seat}")

                # 예약 가능 상태 체크 (보통 'RESERVE' 또는 '예약가능' 관련 상태값 반환)
                can_book_general = general_seat != "FULL" and "매진" not in general_seat
                can_book_special = special_seat != "FULL" and "매진" not in special_seat

                target_to_book = None
                if SEAT_PREFERENCE == "GENERAL" and can_book_general:
                    target_to_book = "일반실"
                elif SEAT_PREFERENCE == "SPECIAL" and can_book_special:
                    target_to_book = "특실"
                elif SEAT_PREFERENCE == "ALL":
                    if can_book_general:
                        target_to_book = "일반실"
                    elif can_book_special:
                        target_to_book = "특실"

                if target_to_book:
                    print(f"🎉 6시 열차 {target_to_book} 잔여석 포착! 예매 시도 중...")
                    
                    # 실제 예약 실행 코드 (reserve 메서드)
                    # korail.reserve(train)을 통해 즉시 예약을 확정합니다.
                    reservation = korail.reserve(train)
                    
                    success_msg = (
                        f"🎉 *KTX 6시 정각 열차 예매 성공!* 🎉\n\n"
                        f"구간: {DPT_STATION} -> {ARR_STATION}\n"
                        f"일시: {DATE_STR} 06:00 ({target_to_book})\n"
                        f"열차번호: {train.train_no}\n"
                        f"코레일 앱에서 결제를 완료해 주세요!"
                    )
                    send_telegram_message(success_msg)
                    print("예매 성공 및 텔레그램 전송 완료!")
                    booked = True
                    break
                else:
                    print("6시 열차는 존재하나 현재 잔여석이 매진 상태입니다.")

        if not booked:
            print("현재 조건에 맞는 6시 열차 예매 가능한 좌석이 없습니다.")

    except Exception as e:
        print(f"예매 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
