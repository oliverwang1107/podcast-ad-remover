import os
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment

# --- 新增的函式 ---
def compress_audio_if_needed(file_path, size_limit_mb=25, bitrate="96k"):
    """
    檢查音檔大小，如果超過限制，就進行壓縮。
    返回一個可供上傳的檔案路徑 (可能是原始路徑或壓縮後的新路徑)。
    """
    limit_bytes = size_limit_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)

    if file_size <= limit_bytes:
        print(f"✅ 檔案大小 ({file_size / 1024 / 1024:.2f}MB) 未超過 {size_limit_mb}MB 限制，無需壓縮。")
        return file_path

    print(f"⚠️ 檔案大小 ({file_size / 1024 / 1024:.2f}MB) 超過 {size_limit_mb}MB 限制，開始壓縮...")
    
    # 定義壓縮後的新檔名
    original_dir = os.path.dirname(file_path)
    original_filename = os.path.basename(file_path)
    compressed_filename = f"compressed_{original_filename}"
    compressed_path = os.path.join(original_dir, compressed_filename)

    try:
        # 使用 pydub 讀取音檔
        audio = AudioSegment.from_mp3(file_path)
        
        # 匯出並設定較低的位元速率 (96k 對於語音來說品質足夠且檔案小)
        audio.export(compressed_path, format="mp3", bitrate=bitrate)
        
        new_size = os.path.getsize(compressed_path)
        print(f"👍 壓縮完成！新檔案：'{compressed_path}' (大小: {new_size / 1024 / 1024:.2f}MB)")
        
        return compressed_path
    except Exception as e:
        print(f"❌ 壓縮失敗：{e}")
        return None


# --- 原有的函式，但現在會先呼叫壓縮函式 ---
def transcribe_audio_with_api(audio_file_path):
    if not audio_file_path:
        return

    # ★ 關鍵改動：先呼叫檢查與壓縮的函式
    file_to_upload = compress_audio_if_needed(audio_file_path)
    
    if not file_to_upload:
        print("無法取得可上傳的檔案，終止轉錄。")
        return

    try:
        load_dotenv()
        client = OpenAI()

        print(f"\n🎧 正在上傳並轉錄檔案：'{file_to_upload}'...")
        # ... 後續程式碼不變 ...
        with open(file_to_upload, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="verbose_json",
                prompt="這是一段台灣的 Podcast 節目..."
            )
        
        print("\n🎉 轉錄成功！")
        print("\n📝【完整逐字稿】")
        print(transcription['text'])
        
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")

# ... select_audio_file() 和主程式執行區的程式碼保持不變 ...
def select_audio_file():
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir) or not os.listdir(base_dir):
        print(f"❌ 錯誤：找不到 '{base_dir}' 資料夾，或資料夾為空。")
        return None
    podcasts = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not podcasts:
        print(f"❌ 錯誤：在 '{base_dir}' 中找不到任何節目資料夾。")
        return None
    print("\n--- 請選擇要處理的 Podcast 節目 ---")
    for i, podcast_name in enumerate(podcasts):
        print(f"[{i + 1}] {podcast_name}")
    try:
        choice = int(input("> 請輸入數字選擇節目: "))
        selected_podcast_dir = podcasts[choice - 1]
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None
    podcast_path = os.path.join(base_dir, selected_podcast_dir)
    episodes = [f for f in os.listdir(podcast_path) if f.endswith(".mp3")]
    if not episodes:
        print(f"❌ 錯誤：在 '{podcast_path}' 中找不到任何 .mp3 檔案。")
        return None
    print(f"\n--- 請選擇 '{selected_podcast_dir}' 的一集 ---")
    for i, episode_name in enumerate(episodes[:20]):
        print(f"[{i + 1}] {episode_name}")
    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        selected_episode_file = episodes[choice - 1]
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None
    return os.path.join(podcast_path, selected_episode_file)

if __name__ == "__main__":
    selected_file = select_audio_file()
    if selected_file:
        transcribe_audio_with_api(selected_file)