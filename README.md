# Notice Bot

경북대학교 컴퓨터학부의 공지사항과 인재모집 게시판을 15분마다 자동으로 확인하여, 새로운 글이 올라오면 텔레그램으로 알림을 보내주는 봇입니다.

## 주요 기능
- **실시간 감시**: GitHub Actions를 이용해 평일 업무 시간(09:00~18:00)에는 15분 간격, 그 외에는 1시간 간격으로 게시판을 모니터링합니다.
- **중복 방지**: 최근 게시글의 '제목+날짜+링크'를 지문(Fingerprint)으로 저장하여, 이미 보낸 알림은 다시 보내지 않습니다.
- **수정 감지**: 게시글의 내용이나 날짜가 수정된 경우에도 이를 감지하여 '내용 수정됨' 알림을 보냅니다.

## Tech Stack
- **Language**: Python 3.12
- **Crawling**: BeautifulSoup4, Requests
- **Infra**: GitHub Actions
- **Notification**: Telegram Bot API

## How to Run
로컬에서 테스트하려면 아래와 같이 실행하세요.

1. **환경 변수 설정** (보안을 위해 토큰은 환경변수로 관리)
   ```bash
   export TELEGRAM_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   ```

2. **라이브러리 설치**
  ```bash
  pip install -r requirements.txt
  ```

3. **실행**
  ```bash
  python main.py
  ```
   
