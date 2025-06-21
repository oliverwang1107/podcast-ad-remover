import os
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# 如果你的環境變數還是有問題，可以保留這一行作為必殺技
# 如果環境變數已正常，可以註解或刪掉這一行
# AudioSegment.ffmpeg = "C:/ffmpeg/bin/ffmpeg.exe"
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★

def compress_audio_if_needed(file_path, target_size_mb=24.5):
    """
    檢查音檔大小，如果超過限制，就進行「智慧壓縮」，
    計算所需位元速率以達到目標大小。
    """
    limit_bytes = target_size_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)

    if file_size <= limit_bytes:
        print(f"✅ 檔案大小 ({file_size / 1024 / 1024:.2f}MB) 未超過 {target_size_mb}MB 限制，無需壓縮。")
        return file_path

    print(f"⚠️ 檔案大小 ({file_size / 1024 / 1024:.2f}MB) 超過 {target_size_mb}MB 限制，開始進行智慧壓縮...")
    
    try:
        # 讀取音檔以取得資訊
        audio = AudioSegment.from_mp3(file_path)
        duration_in_seconds = len(audio) / 1000.0
        
        if duration_in_seconds == 0:
            print("❌ 錯誤：無法讀取音檔時長，無法計算位元速率。")
            return None

        # --- 智慧計算位元速率 ---
        # 目標大小(bytes) * 8 (bits/byte) / 時長(sec) = 目標位元速率(bps)
        # 再除以 1000 換算成 kbps
        target_bitrate_kbps = (limit_bytes * 8) / duration_in_seconds / 1000
        
        # 為了保證最基本的語音清晰度，設定一個最低的位元速率，例如 32k
        # 如果計算出的值低於 32，我們就用 32k，否則用計算值
        final_bitrate_kbps = max(target_bitrate_kbps, 32)
        bitrate_str = f"{int(final_bitrate_kbps)}k"
        
        print(f"🕒 音檔時長: {duration_in_seconds:.2f} 秒")
        print(f"🧮 計算目標位元速率為: {bitrate_str}")

        # 定義壓縮後的新檔名
        original_dir = os.path.dirname(file_path)
        original_filename = os.path.basename(file_path)
        compressed_filename = f"compressed_{original_filename}"
        compressed_path = os.path.join(original_dir, compressed_filename)
        
        # 匯出並使用計算出的位元速率
        audio.export(compressed_path, format="mp3", bitrate=bitrate_str)
        
        new_size = os.path.getsize(compressed_path)
        print(f"👍 壓縮完成！新檔案：'{compressed_path}' (大小: {new_size / 1024 / 1024:.2f}MB)")
        
        return compressed_path

    except Exception as e:
        print(f"❌ 壓縮失敗：{e}")
        return None


# transcribe_audio_with_api 和 select_audio_file 函式保持不變
def transcribe_audio_with_api(audio_file_path):
    if not audio_file_path:
        return

    file_to_upload = compress_audio_if_needed(audio_file_path)
    
    if not file_to_upload:
        print("無法取得可上傳的檔案，終止轉錄。")
        return

    try:
        load_dotenv()
        client = OpenAI()

        print(f"\n🎧 正在上傳並轉錄檔案：'{file_to_upload}'...")
        print("這可能會需要幾分鐘的時間，請稍候...")

        with open(file_to_upload, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="verbose_json",
                prompt="這是一段台灣的 Podcast 節目，內容可能包含一些台灣用語、人名或地名，例如 PTT、Dcard、股癌、台積電。"
            )
        
        print("\n🎉 轉錄成功！")
        print("\n📝【完整逐字稿】")
        print(transcription['text'])
        
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")

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