import os
import json # ★ 新增：匯入 json 函式庫
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment

# 如果你的環境變數還是有問題，可以保留這一行
# AudioSegment.ffmpeg = "C:/ffmpeg/bin/ffmpeg.exe"

def compress_audio_if_needed(file_path, target_size_mb=24.5):
    # ... (此函式保持不變) ...
    limit_bytes = target_size_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)
    if file_size <= limit_bytes:
        return file_path
    print(f"⚠️ 檔案大小 ({file_size / 1024 / 1024:.2f}MB) 超過 {target_size_mb}MB 限制，開始進行智慧壓縮...")
    try:
        audio = AudioSegment.from_mp3(file_path)
        duration_in_seconds = len(audio) / 1000.0
        if duration_in_seconds == 0: return None
        target_bitrate_kbps = (limit_bytes * 8) / duration_in_seconds / 1000
        final_bitrate_kbps = max(target_bitrate_kbps, 32)
        bitrate_str = f"{int(final_bitrate_kbps)}k"
        print(f"🧮 計算目標位元速率為: {bitrate_str}")
        original_dir = os.path.dirname(file_path)
        original_filename = os.path.basename(file_path)
        compressed_filename = f"compressed_{original_filename}"
        compressed_path = os.path.join(original_dir, compressed_filename)
        audio.export(compressed_path, format="mp3", bitrate=bitrate_str)
        new_size = os.path.getsize(compressed_path)
        print(f"👍 壓縮完成！新檔案大小: {new_size / 1024 / 1024:.2f}MB)")
        return compressed_path
    except Exception as e:
        print(f"❌ 壓縮失敗：{e}")
        return None

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
                prompt="這是一段台灣的 Podcast 節目..."
            )
        
        print("\n🎉 轉錄成功！")
        
        # --- ★★★ 新增：儲存檔案的邏輯 ★★★ ---
        
        # 1. 決定儲存的檔名 (跟音檔同名，但副檔名不同)
        base_filename = os.path.splitext(audio_file_path)[0]
        txt_path = base_filename + ".txt"
        json_path = base_filename + ".json"

        # 2. 儲存 .txt 純文字檔
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcription.text)
        print(f"✅ 完整逐字稿已儲存至：{txt_path}")

        # 3. 準備並儲存 .json 檔案
        # 將回傳的 segment 物件列表轉換成 Python 的字典列表，才能存成 JSON
        segments_data = [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text
            } for seg in transcription.segments
        ]
        
        with open(json_path, 'w', encoding='utf-8') as f:
            # json.dump 可以將 Python 字典寫入檔案
            # ensure_ascii=False 確保中文能正確寫入
            # indent=4 讓 JSON 檔案格式化，方便閱讀
            json.dump(segments_data, f, ensure_ascii=False, indent=4)
        print(f"✅ 附時間戳記的 JSON 檔案已儲存至：{json_path}")
        
        # ----------------------------------------------------
        
        print("\n📝【完整逐字稿 (預覽)】")
        print(transcription.text)
        
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")

# ... select_audio_file() 和主程式執行區的程式碼保持不變 ...
def select_audio_file():
    # ... (此函式保持不變) ...
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir) or not os.listdir(base_dir): return None
    podcasts = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not podcasts: return None
    print("\n--- 請選擇要處理的 Podcast 節目 ---")
    for i, podcast_name in enumerate(podcasts): print(f"[{i + 1}] {podcast_name}")
    try:
        choice = int(input("> 請輸入數字選擇節目: "))
        selected_podcast_dir = podcasts[choice - 1]
    except (ValueError, IndexError): return None
    podcast_path = os.path.join(base_dir, selected_podcast_dir)
    episodes = [f for f in os.listdir(podcast_path) if f.endswith(".mp3")]
    if not episodes: return None
    print(f"\n--- 請選擇 '{selected_podcast_dir}' 的一集 ---")
    for i, episode_name in enumerate(episodes[:20]): print(f"[{i + 1}] {episode_name}")
    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        selected_episode_file = episodes[choice - 1]
    except (ValueError, IndexError): return None
    return os.path.join(podcast_path, selected_episode_file)

if __name__ == "__main__":
    selected_file = select_audio_file()
    if selected_file:
        transcribe_audio_with_api(selected_file)