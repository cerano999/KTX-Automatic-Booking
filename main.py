import os
import time
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
    DPT_STATION = "나주"          # 출발역
    ARR_STATION = "용산"          # 도착역
    DATE_STR = "20260723"         # 출발 날짜 (YYYYMMDD)
    TIME_STR = "060000"           # 조회 시작 시간 (06시 정각)
    
    # 좌석 옵션: "ALL"(전체), "GENERAL"(일반실만), "SPECIAL"(특실만)
    SEAT_PREFERENCE = "ALL"
    
    # 반복 조회 횟수 및 딜레이
    MAX_RETRIES = 20
    RETRY_DELAY = 3
    # ---------------------------------------------------------

    print("korail2 API 모듈을 통한 6~8시 KTX 실시간 감시 시작...")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 코레일 객체 생성 및 로그인
            korail = Korail(KID, KPW)
            
            # 06시 기준으로 열차 검색 (korail2 표준 위치 인자 사용)
            trains = korail.search_train(
                DPT_STATION,
                ARR_STATION,
                DATE_STR,
                TIME_STR,
                train_type=TrainType.KTX
            )

            if not trains:
                print(f"[{attempt}/{MAX_RETRIES}] 조회된 열차가 없습니다. {RETRY_DELAY}초 후 재시도...")
                time.sleep(RETRY_DELAY)
                continue

            booked = False
            for train in trains:
                # 출발 시간 시각 추출 (예: "061500" -> 시간은 "06")
                dep_hour = int(train.dep_time[:2])
                
                # [요청 반영] 정확히 6시부터 8시 사이의 열차만 타겟팅
                if 6 <= dep_hour < 8:
                    print(f"열차 발견: {train.dep_date} {train.dep_time} 출발 (열차번호: {train.train_no})")
                    
                    general_seat = train.general_seat_state
                    special_seat = train.special_seat_state
                    
                    print(f"일반실 상태: {general_seat} / 특실 상태: {special_seat}")

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
                        print(f"🎉 6~8시 시간대 열차 {target_to_book} 잔여석 포착! 예매 시도 중...")
                        
                        reservation = korail.reserve(train)
                        
                        success_msg = (
                            f"🎉 *KTX 6~8시 시간대 예매 성공!* 🎉\n\n"
                            f"구간: {DPT_STATION} -> {ARR_STATION}\n"
                            f"일시: {train.dep_date} {train.dep_time} ({target_to_book})\n"
                            f"열차번호: {train.train_no}\n"
                            f"코레일 앱에서 결제를 완료해 주세요!"
                        )
                        send_telegram_message(success_msg)
                        print("예매 성공 및 텔레그램 전송 완료!")
                        booked = True
                        break
                    else:
                        print(f"{train.dep_time} 출발 열차는 현재 잔여석이 매진 상태입니다.")

            if booked:
                break
            else:
                print(f"[{attempt}/{MAX_RETRIES}] 6~8시 범위 내 예매 가능한 좌석 없음. {RETRY_DELAY}초 후 재시도...")
                time.sleep(RETRY_DELAY)

        except Exception as e:
            print(f"예매 처리 중 오류 발생: {e}")
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    main()
