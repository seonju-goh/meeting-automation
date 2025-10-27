"""
일일 DM 스케줄러

매일 오전 9시(KST)에 send_daily_dm.py를 자동 실행
"""

import schedule
import time
import subprocess
from datetime import datetime
import daily_dm_config as dm_config


def run_daily_dm():
    """일일 DM 스크립트 실행"""
    print(f"\n{'='*50}")
    print(f"⏰ 스케줄 실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        result = subprocess.run(
            ["python3", "send_daily_dm.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Errors:\n{result.stderr}")
        
        print(f"\n{'='*50}")
        print(f"✅ 실행 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
    except subprocess.TimeoutExpired:
        print("❌ 타임아웃: 5분 초과")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    """스케줄러 시작"""
    
    print("🕐 일일 액션아이템 DM 스케줄러 시작")
    print(f"⏰ 발송 시간: 매일 {dm_config.SEND_TIME_KST} (한국 시간)")
    print(f"📋 설정된 사용자: {len(dm_config.USERS)}명")
    print("\n" + "="*50)
    print("스케줄러 실행 중... (종료: Ctrl+C)")
    print("="*50 + "\n")
    
    # 매일 9시에 실행
    schedule.every().day.at(dm_config.SEND_TIME_KST).do(run_daily_dm)
    
    # 즉시 테스트 실행 (첫 시작 시)
    print("🧪 초기 테스트 실행...")
    run_daily_dm()
    
    # 스케줄러 루프
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 스케줄러 종료")


