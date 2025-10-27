"""
일일 액션아이템 DM 발송 스크립트

매일 실행되어 미완료 액션아이템을 Slack DM으로 전송
"""

import requests
import base64
from datetime import datetime, timedelta
import re
from typing import List, Dict
import daily_dm_config as dm_config


def search_meeting_notes(username: str, token: str, space_key: str, parent_id: str = None) -> List[Dict]:
    """Confluence에서 회의록 검색"""
    
    auth_string = f"{username}:{token}"
    auth_b64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # CQL 쿼리 생성
    date_limit = (datetime.now() - timedelta(days=dm_config.SEARCH_DAYS)).strftime('%Y-%m-%d')
    
    cql = f'space="{space_key}" AND title~"회의록" AND created>"{date_limit}"'
    
    if parent_id:
        cql += f' AND ancestor="{parent_id}"'
    
    url = f"https://woowahanbros.atlassian.net/wiki/rest/api/content/search"
    params = {
        "cql": cql,
        "limit": 100,
        "expand": "body.storage,version,history"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        results = response.json()
        return results.get('results', [])
    except Exception as e:
        print(f"❌ 회의록 검색 실패: {e}")
        return []


def parse_action_items(page_content: str, page_url: str, page_title: str) -> List[Dict]:
    """회의록에서 액션아이템 파싱"""
    
    action_items = []
    
    # <ac:task> 태그에서 액션아이템 추출
    task_pattern = r'<ac:task><ac:task-id>(.*?)</ac:task-id><ac:task-status>(.*?)</ac:task-status><ac:task-body><span[^>]*>(.*?)</span></ac:task-body></ac:task>'
    
    tasks = re.findall(task_pattern, page_content, re.DOTALL)
    
    for task_id, status, content in tasks:
        # 미완료 항목만
        if status.strip() != 'incomplete':
            continue
        
        # 담당자 추출 (@이름)
        assignee_match = re.search(r'@([^\s—]+)', content)
        assignee = assignee_match.group(1) if assignee_match else 'TBD'
        
        # 마감일 추출
        due_date = None
        due_match = re.search(r'<time datetime="([^"]+)"', content)
        if due_match:
            due_date = due_match.group(1)
        else:
            # Due: YYYY-MM-DD 형식도 확인
            due_text_match = re.search(r'Due:\s*(\d{4}-\d{2}-\d{2})', content)
            if due_text_match:
                due_date = due_text_match.group(1)
        
        # 작업 내용 정리 (HTML 태그 제거)
        task_text = re.sub(r'<[^>]+>', '', content)
        task_text = re.sub(r'—\s*@.*?—.*', '', task_text).strip()
        
        if task_text and due_date and due_date != 'TBD':
            action_items.append({
                'task': task_text,
                'assignee': assignee,
                'due_date': due_date,
                'page_url': page_url,
                'page_title': page_title
            })
    
    return action_items


def classify_by_date(action_items: List[Dict]) -> Dict[str, List[Dict]]:
    """액션아이템을 날짜별로 분류"""
    
    today = datetime.now().date()
    
    classified = {
        'overdue': [],  # 기한 지남
        'd_day': [],    # 오늘 마감
        'd_3': []       # 3일 남음
    }
    
    for item in action_items:
        try:
            due_date = datetime.strptime(item['due_date'], '%Y-%m-%d').date()
            days_left = (due_date - today).days
            
            if days_left < 0:
                classified['overdue'].append(item)
            elif days_left == 0:
                classified['d_day'].append(item)
            elif days_left == 3:
                classified['d_3'].append(item)
        except:
            continue
    
    return classified


def format_slack_dm(classified: Dict[str, List[Dict]], user_name: str) -> str:
    """Slack DM 포맷 생성"""
    
    total = sum(len(items) for items in classified.values())
    
    if total == 0:
        return None  # 보낼 항목 없음
    
    message = f"🔔 *{user_name}님의 액션아이템 리마인더*\n\n"
    message += f"📊 총 {total}개의 미완료 액션아이템이 있습니다.\n\n"
    
    # Overdue
    if classified['overdue']:
        message += f"🚨 *기한 지남* ({len(classified['overdue'])}건)\n"
        for item in classified['overdue'][:5]:  # 최대 5개
            message += f"• {item['task'][:50]}{'...' if len(item['task']) > 50 else ''}\n"
            message += f"  담당: @{item['assignee']} | 마감: {item['due_date']}\n"
            message += f"  📄 <{item['page_url']}|{item['page_title'][:30]}>\n\n"
    
    # D-Day
    if classified['d_day']:
        message += f"⏰ *오늘 마감* ({len(classified['d_day'])}건)\n"
        for item in classified['d_day'][:5]:
            message += f"• {item['task'][:50]}{'...' if len(item['task']) > 50 else ''}\n"
            message += f"  담당: @{item['assignee']} | 마감: {item['due_date']}\n"
            message += f"  📄 <{item['page_url']}|{item['page_title'][:30]}>\n\n"
    
    # D-3
    if classified['d_3']:
        message += f"📅 *3일 후 마감* ({len(classified['d_3'])}건)\n"
        for item in classified['d_3'][:5]:
            message += f"• {item['task'][:50]}{'...' if len(item['task']) > 50 else ''}\n"
            message += f"  담당: @{item['assignee']} | 마감: {item['due_date']}\n"
            message += f"  📄 <{item['page_url']}|{item['page_title'][:30]}>\n\n"
    
    message += "---\n💡 회의록에서 체크박스를 클릭하여 완료 처리하세요!"
    
    return message


def send_slack_dm(slack_id: str, message: str, bot_token: str) -> bool:
    """Slack DM 전송"""
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "channel": slack_id,
        "text": message,
        "mrkdwn": True
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        result = response.json()
        return result.get('ok', False)
    except Exception as e:
        print(f"❌ Slack DM 전송 실패: {e}")
        return False


def main():
    """메인 실행 함수"""
    
    print(f"🚀 일일 액션아이템 DM 발송 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Slack Bot Token (환경변수 또는 config에서)
    import os
    from dotenv import load_dotenv
    load_dotenv()
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    
    if not bot_token:
        print("❌ SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        return
    
    for user in dm_config.USERS:
        print(f"\n📤 처리 중: {user['name']}")
        
        # 1. 회의록 검색
        pages = search_meeting_notes(
            user['confluence_username'],
            user['confluence_token'],
            user['confluence_space'],
            user.get('confluence_parent_id')
        )
        
        print(f"  📄 {len(pages)}개 회의록 발견")
        
        # 2. 액션아이템 수집
        all_action_items = []
        for page in pages:
            page_url = f"https://woowahanbros.atlassian.net/wiki{page['_links']['webui']}"
            page_title = page['title']
            content = page['body']['storage']['value']
            
            items = parse_action_items(content, page_url, page_title)
            all_action_items.extend(items)
        
        print(f"  ✅ {len(all_action_items)}개 액션아이템 발견")
        
        # 3. 날짜별 분류
        classified = classify_by_date(all_action_items)
        
        # 4. Slack DM 생성 및 전송
        message = format_slack_dm(classified, user['name'])
        
        if message:
            success = send_slack_dm(user['slack_id'], message, bot_token)
            if success:
                print(f"  ✅ DM 전송 완료")
            else:
                print(f"  ❌ DM 전송 실패")
        else:
            print(f"  ℹ️  보낼 액션아이템 없음")
    
    print(f"\n✅ 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()


