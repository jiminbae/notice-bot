import requests
from bs4 import BeautifulSoup
import time
import os
import telegram_sender

# ==========================================
BOARDS = [
    {
        "name": "📢 학부 공지",
        "url": "https://cse.knu.ac.kr/bbs/board.php?bo_table=sub5_1",
        "file": "latest_notice.txt"
    },
    {
        "name": "💼 학부 인재 모집",
        "url": "https://cse.knu.ac.kr/bbs/board.php?bo_table=sub5_3_a",
        "file": "latest_recruit.txt"
    }
]
# ==========================================

def get_latest_post_info(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None, None, None
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, 'html.parser')

        rows = soup.select("table tbody tr")
        if not rows: return None, None, None

        for row in rows:
            subject_tag = None
            for a_tag in row.select("a"):
                href = (a_tag.get("href") or "").strip()
                if "wr_id=" in href:
                    subject_tag = a_tag
                    break
            if not subject_tag: continue

            title = subject_tag.get_text(strip=True)
            link = (subject_tag.get("href") or "").strip()
            
            if not link.startswith("http"):
                link = "https://cse.knu.ac.kr/bbs/" + link.lstrip("./")

            date_tag = row.select_one(".td_datetime")
            post_date = date_tag.get_text(strip=True) if date_tag else "no-date"

            return title, link, post_date

        return None, None, None

    except Exception as e:
        print(f"크롤링 에러: {e}")
        return None, None, None

def check_new_notice():
    print(f"\n[텔레그램] 감시 중 ({time.strftime('%H:%M:%S')})")
    
    for board in BOARDS:
        url = board["url"]
        filename = board["file"]
        board_name = board["name"]
        
        title, link, date = get_latest_post_info(url)
        
        if not title: continue

        current_fingerprint = f"{title}|{date}|{link}"

        if not os.path.exists(filename):
            print(f"   🎉 {board_name}: 첫 실행!")
            
            msg = f"[{board_name} - 최신 글]\n{title}"
            telegram_sender.send_msg(msg, link)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(current_fingerprint)
            continue

        with open(filename, "r", encoding="utf-8") as f:
            last_fingerprint = f.read().strip()

        if current_fingerprint != last_fingerprint:
            last_parts = last_fingerprint.split("|")
            
            if title != last_parts[0]:
                status = "✨ 새 글 등록"
            elif date != last_parts[1]:
                status = "📝 내용 수정됨"
            else:
                status = "🔔 업데이트"

            print(f"   🔥 {board_name}: {status} 발견!!")
            
            msg = f"[{board_name} - {status}]\n{title}"
            telegram_sender.send_msg(msg, link)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(current_fingerprint)
        else:
            print(f"   💤 {board_name}: 잠잠함...")

if __name__ == "__main__":
    print("공지사항 알림 시작")
    #telegram_sender.send_msg("봇이 실행되었습니다. 최신 공지를 확인합니다 👀")
    
    while True:
        check_new_notice()
        time.sleep(300) # 5분 대기