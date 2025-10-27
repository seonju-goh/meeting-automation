# ✅ 배포 체크리스트

배포하기 전에 이 체크리스트를 확인하세요!

---

## 📋 배포 전 확인사항

### 보안 관련
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있음
- [ ] 코드에 API 키가 하드코딩되어 있지 않음
- [ ] `requirements.txt`가 최신 상태임

### 파일 확인
- [ ] `.gitignore` 파일 존재
- [ ] `requirements.txt` 파일 존재
- [ ] `README.md` 파일 존재
- [ ] `app.py` 정상 작동 확인

---

## 🚀 배포 과정

### 1. GitHub 저장소
- [ ] Private Repository 생성
- [ ] 코드 Push 완료
- [ ] `.env` 파일이 업로드되지 않았는지 확인

### 2. Streamlit Cloud
- [ ] 계정 생성 (GitHub 연동)
- [ ] 앱 생성
- [ ] Private 저장소 선택

### 3. Secrets 설정
- [ ] `OPENAI_API_KEY` 입력
- [ ] `CONFLUENCE_URL` 입력
- [ ] `CONFLUENCE_USERNAME` 입력
- [ ] `CONFLUENCE_API_TOKEN` 입력
- [ ] `CONFLUENCE_SPACE_KEY` 입력
- [ ] `SLACK_BOT_TOKEN` 입력
- [ ] `SLACK_CHANNEL_ID` 입력

### 4. 배포 확인
- [ ] 앱이 정상적으로 시작됨
- [ ] 테스트 회의록 생성 성공
- [ ] Confluence 업로드 성공
- [ ] Slack 메시지 전송 성공

---

## 🎯 배포 후 체크

### 기능 테스트
- [ ] 제목 자동 생성 작동
- [ ] 액션아이템 AI 추출 작동
- [ ] 액션아이템 편집 가능
- [ ] Confluence 체크박스 정상 표시
- [ ] Confluence 캘린더 정상 표시
- [ ] Slack 메시지 정상 전송

### 보안 재확인
- [ ] GitHub에 `.env` 파일 없음
- [ ] Streamlit Secrets에만 API 키 존재
- [ ] URL 공유 시 민감정보 노출 안됨

---

## 📞 문제 발생 시

### API 키 관련
- Streamlit Cloud → Settings → Secrets 다시 확인
- 오타 확인
- 따옴표 확인

### 배포 실패
- Logs 확인
- requirements.txt 확인
- GitHub 권한 확인

---

## ✨ 완료!

모든 체크리스트를 통과했다면 배포 완료입니다! 🎉

팀원들에게 URL을 공유하세요:
`https://your-username-meeting-automation.streamlit.app`


