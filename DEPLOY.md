# 🚀 Streamlit Cloud 배포 가이드

## ✅ 준비사항

- [x] GitHub 계정
- [x] Streamlit Cloud 계정 (GitHub로 로그인)
- [x] 코드 완성

---

## 📝 Step 1: GitHub 저장소 생성

### 1-1. GitHub에서 Private Repository 생성

```
1. GitHub.com 접속
2. 우측 상단 "+" → "New repository"
3. 이름: meeting-automation (또는 원하는 이름)
4. ✅ Private 선택 (중요!)
5. Create repository
```

### 1-2. 코드 업로드

**터미널에서:**

```bash
cd /Users/seonju/Desktop/BaeminWorkspace/meeting-automation

# Git 초기화
git init

# GitHub 저장소 연결
git remote add origin https://github.com/your-username/meeting-automation.git

# 모든 파일 추가 (단, .env는 자동 제외됨!)
git add .

# 커밋
git commit -m "Initial commit: 회의록 자동화 시스템"

# Push
git push -u origin main
```

**⚠️ 중요:** `.env` 파일은 절대 업로드되지 않습니다! (`.gitignore`가 막아줌)

---

## 🔐 Step 2: API 키 안전하게 설정

### 2-1. .env 파일 내용 복사해두기

```bash
# 현재 .env 파일 내용을 메모장에 복사
cat .env
```

복사한 내용을 잠시 보관 (곧 사용)

---

## ☁️ Step 3: Streamlit Cloud 배포

### 3-1. Streamlit Cloud 접속

```
1. https://streamlit.io/cloud 접속
2. "Sign up" → GitHub로 로그인
3. "New app" 클릭
```

### 3-2. 앱 설정

```
Repository: your-username/meeting-automation (Private 표시 확인!)
Branch: main
Main file path: app.py
```

### 3-3. Advanced settings

```
Python version: 3.9
```

"Deploy!" 클릭

---

## 🔑 Step 4: Secrets 설정 (가장 중요!)

### 4-1. Secrets 페이지 접속

```
1. 배포 중인 앱에서 "Settings" 클릭
2. "Secrets" 클릭
3. "Edit Secrets" 클릭
```

### 4-2. API 키 입력

**아까 복사한 .env 내용을 다음 형식으로 입력:**

```toml
# OpenAI
OPENAI_API_KEY = "sk-proj-vog5kbsgdnqPvCLQ5FN..."

# Confluence
CONFLUENCE_URL = "https://woowahanbros.atlassian.net"
CONFLUENCE_USERNAME = "seonju@woowahan.com"
CONFLUENCE_API_TOKEN = "ATATT3xFfGF0Ujf9chuH9G..."
CONFLUENCE_SPACE_KEY = "~seonju"

# Slack
SLACK_BOT_TOKEN = "xoxb-9745123589747-9736105206551..."
SLACK_CHANNEL_ID = "#새-채널"
```

**주의:**
- 따옴표 필수!
- `=` 양쪽에 공백 필수!

"Save" 클릭

---

## ✨ Step 5: 배포 완료!

### 앱 URL 확인

```
https://your-username-meeting-automation.streamlit.app
```

이제 이 URL을 팀원들과 공유하면 됩니다! 🎉

---

## 🔒 보안 확인 체크리스트

- [x] GitHub 저장소: Private
- [x] `.env` 파일: 업로드 안됨 (`.gitignore`)
- [x] API 키: Streamlit Secrets에 안전하게 저장
- [x] 코드에 하드코딩된 키 없음

---

## 👥 팀원 접근 권한 관리

### 코드 접근 (GitHub)
```
GitHub → Settings → Collaborators
→ 팀원 이메일 초대
```

### 앱 접근
```
누구나 URL만 알면 사용 가능
(추가 인증 필요하면 Streamlit 유료 플랜 or 자체 로그인 구현)
```

---

## 🛠️ 배포 후 업데이트

### 코드 수정 후:

```bash
git add .
git commit -m "기능 추가: xxx"
git push
```

**자동으로 재배포됩니다!** (1-2분 소요)

---

## ⚠️ 문제 해결

### "Secrets not found" 에러
```
→ Streamlit Cloud Secrets 다시 확인
→ 오타 확인
→ 따옴표 확인
```

### "Module not found" 에러
```
→ requirements.txt 확인
→ 모든 라이브러리 포함되어 있는지 확인
```

### 배포 실패
```
→ Streamlit Cloud Logs 확인
→ GitHub 저장소 권한 확인
```

---

## 📞 도움이 필요하면?

Streamlit Community: https://discuss.streamlit.io/

---

Happy Deploying! 🚀

