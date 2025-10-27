"""유틸리티 함수들"""

import re
import uuid


def convert_due_date_to_time_tag(content: str) -> str:
    """Due: YYYY-MM-DD를 Confluence <time> 태그로 변환
    
    예: "작업 내용 — @김철수 — Due: 2025-10-27"
    → "작업 내용 — @김철수 — <time datetime=\"2025-10-27\"></time>"
    """
    # Due: YYYY-MM-DD 또는 Due: TBD 패턴 찾기
    pattern = r'Due:\s*(\d{4}-\d{2}-\d{2})'
    
    def replace_with_time_tag(match):
        date = match.group(1)
        return f'<time datetime="{date}"></time>'
    
    # Due: 날짜를 <time> 태그로 변환
    converted = re.sub(pattern, replace_with_time_tag, content)
    
    return converted


def markdown_to_confluence_storage(markdown_text: str) -> str:
    """마크다운을 Confluence Storage Format으로 변환"""
    
    lines = markdown_text.split('\n')
    result = []
    in_task_list = False
    task_buffer = []
    
    for line in lines:
        # 헤더 변환
        if line.startswith('# '):
            # task-list 닫기 (필요시)
            if in_task_list and task_buffer:
                result.append('<ac:task-list>')
                result.extend(task_buffer)
                result.append('</ac:task-list>')
                task_buffer = []
                in_task_list = False
            result.append(f"<h1>{line[2:].strip()}</h1>")
        elif line.startswith('## '):
            # task-list 닫기 (필요시)
            if in_task_list and task_buffer:
                result.append('<ac:task-list>')
                result.extend(task_buffer)
                result.append('</ac:task-list>')
                task_buffer = []
                in_task_list = False
            result.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith('### '):
            # task-list 닫기 (필요시)
            if in_task_list and task_buffer:
                result.append('<ac:task-list>')
                result.extend(task_buffer)
                result.append('</ac:task-list>')
                task_buffer = []
                in_task_list = False
            result.append(f"<h3>{line[4:].strip()}</h3>")
        
        # 체크박스 변환 (가장 중요!)
        elif line.strip().startswith('- [ ]'):
            # 미완료 체크박스
            content = line.strip()[5:].strip()  # "- [ ] " 제거
            # Due: YYYY-MM-DD를 <time> 태그로 변환
            content = convert_due_date_to_time_tag(content)
            task_id = str(uuid.uuid4())
            task_buffer.append(f'<ac:task><ac:task-id>{task_id}</ac:task-id><ac:task-status>incomplete</ac:task-status><ac:task-body><span class="placeholder-inline-tasks">{content}</span></ac:task-body></ac:task>')
            in_task_list = True
        
        elif line.strip().startswith('- [x]') or line.strip().startswith('- [X]'):
            # 완료된 체크박스
            content = line.strip()[5:].strip()  # "- [x] " 제거
            # Due: YYYY-MM-DD를 <time> 태그로 변환
            content = convert_due_date_to_time_tag(content)
            task_id = str(uuid.uuid4())
            task_buffer.append(f'<ac:task><ac:task-id>{task_id}</ac:task-id><ac:task-status>complete</ac:task-status><ac:task-body><span class="placeholder-inline-tasks">{content}</span></ac:task-body></ac:task>')
            in_task_list = True
        
        # 일반 리스트
        elif line.strip().startswith('- '):
            # task-list 닫기 (필요시)
            if in_task_list and task_buffer:
                result.append('<ac:task-list>')
                result.extend(task_buffer)
                result.append('</ac:task-list>')
                task_buffer = []
                in_task_list = False
            content = line.strip()[2:]
            result.append(f'<li>{content}</li>')
        
        # 일반 텍스트
        elif line.strip():
            # task-list 닫기 (필요시)
            if in_task_list and task_buffer:
                result.append('<ac:task-list>')
                result.extend(task_buffer)
                result.append('</ac:task-list>')
                task_buffer = []
                in_task_list = False
            result.append(f'<p>{line.strip()}</p>')
    
    # 마지막 task-list 닫기
    if in_task_list and task_buffer:
        result.append('<ac:task-list>')
        result.extend(task_buffer)
        result.append('</ac:task-list>')
    
    return '\n'.join(result)


def extract_action_items_count(structured_content: str) -> tuple:
    """액션아이템 개수 추출 (완료/미완료)"""
    incomplete = len(re.findall(r'- \[ \]', structured_content))
    complete = len(re.findall(r'- \[x\]', structured_content, re.IGNORECASE))
    return complete, incomplete

