# 🤖 회의록 자동화 시스템

AI가 회의록을 자동으로 구조화하고 Confluence와 Slack에 공유하는 시스템입니다.

## 🚀 실행 방법

### 방법 1: 스크립트 더블클릭 (가장 쉬움!)

1. Finder에서 `meeting-automation` 폴더 열기
2. `start.sh` 파일 찾기
3. **더블클릭!** 🖱️

> **처음 실행 시**: "신뢰할 수 없는 개발자" 경고가 나오면
> → 우클릭 → "열기" → "열기" 버튼 클릭

### 방법 2: 터미널에서 실행

```bash
cd /Users/seonju/Desktop/BaeminWorkspace/meeting-automation
./start.sh
```

### 방법 3: 수동 실행

```bash
cd /Users/seonju/Desktop/BaeminWorkspace/meeting-automation
python3 -m streamlit run app.py
```

---

## 🌐 접속 주소

시작하면 자동으로 브라우저가 열립니다.
직접 접속: **http://localhost:8501**

---

## ⏹️ 종료 방법

터미널 창에서 `Ctrl + C` (또는 Command + C)

---

## ✨ 주요 기능

- ✅ 회의록 자동 구조화
- ✅ 액션아이템 AI 자동 추출
- ✅ Confluence 자동 업로드 (캘린더 통합)
- ✅ Slack 자동 공유
- ✅ 체크박스 실시간 편집
- ✅ **개인 설정 지원** (각자 계정으로 작성)

---

## 🔧 첫 사용 설정

### 1. Confluence API Token 발급

1. [Confluence 설정 페이지](https://id.atlassian.com/manage-profile/security/api-tokens) 접속
2. "Create API token" 클릭
3. 이름 입력 (예: 회의록봇)
4. Token 복사
5. 앱 사이드바에 붙여넣기

### 2. 앱에서 설정

1. 웹 앱 실행 후 **사이드바** 열기
2. 다음 정보 입력:
   - Confluence 이메일
   - Confluence API Token
   - 기본 공간 키 (예: `TEAM-A`, `~username`)
   - 기본 채널 (예: `#team-a`)
3. "💾 설정 저장" 클릭

### 3. Private 채널 사용 시

Slack Private 채널에 봇 초대:
```
/invite @회의록봇
```

> **중요:** 각 팀장이 자기 Token을 사용하므로 **회의록 작성자는 실제 사용자 이름**으로 표시됩니다!

---

## 🛠️ 문제 해결

### "python3 command not found"
```bash
python --version  # Python 3.x 확인
```

### "streamlit not found"
```bash
pip3 install streamlit
```

### 포트 충돌 (8501 이미 사용 중)
```bash
lsof -ti:8501 | xargs kill -9
```

---

## 🌐 다른 사람들과 공유하기

**배포 가이드:** [DEPLOY.md](DEPLOY.md) 참고

### 간단 요약:
1. GitHub Private 저장소에 코드 업로드
2. Streamlit Cloud에 배포
3. API 키는 Secrets로 안전하게 관리

**결과:** `https://your-app.streamlit.app` 같은 URL로 접근 가능!

---

## 🔔 일일 액션아이템 DM (신규!)

매일 오전 9시, 미완료 액션아이템을 Slack DM으로 자동 전송합니다.

### 설정 방법

**1단계: Slack ID 확인**

앱 사이드바에서 본인의 Slack ID를 확인하고 복사

**2단계: 관리자에게 전달**

복사한 Slack ID와 Confluence 설정을 관리자에게 전달:
- Slack ID (예: U123ABC456)
- Confluence 이메일
- Confluence API Token
- 검색할 공간 키
- (선택) 상위 페이지 ID

**3단계: 관리자 설정**

관리자가 `daily_dm_config.py` 파일에 사용자 정보 추가:

```python
USERS = [
    {
        "name": "고선주",
        "slack_id": "U123ABC456",
        "confluence_username": "seonju@woowahan.com",
        "confluence_token": "ATATT...",
        "confluence_space": "~seonju",
        "confluence_parent_id": "123456789",  # 선택
    },
]
```

**4단계: 스케줄러 실행**

```bash
./start_scheduler.sh
```

> **💡 Tip:** 스케줄러는 서버나 항상 켜진 컴퓨터에서 실행하세요!

### DM 내용

- 🚨 **기한 지남**: 오늘 날짜 기준 지난 항목
- ⏰ **오늘 마감**: D-Day 항목
- 📅 **3일 후 마감**: D-3 항목

각 항목에는 원본 회의록 링크 포함!

---

## 📝 다음 단계 (8~10번 스펙)

- [ ] Jira/Wiki 추천 항목
- [x] **일일 액션아이템 DM** ✅
- [ ] Slack 대화 요약
- [ ] 리마인더 기능

---

Made with ❤️ by AI
