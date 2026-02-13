import requests
from bs4 import BeautifulSoup
import time
import os
import json
import hashlib
import telegram_sender

# ==========================================
# 게시판 설정
POST_LIMIT = 15
BOARDS = [
    {
        "name": "📢 학부 공지",
        "url": "https://cse.knu.ac.kr/bbs/board.php?bo_table=sub5_1",
        "file": "notice_list_v2.json"
    },
    {
        "name": "💼 학부 인재 모집",
        "url": "https://cse.knu.ac.kr/bbs/board.php?bo_table=sub5_3_a",
        "file": "recruit_list_v2.json"
    }
]
# ==========================================

def get_post_content(link):
    """
    게시글 본문(상세 내용)을 가져와서 해시값(지문)으로
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(link, headers=headers, timeout=5)
        if response.status_code != 200:
            return ""
        
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.select_one("#bo_v_con")
        
        if content_div:
            return content_div.get_text(strip=True)
        return ""
    except:
        return ""

def get_recent_posts(url, limit):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        posts = []
        rows = soup.select("table tbody tr")
        
        for row in rows:
            if len(posts) >= limit:
                break 

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

            try:
                post_id = link.split("wr_id=")[1].split("&")[0]
            except:
                post_id = link 

            date_tag = row.select_one(".td_datetime")
            post_date = date_tag.get_text(strip=True) if date_tag else "no-date"

            # 본문 내용 확인 (해시값 생성)
            content_text = get_post_content(link)
            content_hash = hashlib.md5(content_text.encode('utf-8')).hexdigest()

            posts.append({
                "id": post_id,
                "title": title,
                "date": post_date,
                "link": link,
                "content_hash": content_hash
            })
            time.sleep(0.3) # 서버 부하 방지

        return posts

    except Exception as e:
        print(f"❌ 목록 크롤링 에러: {e}")
        return []

def check_new_notice():
    print(f"\n[텔레그램] 감시 시작 ({time.strftime('%H:%M:%S')})")
    
    for board in BOARDS:
        board_name = board["name"]
        url = board["url"]
        filename = board["file"]
        
        current_posts = get_recent_posts(url, limit=POST_LIMIT)
        if not current_posts: continue

        saved_posts = {}
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    saved_posts = json.load(f)
            except:
                saved_posts = {}

        # 첫 실행이면 저장만 하고 패스
        if len(saved_posts) == 0:
            print(f"   {board_name}: 첫 실행! 기준점 저장 완료.")
            new_save_data = {}
            for post in current_posts:
                new_save_data[post["id"]] = post
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(new_save_data, f, ensure_ascii=False, indent=4)
            continue

        # 알림 보낼 메시지들을 담을 '우체통' (리스트)
        messages_queue = []
        changes_detected = False
        new_save_data = saved_posts.copy()

        for post in current_posts:
            pid = post["id"]
            title = post["title"]
            
            # (A) 새 글 발견
            if pid not in saved_posts:
                print(f"   🔥 {board_name}: 새 글 -> {title}")
                msg = f"[{board_name} - ✨ 새 글]\n{title}"
                # 우체통에 '메시지 내용'과 '링크'를 담음
                messages_queue.append({"msg": msg, "link": post["link"]})
                
                new_save_data[pid] = post
                changes_detected = True

            # (B) 기존 글 수정 발견
            else:
                old_post = saved_posts[pid]
                old_hash = old_post.get("content_hash", "")
                
                is_header_changed = (old_post["title"] != title) or (old_post["date"] != post["date"])
                is_content_changed = (old_hash != post["content_hash"]) and (old_hash != "")

                if is_header_changed:
                    status = "📝 제목/날짜 수정됨"
                elif is_content_changed:
                    status = "🕵️ 본문 내용 수정됨"
                else:
                    status = None

                if status:
                    print(f"   ♻️ {board_name}: {status} -> {title}")
                    msg = f"[{board_name} - {status}]\n{title}\n(링크에서 확인하세요)"
                    messages_queue.append({"msg": msg, "link": post["link"]})
                    
                    new_save_data[pid] = post
                    changes_detected = True

        # 여러 개가 동시에 올라왔을 때, '오래된 순서'대로 보내기 위해 뒤집음
        # 채팅방은 [과거]가 위에 있어야 보기가 편함
        if messages_queue:
            print(f"   총 {len(messages_queue)}개의 알림을 전송합니다.")
            
            # 리스트 뒤집기 (Newest First -> Oldest First)
            messages_queue.reverse()

            for item in messages_queue:
                try:
                    telegram_sender.send_msg(item["msg"], item["link"])
                    time.sleep(1)
                except Exception as e:
                    print(f"   전송 실패: {e}")


        if changes_detected:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(new_save_data, f, ensure_ascii=False, indent=4)
        else:
            print(f"    {board_name}: 변동 없음")

if __name__ == "__main__":
    check_new_notice()
