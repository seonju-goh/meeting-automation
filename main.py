#!/usr/bin/env python3
"""
회의록 자동화 워크플로우
1. 회의록 입력
2. OpenAI로 구조화
3. Confluence 업로드
4. Slack 요약 전송
"""

import sys
import base64
from datetime import datetime
import requests
from openai import OpenAI
import config

# OpenAI 클라이언트
client = OpenAI(api_key=config.OPENAI_API_KEY)


def structure_meeting_notes(meeting_title: str, meeting_notes: str) -> str:
    """회의록을 구조화"""
    print("📝 회의록 구조화 중...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT_STRUCTURE},
            {"role": "user", "content": f"다음 회의 내용을 위 형식으로 정리해주세요:\n\n회의 제목: {meeting_title}\n\n회의 내용:\n{meeting_notes}"}
        ],
        temperature=0.3,
        max_tokens=2000
    )
    
    structured_content = response.choices[0].message.content
    print("✅ 구조화 완료")
    return structured_content


def upload_to_confluence(title: str, content: str) -> dict:
    """Confluence에 페이지 생성"""
    print("📤 Confluence 업로드 중...")
    
    # 인증 헤더
    auth_string = f"{config.CONFLUENCE_USERNAME}:{config.CONFLUENCE_API_TOKEN}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    # 타임스탬프 추가 (중복 방지)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    page_title = f"{title} – 회의록 ({timestamp})"
    
    # Confluence Storage Format으로 변환 (간단 버전)
    html_content = f"<h1>회의록</h1><pre>{content}</pre>"
    
    # API 요청
    url = f"{config.CONFLUENCE_URL}/wiki/rest/api/content"
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "type": "page",
        "title": page_title,
        "space": {
            "key": config.CONFLUENCE_SPACE_KEY
        },
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        result = response.json()
        page_url = f"{config.CONFLUENCE_URL}/wiki{result['_links']['webui']}"
        print(f"✅ Confluence 업로드 완료: {page_url}")
        return {"success": True, "url": page_url, "data": result}
    else:
        print(f"❌ Confluence 업로드 실패: {response.status_code}")
        print(f"   에러: {response.text}")
        return {"success": False, "error": response.text}


def create_slack_summary(structured_content: str) -> str:
    """Slack용 요약 생성"""
    print("📊 Slack 요약 생성 중...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT_SUMMARY},
            {"role": "user", "content": f"다음 회의록을 요약해주세요:\n\n{structured_content}"}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    summary = response.choices[0].message.content
    print("✅ 요약 완료")
    return summary


def send_to_slack(summary: str, confluence_url: str = None) -> dict:
    """Slack 채널에 메시지 전송"""
    print("💬 Slack 전송 중...")
    
    # 메시지 구성
    message = summary
    if confluence_url:
        message += f"\n\n---\n📄 *전체 회의록:* {confluence_url}"
    
    # Slack API 요청
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {config.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "channel": config.SLACK_CHANNEL_ID,
        "text": message
    }
    
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    if result.get("ok"):
        print("✅ Slack 전송 완료")
        return {"success": True}
    else:
        print(f"❌ Slack 전송 실패: {result.get('error')}")
        return {"success": False, "error": result.get('error')}


def main():
    """메인 워크플로우"""
    print("🚀 회의록 자동화 시작\n")
    
    # 테스트 데이터
    meeting_title = "[AI] 2025-01-15 온라인 회의 테스트"
    meeting_notes = """참석자: 김철수, 이영희, 박민수
일시: 2021-01-19 15시
장소: 온라인 회의

## 확인이 필요한 안건
- 신규 배달 서비스 첫 주문 쿠폰의 구체적인 스펙
- 배달팁 쿠폰의 요구사항
- 프로모션 쿠폰은 어떻게 활용되며, 추가개발이 필요한 지?

## 논의 내용

### 1. 신규 배달 서비스 첫 주문 쿠폰
- 어떤 기간의 주문 이력으로 판단할 것인가?
- 마케팅 입장에서는 최대한 많은 이용자가 쿠폰을 받을 수 있도록 발급 기준을 설정
- 주문 서비스팀과 협의 필요

결정: 구현방안별 일정을 마케팅팀에 공유
프로모션 시작일: ASAP 희망

### 2. 배달팁 할인쿠폰
- 내부에서 발급해 주는 것이 사용자 경험에도 좋을 것으로 판단
- 서비스별 구분 필요함
- 배달팁을 아예 무료로 만드는 쿠폰 필요

우려사항: 배달팁 쿠폰이 생기면 업주들이 일부러 배달팁을 올리는 역효과 가능성

## 액션아이템
1. (incomplete) 신규 배달 서비스 쿠폰 구현방식 관련 개발팀과 논의 - 김철수, 1/25까지
2. (complete) 배달팁 쿠폰 관련 계획 확인 후 마케팅팀 공유 - 이영희, 1/21
3. (incomplete) 배달팁 쿠폰 구현 진행 여부 및 구체적인 요건 논의 - 박민수, 1/28까지
"""
    
    try:
        # 1. 회의록 구조화
        structured_content = structure_meeting_notes(meeting_title, meeting_notes)
        print(f"\n{'='*60}\n구조화된 회의록:\n{'='*60}\n{structured_content}\n{'='*60}\n")
        
        # 2. Confluence 업로드
        confluence_result = upload_to_confluence(meeting_title, structured_content)
        
        # 3. Slack 요약 생성
        slack_summary = create_slack_summary(structured_content)
        
        # 4. Slack 전송
        confluence_url = confluence_result.get('url') if confluence_result.get('success') else None
        slack_result = send_to_slack(slack_summary, confluence_url)
        
        print("\n" + "="*60)
        print("🎉 전체 워크플로우 완료!")
        print("="*60)
        
        if confluence_result.get('success'):
            print(f"✅ Confluence: {confluence_result['url']}")
        if slack_result.get('success'):
            print("✅ Slack: 메시지 전송 완료")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


