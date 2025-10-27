#!/bin/bash

# 회의록 자동화 시스템 시작 스크립트

echo "🚀 회의록 자동화 시스템을 시작합니다..."
echo ""

# 현재 디렉토리로 이동
cd "$(dirname "$0")"

# Streamlit 실행
echo "📝 웹 브라우저에서 http://localhost:8501 이 열립니다."
echo ""
echo "종료하려면 이 터미널 창에서 Ctrl+C를 누르세요."
echo ""

python3 -m streamlit run app.py

# 종료 메시지
echo ""
echo "👋 회의록 자동화 시스템이 종료되었습니다."

