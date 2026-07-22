import os
import time
import requests
from korail2 import Korail

def run_ktx_macro():
    # GitHub Secrets에 등록된 환경 변수 불러오기
    ktx_id = os.environ.get("KID")
    ktx_pw = os.environ.get("KPW")
    tg_token = os.environ.get("TG_TOKEN")
    tg_chat_id = os.environ.get("TG_CHAT_ID")
    
    try:
        print("🚀 KTX 자동 예매 스크립트 실행 시작...")
        korail = Korail(ktx_id, ktx_pw)
        
        # 💡 [여정 및 시간 범위 설정 구간]
        dep = "나주"
        arr = "용산"
        date = "20260723"          # 예매 날짜 (YYYYMMDD)
        start_time = "080000"     # 탐색 시작 시간 (HHMMSS 형식, 오전 8시)
        range_hours = 3           # ⏰ 8시부터 몇 시간 동안 탐색할 것인지 지정 (예: 3시간 = 8시, 9시, 10시 대 열차 모두 조회)
        
        # 기준 시간을 분(Minute) 단위로 변환
        base_hour = int(start_time[:2])
        base_minute = int(start_time[2:4])
        base_total_min = base_hour * 60 + base_minute
        
        target_trains = []
        
        # 지정한 시간 범위(시간 단위)만큼 순차적으로 열차 조회
        for h in range(range_hours):
            current_total_min = base_total_min + (h * 60)
            cur_h = current_total_min // 60
            cur_m = current_total_min % 60
            
            # HHMMSS 형식으로 시간 문자열 생성 (예: 080000, 090000, 100000)
            time_slot = f"{cur_h:02d}{cur_m:02d}00"
            
            print(f"🔍 [{dep} → {arr}] {date} {time_slot[:4]}경 기준 열차 조회 중...")
            try:
                trains = korail.search_train(dep, arr, date, time_slot)
                if trains:
                    target_trains.extend(trains)
            except Exception as e:
                print(f"⚠️ {time_slot[:4]} 시간대 조회 중 오류 발생: {e}")
            
            # 서버 부하 방지를 위한 짧은 대기
            time.sleep(1)
        
        if not target_trains:
            print("⏳ 조건에 맞는 열차가 없습니다.")
            return

        print(f"📋 총 {len(target_trains)}개의 열차를 확인했습니다. 잔여석 검사 중...")
        
        # 중복 열차 제거 및 시간순 정렬 (필요시)
        # 조회된 열차들을 순회하며 잔여석 확인
        for train in target_trains:
            if train.general_seat_available():
                print(f"🎉 [{train.dep_time} 출발] 잔여석 발견! 예매 시도 중...")
                seat = korail.reserve(train)
                print(f"✅ 예매 성공: {seat}")
                
                # 텔레그램 알림 전송
                msg = (
                    f"🎉 [KTX] 예매 성공!\n"
                    f"▶ {dep} → {arr}\n"
                    f"▶ {date[:4]}-{date[4:6]}-{date[6:]} {train.dep_time} 출발\n"
                    f"⚠️ 10분 내로 코레일 앱에서 결제하세요!"
                )
                url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
                requests.post(url, data={"chat_id": tg_chat_id, "text": msg})
                break
        else:
            print("⏳ 탐색 범위 내에 잔여석이 있는 열차가 없습니다.")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    run_ktx_macro()
