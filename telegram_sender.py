import requests
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_msg(text, link=""):
    """
    text: 보낼 메시지 내용 (제목 등)
    link: 공지사항 URL
    """
    if link:
        formatted_text = f"<b>{text}</b>\n\n<a href='{link}'>🔗 공지 바로가기 🔗</a>"
    else:
        formatted_text = text

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    params = {
        "chat_id": CHAT_ID,
        "text": formatted_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("텔레그램 전송 성공")
        else:
            print(f"전송 실패: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    send_msg("테스트 메시지", "https://cse.knu.ac.kr")

