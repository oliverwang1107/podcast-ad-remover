import os
import time
import groq # ★ 匯入新的 groq 函式庫
from dotenv import load_dotenv

def select_mp3_file():
    """互動式選單，選擇要轉錄的 MP3 檔案。"""
    # ... (這個函式的程式碼和之前的版本完全一樣，此處省略以保持簡潔) ...
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir) or not os.listdir(base_dir): return None
    podcasts = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not podcasts: return None
    print("\n--- 請選擇要轉錄的 Podcast 節目 ---")
    for i, podcast_name in enumerate(podcasts): print(f"[{i + 1}] {podcast_name}")
    try:
        choice = int(input("> 請輸入數字選擇節目: "))
        podcast_path = os.path.join(base_dir, podcasts[choice - 1])
    except (ValueError, IndexError): return None
    # 只列出還沒有 .txt 逐字稿的 mp3 檔案
    mp3_files = [f for f in os.listdir(podcast_path) if f.endswith(".mp3") and not os.path.exists(os.path.join(podcast_path, os.path.splitext(f)[0] + ".txt"))]
    if not mp3_files:
        print(f"✅ 在 '{podcasts[choice - 1]}' 中沒有找到需要轉錄的新檔案。")
        return None
    print(f"\n--- 請選擇 '{podcasts[choice - 1]}' 要轉錄的一集 ---")
    for i, file_name in enumerate(mp3_files): print(f"[{i + 1}] {file_name}")
    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        return os.path.join(podcast_path, mp3_files[choice - 1])
    except (ValueError, IndexError): return None


def transcribe_with_groq(audio_path):
    """使用 Groq API 進行超高速轉錄。"""
    if not audio_path:
        return

    load_dotenv()
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ 錯誤：請在 .env 檔案中設定 GROQ_API_KEY")
        return

    try:
        # ★ 初始化 Groq Client
        client = groq.Groq(api_key=groq_key)

        print(f"\n⚡️ 正在將檔案 '{os.path.basename(audio_path)}' 上傳至 Groq... (準備感受速度！)")
        
        start_time = time.time()

        with open(audio_path, "rb") as audio_file:
            # ★ 呼叫 audio.transcriptions.create，與 OpenAI SDK 非常相似
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), audio_file.read()),
                model="whisper-large-v3",
                # 你也可以提供 prompt 來提高特定術語的準確性
                # prompt="這是有關台灣科技的 Podcast，可能會提到台積電、聯發科等。"
            )
        
        end_time = time.time()
        print(f"✅ 轉錄完成！**耗時: {end_time - start_time:.2f} 秒**")
        
        # --- 顯示並儲存結果 ---
        print("\n--- 轉錄結果 (純文字) ---")
        print(transcription.text)
        
        # 由於 Groq API 只回傳純文字，我們只儲存 .txt 檔案
        base_filename = os.path.splitext(audio_path)[0]
        txt_path = base_filename + ".txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcription.text)
        print(f"\n💾 純文字逐字稿已儲存至：{txt_path}")

    except Exception as e:
        print(f"\n❌ 呼叫 Groq API 時發生錯誤: {e}")


if __name__ == "__main__":
    mp3_file = select_mp3_file()
    if mp3_file:
        transcribe_with_groq(mp3_file)