#!/usr/bin/env python3
"""
회의록 자동화 웹 UI (Streamlit)
"""

import streamlit as st
import base64
from datetime import datetime
import requests
from openai import OpenAI
import config
from utils import markdown_to_confluence_storage, extract_action_items_count
import json

# 페이지 설정
st.set_page_config(
    page_title="회의록 자동화",
    page_icon="📝",
    layout="wide"
)

# OpenAI 클라이언트
@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=config.OPENAI_API_KEY)

client = get_openai_client()


# 설정 저장/로드 함수 (로컬 JSON 파일 사용)
import os
from pathlib import Path

CONFIG_FILE = Path.home() / '.meeting_automation_config.json'

def save_user_config(config_data: dict):
    """사용자 설정을 로컬 JSON 파일에 저장"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"설정 저장 실패: {e}")
        return False


def load_user_config() -> dict:
    """로컬 JSON 파일에서 사용자 설정 로드"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"설정 파일 로드 중 오류: {e}")
    
    # 기본값 반환
    return {
        'confluence_username': '',
        'confluence_token': '',
        'confluence_space': '',
        'confluence_parent_id': '',
        'slack_channel': ''
    }


def generate_title(meeting_notes: str, meeting_date: str = "") -> str:
    """회의 내용에서 제목 자동 생성 (날짜 제외)"""
    import re
    from datetime import datetime
    
    # 회의 내용이 충분하지 않으면 날짜 + '회의록' 반환
    if len(meeting_notes.strip()) < 50:  # 50글자 미만이면 부족한 것으로 판단
        if meeting_date:
            return f"{meeting_date} 회의록"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            return f"{today} 회의록"
    
    # 의미있는 단어 개수 체크 (중복 단어나 의미없는 단어 제외)
    words = meeting_notes.split()
    meaningful_words = [word for word in words if len(word) > 2 and word.lower() not in ['test', '테스트', '안녕', 'hello', 'hi', '안녕하세요']]
    unique_meaningful_words = list(set(meaningful_words))
    
    # 의미있는 단어가 3개 미만이면 부족한 것으로 판단
    if len(unique_meaningful_words) < 3:
        if meeting_date:
            return f"{meeting_date} 회의록"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            return f"{today} 회의록"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT_TITLE},
                {"role": "user", "content": f"다음 회의 내용의 제목을 생성해주세요:\n\n{meeting_notes[:500]}"}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        title = response.choices[0].message.content.strip()
        
        # 혹시 날짜가 포함되어 있으면 제거
        title = re.sub(r'^\d{4}[-년./]\d{1,2}[-월./]\d{1,2}[일]?\s*', '', title)
        title = re.sub(r'^\d{1,2}[-월/]\d{1,2}[일]?\s*', '', title)
        
        # 제목이 너무 짧거나 이상하면 날짜 + '회의록' 반환
        if len(title.strip()) < 5 or title.strip() in ['제목', '회의록', '회의', '']:
            if meeting_date:
                return f"{meeting_date} 회의록"
            else:
                today = datetime.now().strftime("%Y-%m-%d")
                return f"{today} 회의록"
        
        return title.strip()
        
    except Exception as e:
        # AI 생성 실패 시 날짜 + '회의록' 반환
        if meeting_date:
            return f"{meeting_date} 회의록"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            return f"{today} 회의록"


def structure_meeting_notes(meeting_title: str, attendees: str, meeting_date: str, meeting_notes: str, action_items_text: str = "") -> str:
    """회의록을 구조화"""
    
    # 참석자와 날짜 정보를 회의 내용에 추가
    full_content = f"""회의명: {meeting_title}
일시: {meeting_date}
참석자: {attendees}

회의 내용:
{meeting_notes}
{action_items_text}"""
    
    response = client.chat.completions.create(
        model="gpt-4o",  # GPT-4o로 업그레이드!
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT_STRUCTURE},
            {"role": "user", "content": f"다음 회의 내용을 위 형식으로 정리해주세요:\n\n{full_content}"}
        ],
        temperature=0.3,
        max_tokens=3000
    )
    return response.choices[0].message.content


def upload_to_confluence(title: str, content: str, meeting_date: str, username: str, token: str, space_key: str, parent_id: str = None) -> dict:
    """Confluence에 페이지 생성"""
    auth_string = f"{username}:{token}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    # 제목 형식: YYYY-MM-DD 회의명 – 회의록
    page_title = f"{meeting_date} {title} – 회의록"
    
    # Confluence Storage Format으로 변환
    html_content = markdown_to_confluence_storage(content)
    
    url = f"{config.CONFLUENCE_URL}/wiki/rest/api/content"
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "type": "page",
        "title": page_title,
        "space": {
            "key": space_key
        },
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }
    
    # 상위 페이지 ID가 있으면 추가
    if parent_id and parent_id.strip():
        payload["ancestors"] = [{"id": parent_id.strip()}]
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        result = response.json()
        page_url = f"{config.CONFLUENCE_URL}/wiki{result['_links']['webui']}"
        return {"success": True, "url": page_url, "data": result}
    else:
        return {"success": False, "error": response.text}


def create_slack_summary(structured_content: str) -> str:
    """Slack용 요약 생성"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT_SUMMARY},
            {"role": "user", "content": f"다음 회의록을 요약해주세요:\n\n{structured_content}"}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    return response.choices[0].message.content


def extract_action_items_from_notes(meeting_notes: str) -> list:
    """회의 내용에서 액션아이템 자동 추출"""
    prompt = """다음 회의 내용에서 **모든 실행 가능한 작업(액션아이템)**을 적극적으로 추출해주세요.

**액션아이템 정의:**
다음 표현이 포함된 모든 작업을 추출하세요:
- "~해야 한다", "~필요하다", "~되어야 한다"
- "~수정", "~작업", "~검토", "~확인", "~작성", "~정리"
- "~반영", "~포함", "~구성", "~통합"
- 명시적인 TODO나 액션아이템
- 데드라인이나 목표가 언급된 작업

**출력 형식:** JSON 배열
[
  {"task": "구체적인 작업 내용", "assignee": "담당자명 또는 TBD", "due": "YYYY-MM-DD 또는 TBD"}
]

**중요 규칙:**
1. 담당자가 없으면 무조건 "TBD"
2. 마감일이 없으면 무조건 "TBD"
3. 의미 없는 작업은 제외하되, **애매하면 포함**
4. 작업 내용은 구체적이고 명확하게 작성
5. JSON만 반환 (다른 설명 없이)

**예시:**
입력: "이 시트에서 수정이 필요할 것 같다. 5월 실적을 이걸로 보고되면 좋겠음."
출력: [
  {"task": "시트 수정 작업", "assignee": "TBD", "due": "TBD"},
  {"task": "5월 실적 보고서 작성 및 제출", "assignee": "TBD", "due": "TBD"}
]

회의 내용:
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """당신은 회의록에서 액션아이템을 적극적으로 추출하는 전문가입니다.

핵심 원칙:
1. **많이 추출하는 것이 적게 추출하는 것보다 낫습니다**
2. 암묵적인 작업도 추출하세요 (예: "수정이 필요하다" → 액션아이템)
3. 담당자/날짜가 없어도 추출하세요 (TBD로 설정)
4. JSON 배열만 반환하세요

반드시 JSON만 출력하고, 다른 텍스트는 절대 포함하지 마세요."""},
            {"role": "user", "content": prompt + meeting_notes}
        ],
        temperature=0.4,
        max_tokens=2000
    )
    
    import json
    import re
    
    try:
        content = response.choices[0].message.content.strip()
        
        # JSON만 추출 (코드블록이나 다른 텍스트 제거)
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        result = json.loads(content)
        
        if isinstance(result, list):
            # TBD 값 정규화
            for item in result:
                if not item.get('assignee') or item['assignee'].strip() == '':
                    item['assignee'] = 'TBD'
                if not item.get('due') or item['due'].strip() == '':
                    item['due'] = 'TBD'
            return result
        return []
    except Exception as e:
        print(f"액션아이템 추출 실패: {e}")
        print(f"GPT 응답: {response.choices[0].message.content}")
        return []


def validate_confluence_settings(username: str, token: str, space_key: str) -> dict:
    """Confluence 설정 유효성 검증"""
    try:
        auth_string = f"{username}:{token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        }
        
        # 공간 정보 조회로 접근 가능 여부 확인
        url = f"{config.CONFLUENCE_URL}/wiki/rest/api/space/{space_key}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            space_data = response.json()
            space_name = space_data.get('name', space_key)
            return {"success": True, "space_name": space_name}
        elif response.status_code == 401:
            return {"success": False, "error": "인증 실패: 이메일 또는 API Token이 잘못되었습니다"}
        elif response.status_code == 404:
            return {"success": False, "error": f"공간 '{space_key}'를 찾을 수 없습니다. 공간 키를 확인해주세요"}
        elif response.status_code == 403:
            return {"success": False, "error": f"공간 '{space_key}'에 접근 권한이 없습니다"}
        else:
            return {"success": False, "error": f"알 수 없는 오류 (코드: {response.status_code})"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "연결 시간 초과: Confluence 서버 응답이 없습니다"}
    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}


def validate_slack_channel(channel: str) -> dict:
    """Slack 채널 유효성 검증"""
    try:
        # # 제거 (API는 #없이 사용)
        channel_clean = channel.lstrip('#')
        
        url = "https://slack.com/api/conversations.info"
        headers = {
            "Authorization": f"Bearer {config.SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # 채널 ID로 조회 (채널명 입력 시 검색)
        # 먼저 채널 목록에서 이름으로 찾기
        list_url = "https://slack.com/api/conversations.list"
        list_params = {"types": "public_channel,private_channel", "limit": 1000}
        list_response = requests.get(list_url, headers=headers, params=list_params, timeout=10)
        list_result = list_response.json()
        
        if not list_result.get("ok"):
            error = list_result.get('error', 'unknown_error')
            if error == "invalid_auth":
                return {"success": False, "error": "Slack Bot Token이 유효하지 않습니다"}
            return {"success": False, "error": f"Slack API 오류: {error}"}
        
        # 채널 이름으로 검색
        channels = list_result.get('channels', [])
        matching_channel = None
        
        for ch in channels:
            if ch.get('name') == channel_clean or ch.get('id') == channel_clean:
                matching_channel = ch
                break
        
        if matching_channel:
            channel_name = matching_channel.get('name')
            is_member = matching_channel.get('is_member', False)
            
            if not is_member:
                return {
                    "success": False, 
                    "error": f"채널 '#{channel_name}'을 찾았지만 Bot이 멤버가 아닙니다.\n채널에서 `/invite @회의록봇` 명령을 실행해주세요"
                }
            
            return {"success": True, "channel_name": channel_name}
        else:
            return {"success": False, "error": f"채널 '{channel}'을 찾을 수 없습니다. 채널명을 확인해주세요"}
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "연결 시간 초과: Slack 서버 응답이 없습니다"}
    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}


def send_to_slack(summary: str, channel: str, confluence_url: str = None) -> dict:
    """Slack 채널에 메시지 전송"""
    message = summary
    if confluence_url:
        message += f"\n\n---\n📄 *전체 회의록:* {confluence_url}"
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {config.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "channel": channel.lstrip('#'),  # # 제거
        "text": message
    }
    
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    if result.get("ok"):
        return {"success": True}
    else:
        return {"success": False, "error": result.get('error')}


# Session State 초기화
if 'action_items' not in st.session_state:
    st.session_state.action_items = []
if 'auto_extracted' not in st.session_state:
    st.session_state.auto_extracted = False

# 사용자 설정 초기화 - 로컬 파일에서 자동 로드
if 'config_loaded' not in st.session_state:
    saved_config = load_user_config()
    st.session_state.user_confluence_username = saved_config.get('confluence_username', '')
    st.session_state.user_confluence_token = saved_config.get('confluence_token', '')
    st.session_state.user_confluence_space = saved_config.get('confluence_space', '')
    st.session_state.user_confluence_parent_id = saved_config.get('confluence_parent_id', '')
    st.session_state.user_slack_channel = saved_config.get('slack_channel', '')
    st.session_state.config_loaded = True

# Streamlit UI
st.title("📝 회의 후속조치 자동화 AI 비서")
st.markdown("AI가 회의록을 작성/발행/공유하며, 이후 follow-up까지 책임집니다.")
st.markdown("---")

# 제목 입력 (폼 밖에서 즉시 반응)
st.subheader("1️⃣ 회의 기본 정보")

col1, col2 = st.columns([2, 1])

with col1:
    auto_title = st.checkbox("✨ 제목 자동 생성 (AI가 회의 내용에서 자동으로 생성)", value=False)
    
    if not auto_title:
        meeting_title_input = st.text_input(
            "회의 제목 *",
            placeholder="예: 멤버십 시스템 개선 회의",
            key="title_input"
        )
    else:
        meeting_title_input = None
        st.success("🤖 **AI가 회의 내용을 분석하여 자동으로 제목을 생성합니다**")
        st.caption("(제목 입력 불필요)")

with col2:
    meeting_date_input = st.date_input(
        "회의 날짜 *",
        value=datetime.now(),
        key="date_input"
    ).strftime('%Y-%m-%d')

attendees_input = st.text_input(
    "참석자 *",
    placeholder="예: 김철수, 이영희, 박민수",
    help="쉼표(,)로 구분해주세요",
    key="attendees_input"
)

# 입력 폼 (회의 내용만)
with st.form("meeting_form"):
    
    st.subheader("2️⃣ 회의 내용")
    
    meeting_notes = st.text_area(
        "회의 내용 *",
        height=250,
        placeholder="""## 논의 내용
- 주요 안건 1
- 주요 안건 2

## 결정 사항
- 결정 1
- 결정 2""",
        help="자유롭게 작성하세요. AI가 자동으로 구조화합니다."
    )
    
    submitted = st.form_submit_button("다음 단계: 액션아이템 설정", use_container_width=True, type="primary")

# 폼 제출 처리
if submitted:
    # 필수 입력 검증
    missing_fields = []
    if not auto_title and not meeting_title_input:
        missing_fields.append("회의 제목")
    if not attendees_input:
        missing_fields.append("참석자")
    if not meeting_notes:
        missing_fields.append("회의 내용")
    
    if missing_fields:
        st.error(f"❌ 다음 필수 항목을 입력해주세요: {', '.join(missing_fields)}")
    else:
        # 세션 스테이트에 저장 (입력된 날짜 그대로 사용)
        st.session_state.meeting_title = meeting_title_input if not auto_title else None
        st.session_state.auto_title = auto_title
        st.session_state.meeting_date = meeting_date_input
        st.session_state.attendees = attendees_input
        st.session_state.meeting_notes = meeting_notes
        st.session_state.form_submitted = True
        
        # 액션아이템 자동 추출 (첫 제출 시)
        if not st.session_state.auto_extracted:
            with st.spinner("🤖 AI가 액션아이템을 자동으로 추출하는 중..."):
                extracted = extract_action_items_from_notes(meeting_notes)
                st.session_state.action_items = extracted
                st.session_state.auto_extracted = True
            st.rerun()

# 액션아이템 설정 UI (폼 제출 후)
if st.session_state.get('form_submitted', False):
    st.markdown("---")
    st.subheader("3️⃣ 액션아이템 설정")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"💡 AI가 **{len(st.session_state.action_items)}개**의 액션아이템을 자동으로 추출했습니다. 수정하거나 추가하세요.")
    with col2:
        if st.button("➕ 액션아이템 추가", use_container_width=True):
            st.session_state.action_items.append({"task": "", "assignee": "TBD", "due": "TBD"})
            st.rerun()
    
    # 액션아이템 편집
    if len(st.session_state.action_items) == 0:
        st.warning("액션아이템이 없습니다. 필요하면 추가 버튼을 눌러주세요.")
    else:
        for i, item in enumerate(st.session_state.action_items):
            with st.expander(f"📋 액션아이템 {i+1}", expanded=True):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
                
                with col1:
                    new_task = st.text_input("작업 내용", value=item.get('task', ''), key=f"edit_task_{i}", placeholder="작업 내용 입력")
                with col2:
                    new_assignee = st.text_input("담당자", value=item.get('assignee', 'TBD'), key=f"edit_assignee_{i}", placeholder="담당자")
                with col3:
                    # Due date 처리
                    due_value = item.get('due', 'TBD')
                    if due_value != 'TBD':
                        try:
                            from datetime import datetime as dt
                            due_date_obj = dt.strptime(due_value, '%Y-%m-%d').date()
                        except:
                            due_date_obj = datetime.now().date()
                    else:
                        due_date_obj = datetime.now().date()
                    
                    new_due = st.date_input("마감일", value=due_date_obj, key=f"edit_due_{i}")
                with col4:
                    if st.button("🗑️", key=f"delete_{i}", help="삭제"):
                        st.session_state.action_items.pop(i)
                        st.rerun()
                
                # 업데이트
                st.session_state.action_items[i] = {
                    "task": new_task,
                    "assignee": new_assignee,
                    "due": new_due.strftime('%Y-%m-%d')
                }
    
    st.markdown("---")
    
    # 최종 생성 버튼과 처리
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🚀 회의록 wiki문서 생성 및 Slack전송", use_container_width=True, type="primary")
    
    # 버튼 클릭 시 처리 (버튼 바로 아래에 표시)
    if generate_button:
        meeting_title = st.session_state.meeting_title
        auto_title = st.session_state.auto_title
        meeting_date = st.session_state.meeting_date
        attendees = st.session_state.attendees
        meeting_notes = st.session_state.meeting_notes
        action_items = st.session_state.action_items
        
        # 설정 검증
        if not st.session_state.user_confluence_token or not st.session_state.user_confluence_space:
            st.error("❌ Confluence 설정이 필요합니다! 사이드바에서 설정해주세요.")
            st.stop()
        
        if not st.session_state.user_slack_channel:
            st.error("❌ Slack 채널 설정이 필요합니다! 사이드바에서 설정해주세요.")
            st.stop()
        
        try:
            # 프로그레스 바
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 0. 제목 자동 생성 (필요시)
            if auto_title:
                status_text.text("🤖 회의 제목 생성 중...")
                progress_bar.progress(10)
                meeting_title = generate_title(meeting_notes, meeting_date)
                st.info(f"✨ 생성된 제목: **{meeting_title}**")
                progress_bar.progress(20)
            
            # 액션아이템을 명확하게 구조화
            action_items_text = ""
            if action_items:
                action_items_text = "\n\n## 사용자 지정 액션아이템 (반드시 포함):\n"
                for i, item in enumerate(action_items, 1):
                    # 날짜 형식 변환: 2025/10/27 → 2025-10-27
                    due_date = item['due'].replace('/', '-')
                    action_items_text += f"{i}. 작업: {item['task']} | 담당자: {item['assignee']} | 마감일: {due_date}\n"
            
            # 1. 구조화
            status_text.text("📝 회의록 구조화 중...")
            progress_bar.progress(40)
            structured_content = structure_meeting_notes(meeting_title, attendees, meeting_date, meeting_notes, action_items_text)
            
            # 🔍 디버그: GPT 출력 확인
            st.write("### 🔍 디버그: GPT가 생성한 원본")
            st.code(structured_content, language="markdown")
            
            # 체크박스 패턴 확인
            import re
            checkbox_incomplete = re.findall(r'^- \[ \].+$', structured_content, re.MULTILINE)
            checkbox_complete = re.findall(r'^- \[[xX]\].+$', structured_content, re.MULTILINE)
            st.write(f"**발견된 체크박스:** 미완료 {len(checkbox_incomplete)}개, 완료 {len(checkbox_complete)}개")
            if checkbox_incomplete:
                st.write("**미완료 항목 예시:**", checkbox_incomplete[0] if checkbox_incomplete else "없음")
            if checkbox_complete:
                st.write("**완료 항목 예시:**", checkbox_complete[0] if checkbox_complete else "없음")
            
            # 🔍 디버그: 변환된 HTML 확인
            from utils import markdown_to_confluence_storage
            html_preview = markdown_to_confluence_storage(structured_content)
            st.write("### 🔍 디버그: Confluence Storage Format 변환 결과")
            st.code(html_preview, language="html")
            
            # 2. Confluence 업로드
            status_text.text("📤 Confluence 업로드 중...")
            progress_bar.progress(60)
            confluence_result = upload_to_confluence(
                meeting_title, 
                structured_content, 
                meeting_date,
                st.session_state.user_confluence_username,
                st.session_state.user_confluence_token,
                st.session_state.user_confluence_space,
                st.session_state.user_confluence_parent_id
            )
            
            # 3. Slack 요약
            status_text.text("📊 Slack 요약 생성 중...")
            progress_bar.progress(80)
            slack_summary = create_slack_summary(structured_content)
            
            # 4. Slack 전송
            status_text.text("💬 Slack 전송 중...")
            progress_bar.progress(90)
            confluence_url = confluence_result.get('url') if confluence_result.get('success') else None
            slack_result = send_to_slack(slack_summary, st.session_state.user_slack_channel, confluence_url)
            
            progress_bar.progress(100)
            status_text.empty()
            
            # 완료 팝업
            st.toast("🎉 회의록 작성 완료!")
            
            # 완료 메시지 - 크고 강조된 스타일
            st.markdown("""
            <div id="completion-marker" style="text-align: center; padding: 20px; background-color: #d4edda; border-radius: 10px; margin-bottom: 20px;">
                <h1 style="color: #155724; margin: 0;">✅ 완료!</h1>
                <p style="color: #155724; font-size: 18px; margin-top: 10px;">회의록이 성공적으로 생성되었습니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 스크롤 스크립트
            st.components.v1.html("""
            <script>
                window.parent.document.getElementById('completion-marker').scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            </script>
            """, height=0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📄 Confluence")
                if confluence_result.get('success'):
                    st.success("✅ 업로드 완료")
                    
                    # 회의록 보기 링크와 복사 기능
                    st.markdown(f"### [📖 회의록 보기]({confluence_result['url']})")
                    
                    # 클립보드 복사 기능
                    st.markdown(f"""
                    <div style="margin-top: 10px;">
                        <button onclick="navigator.clipboard.writeText('{confluence_result['url']}').then(() => alert('URL이 클립보드에 복사되었습니다!'))" 
                                style="background-color: #f0f2f6; border: 1px solid #ccc; border-radius: 4px; padding: 8px 12px; cursor: pointer; font-size: 14px;">
                            📋 URL 복사
                        </button>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ 업로드 실패")
                    with st.expander("에러 상세"):
                        st.code(confluence_result.get('error', 'Unknown error'))
            
            with col2:
                st.subheader("💬 Slack")
                if slack_result.get('success'):
                    st.success("✅ 메시지 전송 완료")
                    st.info(f"채널: {st.session_state.user_slack_channel}")
                else:
                    st.error("❌ 전송 실패")
                    with st.expander("에러 상세"):
                        st.code(slack_result.get('error', 'Unknown error'))
            
            # 구조화된 회의록 표시
            with st.expander("📋 구조화된 회의록 전체 보기", expanded=False):
                st.markdown(structured_content)
            
            # Slack 요약 표시
            with st.expander("💬 Slack 요약 미리보기", expanded=False):
                st.markdown(slack_summary)
            
            # 세션 리셋 버튼
            st.markdown("---")
            if st.button("🔄 새 회의록 작성", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ 에러 발생: {e}")
            with st.expander("상세 에러 정보"):
                import traceback
                st.code(traceback.format_exc())

# 사이드바 - 개인 설정
with st.sidebar:
    st.header("⚙️ 개인 설정")
    
    st.markdown("### 📍 Confluence")
    
    with st.expander("❓ Token 발급 방법", expanded=False):
        st.markdown("""
**Confluence API Token 발급:**

1. [Confluence 설정](https://id.atlassian.com/manage-profile/security/api-tokens) 접속
2. "Create API token" 클릭
3. 이름 입력 (예: 회의록봇)
4. Token 복사
5. 아래에 붙여넣기
        """)
    
    user_confluence_username = st.text_input(
        "Confluence 이메일",
        value=st.session_state.user_confluence_username,
        placeholder="your-email@woowahan.com",
        help="Confluence 로그인 이메일"
    )
    
    user_confluence_token = st.text_input(
        "Confluence API Token",
        value=st.session_state.user_confluence_token,
        type="password",
        placeholder="ATATTxxxxx...",
        help="위에서 발급받은 API Token"
    )
    
    user_confluence_space = st.text_input(
        "회의록을 생성할 위키 공간 key",
        value=st.session_state.user_confluence_space,
        placeholder="예: TEAM-A, ~username",
        help="회의록을 저장할 공간 (매번 변경 가능)"
    )
    
    user_confluence_parent_id = st.text_input(
        "회의록을 생성할 상위 페이지ID (선택)",
        value=st.session_state.user_confluence_parent_id,
        placeholder="예: 123456789 (비워두면 루트에 생성)",
        help="특정 페이지 하위에 회의록 생성"
    )
    
    with st.expander("❓ 상위 페이지 ID 확인 방법", expanded=False):
        st.markdown("""
**회의록을 특정 페이지 하위에 생성하려면:**

1. Confluence에서 상위 페이지 열기 (예: "2025년 회의록")
2. 페이지 우측 상단 **⋯ (더보기)** 클릭
3. **"페이지 정보"** 또는 **"Page Information"** 클릭
4. URL에서 숫자 복사:
   ```
   pageId=123456789
          ^^^^^^^^^
   ```
5. 위 입력란에 붙여넣기

**비워두면?** 공간 루트에 바로 생성됩니다.
        """)
    
    st.markdown("---")
    st.markdown("### 📍 Slack")
    
    with st.expander("먼저 Slack 봇을 채널에 초대해주세요", expanded=False):
        st.markdown("""
1. Slack 채널 열기
2. 다음 명령어 입력:
   ```
   /invite @회의록봇
   ```
3. Bot이 채널에 추가됨
4. 이제 메시지 전송 가능!
        """)
    
    user_slack_channel = st.text_input(
        "채널명",
        value=st.session_state.user_slack_channel,
        placeholder="예: #team-a, #프로젝트명",
        help="회의록을 공유할 채널 (매번 변경 가능)"
    )
    
    st.markdown("---")
    st.markdown("### 🔔 일일 액션아이템 DM (선택)")
    
    with st.expander("❓ 일일 DM이란?", expanded=False):
        st.markdown("""
**매일 오전 9시 자동 DM 발송:**

- 📊 미완료 액션아이템 자동 집계
- ⏰ D-3, D-Day, 기한지남 분류
- 📄 원본 회의록 링크 포함

**설정 방법:**
1. 나의 Slack ID 확인
2. 관리자에게 전달
3. 설정 완료!

**💡 프로토타입 한계:**
현재는 LocalStorage 기반이라 자동 DM을 위해
관리자가 서버 설정 파일에 직접 추가해야 합니다.
        """)
    
    with st.expander("🆔 나의 Slack ID 확인 방법", expanded=False):
        st.markdown("""
**Slack ID 확인:**

1. Slack 앱 열기
2. 나의 프로필 클릭
3. "⋯ 더보기" → "프로필 보기"
4. 주소창 URL 확인:
   ```
   https://app.slack.com/client/.../U123ABC456
                                     ^^^^^^^^^
                                     이 부분이 Slack ID
   ```
5. 'U'로 시작하는 ID 복사하여 관리자에게 전달

**또는:**
1. Slack에서 자신에게 DM 보내기
2. 주소창 확인
        """)
    
    st.markdown("---")
    
    if st.button("💾 설정 저장", use_container_width=True, type="primary"):
        # 입력 검증
        errors = []
        
        if not user_confluence_username:
            errors.append("Confluence 이메일을 입력해주세요")
        if not user_confluence_token:
            errors.append("Confluence API Token을 입력해주세요")
        if not user_confluence_space:
            errors.append("공간 키를 입력해주세요")
        if not user_slack_channel:
            errors.append("Slack 채널을 입력해주세요")
        
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # 유효성 검증 시작
            with st.spinner("🔍 설정을 검증하는 중..."):
                validation_success = True
                
                # 1. Confluence 검증
                st.info("📍 Confluence 공간 확인 중...")
                confluence_result = validate_confluence_settings(
                    user_confluence_username,
                    user_confluence_token,
                    user_confluence_space
                )
                
                if confluence_result['success']:
                    st.success(f"✅ Confluence: '{confluence_result['space_name']}' 공간에 접근 가능합니다")
                else:
                    st.error(f"❌ Confluence: {confluence_result['error']}")
                    validation_success = False
                
                # 2. Slack 검증
                st.info("💬 Slack 채널 확인 중...")
                slack_result = validate_slack_channel(user_slack_channel)
                
                if slack_result['success']:
                    st.success(f"✅ Slack: '#{slack_result['channel_name']}' 채널 사용 가능합니다")
                else:
                    st.error(f"❌ Slack: {slack_result['error']}")
                    validation_success = False
                
                # 3. 모두 성공 시 저장
                if validation_success:
                    st.session_state.user_confluence_username = user_confluence_username
                    st.session_state.user_confluence_token = user_confluence_token
                    st.session_state.user_confluence_space = user_confluence_space
                    st.session_state.user_confluence_parent_id = user_confluence_parent_id
                    st.session_state.user_slack_channel = user_slack_channel
                    
                    # 로컬 파일에 저장
                    config_data = {
                        'confluence_username': user_confluence_username,
                        'confluence_token': user_confluence_token,
                        'confluence_space': user_confluence_space,
                        'confluence_parent_id': user_confluence_parent_id,
                        'slack_channel': user_slack_channel
                    }
                    
                    if save_user_config(config_data):
                        st.success("🎉 설정이 성공적으로 저장되었습니다!")
                        st.info(f"💡 설정이 로컬 파일에 저장되었습니다: `{CONFIG_FILE}`\n브라우저를 새로고침해도 설정이 유지됩니다!")
                        st.balloons()
                    else:
                        st.warning("⚠️ 설정이 세션에는 저장되었지만, 파일 저장에 실패했습니다.")
                else:
                    st.warning("⚠️ 위 오류를 수정 후 다시 시도해주세요")
    
    # 설정 상태 표시
    st.markdown("---")
    with st.expander("📊 설정 상태"):
        if st.session_state.user_confluence_token and st.session_state.user_confluence_space:
            st.success("✅ Confluence 설정 완료")
        else:
            st.warning("⚠️ Confluence 설정 필요")
        
        if st.session_state.user_slack_channel:
            st.success("✅ Slack 설정 완료")
        else:
            st.warning("⚠️ Slack 설정 필요")
    
    st.markdown("---")
    
    st.header("💡 사용 가이드")
    
    with st.expander("🎯 워크플로우"):
        st.markdown("""
**1단계: 기본 정보 입력**
- 회의 제목/날짜/참석자/내용 입력
- "다음 단계" 버튼 클릭

**2단계: AI 자동 추출**
- AI가 회의 내용에서 액션아이템 자동 추출
- 추출된 항목 수정/삭제/추가 가능

**3단계: 회의록 생성**
- Confluence 업로드
- Slack 자동 공유
        """)
    
    with st.expander("✨ 주요 기능"):
        st.markdown("""
- **GPT-4o**: 최신 모델로 정확한 구조화
- **AI 자동화**: 회의록 작성 및 회의 내용에서 액션아이템 자동 감지, 회의록 발행 및 슬랙 요약 공유
- **실시간 편집**: 추출된 액션아이템 수정 가능
- **스케줄러**: 액션아이템의 상태를 매일 오전 슬랙으로 리마인드
        """)
    
    st.markdown("---")
    st.caption("Made with ❤️ by AI")
