import os
import time
from korail2 import Korail, AdultPassenger

def run_ktx_macro():
    # GitHub Secrets에서 안전하게 가져오는 계정 정보
    ktx_id = os.environ.get("KID")
    ktx_pw = os.environ.get("KPW")
    
    # 텔레그램 봇 정보
    tg_token = os.environ.get("TG_TOKEN")
    tg_chat_id = os.environ.get("TG_CHAT_ID")
    
    try:
        print("KTX 자동 예매 스크립트 실행 중...")
        korail = Korail(ktx_id, ktx_pw)
        
        # 예매 조건 설정 (예: 서울 -> 부산, 날짜, 시간)
        dep = "서울"
        arr = "부산"
        date = "20260710"
        time_slot = "080000"
        
        trains = korail.search_train(dep, arr, date, time_slot)
        
        for train in trains:
            # 잔여석이 있는 경우 예매 시도
            if train.general_seat_available():
                seat = korail.reserve(train)
                print(f"예매 성공: {seat}")
                # 텔레그램 알림 전송 로직 추가 가능
                break
                
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    run_ktx_macro()
