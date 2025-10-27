"""
일일 액션아이템 DM 설정 파일 예시

사용법:
1. 이 파일을 'daily_dm_config.py'로 복사
2. 실제 값으로 변경
3. Git에는 절대 커밋하지 마세요! (.gitignore에 등록됨)
"""

# DM을 받을 사용자 목록
USERS = [
    {
        "name": "고선주",  # 표시용 이름
        "slack_id": "U123ABC456",  # Slack 사용자 ID (앱 사이드바에서 확인)
        "confluence_username": "seonju@woowahan.com",  # Confluence 이메일
        "confluence_token": "ATATT3xFfGF0...",  # Confluence API Token (앱 사이드바 참고)
        "confluence_space": "~seonju",  # 검색할 공간 키
        "confluence_parent_id": "",  # 상위 페이지 ID (선택, 비워두면 공간 전체)
    },
    # 다른 사용자 추가 시:
    # {
    #     "name": "김팀장",
    #     "slack_id": "U456DEF789",
    #     "confluence_username": "kimteam@woowahan.com",
    #     "confluence_token": "ATATT3xFfGF0...",
    #     "confluence_space": "TEAM-B",
    #     "confluence_parent_id": "123456789",
    # },
]

# DM 발송 시간 (한국 시간 기준, HH:MM 형식)
SEND_TIME_KST = "09:00"

# 검색 범위 (일) - 최근 N일 이내 작성된 회의록만 검색
SEARCH_DAYS = 60


