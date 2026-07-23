import os
import time
import requests
from korail2 import Korail

# ---------------------------------------------------------
# 환경 변수에서 계정 정보 불러오기
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
    
    DATE_STR = "20260727"         # 출발 날짜 (2026년 7월 27일)
    TIME_STR = "060000"           # 조회 기준 시간 (06시)
    
    START_HOUR = 6                # 검색 시작 시간 (6시)
    END_HOUR = 8                  # 검색 종료 시간 (8시)
    
    MAX_RETRIES = 40              # 반복 조회 횟수
    RETRY_DELAY = 2               # 재시도 딜레이 (초)
    # ---------------------------------------------------------

    print("1단계: 코레일 API 서버 로그인 접속 중...")
    try:
        # 코레일 API 로그인 (서버 직접 통신)
        korail = Korail(KID, KPW)
        print("✅ 코레일 로그인 성공!")
    except Exception as e:
        print(f"❌ 로그인 실패 (계정 정보를 확인해 주세요): {e}")
        return

    print(f"2단계: {DPT_STATION_NAME} -> {ARR_STATION_NAME} ({DATE_STR} {START_HOUR}~{END_HOUR}시) API 정밀 감시 시작...")
    
    booked_success = False

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"[{attempt}/{MAX_RETRIES}] 코레일 서버 잔여석 데이터 요청 중...")
        
        try:
            # 설정한 조건으로 열차 조회
            trains = korail.search_train(DPT_STATION_NAME, ARR_STATION_NAME, DATE_STR, TIME_STR)
            
            for train in trains:
                # 출발 시간 추출 (예: '062000' -> 6)
                departure_hour = int(train.dep_time[:2])
                
                # 6시에서 8시 사이의 열차인지 필터링
                if START_HOUR <= departure_hour <= END_HOUR:
                    # 일반실 예약 가능 여부 확인
                    if train.has_general_seat():
                        print(f"🎯 {train.dep_time[:4]} 출발 열차 예매 가능 좌석 포착! 즉시 예약 시도 중...")
                        
                        try:
                            # 코레일 장바구니에 승차권 예약 (결제 대기 상태)
                            korail.reserve(train)
                            
                            success_msg = (
                                f"🎉 *KTX {START_HOUR}~{END_HOUR}시 시간대 예약 성공!* 🎉\n\n"
                                f"열차: {train.train_type_name} {train.train_no}호\n"
                                f"구간: {DPT_STATION_NAME} ({train.dep_time[:4]}) -> {ARR_STATION_NAME} ({train.arr_time[:4]})\n"
                                f"일시: {DATE_STR}\n\n"
                                f"⚠️ *주의:* 코레일톡 앱에 접속하여 **20분 내에 결제**를 완료해야 발권이 확정됩니다!"
                            )
                            send_telegram_message(success_msg)
                            print("✅ 예약 성공 및 텔레그램 전송 완료!")
                            booked_success = True
                            break
                        except Exception as reserve_err:
                            print(f"예약 처리 중 서버 거부: {reserve_err}")
                            continue
                            
        except Exception as e:
            print(f"API 조회 중 통신 오류 발생: {e}")

        if booked_success:
            break
        else:
            print(f"조건 범위 내 잔여석 없음. {RETRY_DELAY}초 후 서버에 재요청합니다.")
            time.sleep(RETRY_DELAY)

    if not booked_success:
        print("설정된 최대 재시도 횟수 동안 범위 내 예약 가능한 잔여석이 발견되지 않았습니다.")

if __name__ == "__main__":
    main()
