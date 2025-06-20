import os
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

def sanitize_filename(filename):
    """清除檔案名稱中的無效字元，使其可以在檔案系統中安全使用。"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_episode(url, save_path):
    """下載單一音檔並顯示進度，如果檔案已存在則跳過。"""
    if os.path.exists(save_path):
        print(f"✅ 已存在，跳過。")
        return True
        
    try:
        print(f"  📥 下載中...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"  👍 下載成功！")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n  ❌ 下載失敗：{e}")
        if os.path.exists(save_path):
            os.remove(save_path)
        return False

def parse_and_download_podcast():
    """主程式：提示使用者輸入 RSS Feed URL 和下載數量，並下載對應的集數。"""
    rss_url = input("請貼上 Podcast 的 RSS Feed URL：\n> ")

    if not rss_url.startswith(('http://', 'https://')):
        print("錯誤：這不是一個有效的 URL。")
        return

    # ★ 新增功能：詢問要下載的集數
    num_to_download_str = input("你想下載最新的幾集？ (請輸入數字，或直接按 Enter 下載全部)\n> ")
    num_to_download = None
    if num_to_download_str.strip():
        try:
            num = int(num_to_download_str)
            if num > 0:
                num_to_download = num
        except ValueError:
            print("輸入無效，將下載全部集數。")
            
    try:
        print("\n📡 正在取得並解析 RSS Feed...")
        response = requests.get(rss_url, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"錯誤：無法取得 RSS Feed。\n{e}")
        return

    try:
        root = ET.fromstring(response.content)
        
        podcast_title = root.findtext('./channel/title', 'Untitled Podcast')
        safe_podcast_title = sanitize_filename(podcast_title)
        
        print(f"🎧 節目名稱：'{podcast_title}'")
        
        base_dir = "podcast_downloads"
        podcast_dir = os.path.join(base_dir, safe_podcast_title)
        os.makedirs(podcast_dir, exist_ok=True)
        print(f"📁 檔案將儲存於：'{podcast_dir}'")
        
        all_items = root.findall('./channel/item')
        
        # ★ 新增功能：根據使用者輸入決定要處理的集數列表
        items_to_process = []
        if num_to_download and num_to_download <= len(all_items):
            # RSS Feed 通常最新的在最前面，所以我們取前 n 個
            items_to_process = all_items[:num_to_download]
            print(f"🔍 準備處理最新的 {num_to_download} 集節目。")
        else:
            items_to_process = all_items
            print(f"🔍 準備處理全部 {len(all_items)} 集節目。")
        
        total_to_process = len(items_to_process)
        print(f"開始檢查與下載...\n")

        for i, item in enumerate(items_to_process):
            ep_title = item.findtext('title', 'Untitled Episode')
            print(f"--- ({i+1}/{total_to_process}) 正在處理：{ep_title} ---")
            
            pub_date_str = item.findtext('pubDate', '')
            date_prefix = 'NODATE'
            if pub_date_str:
                try:
                    date_obj = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                    date_prefix = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                     pass

            enclosure = item.find('enclosure')
            if enclosure is None or 'url' not in enclosure.attrib:
                print(f"  ⚠️ 警告：找不到音檔連結，已跳過。")
                continue
            
            audio_url = enclosure.attrib['url']
            
            safe_ep_title = sanitize_filename(ep_title)
            filename = f"{date_prefix} - {safe_ep_title}.mp3"
            filepath = os.path.join(podcast_dir, filename)
            
            download_episode(url=audio_url, save_path=filepath)

        print("\n🎉 所有任務完成！")

    except ET.ParseError:
        print("錯誤：無法解析 RSS Feed。")
    except Exception as e:
        print(f"發生未預期的錯誤：{e}")

# --- 主程式執行區 ---
if __name__ == "__main__":
    parse_and_download_podcast()