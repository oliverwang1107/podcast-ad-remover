import os
from openai import OpenAI
from dotenv import load_dotenv

def transcribe_audio_with_api(audio_file_path):
    """
    使用 OpenAI Whisper API 將指定的音訊檔案轉換成文字。
    """
    # 檢查檔案是否存在
    if not os.path.exists(audio_file_path):
        print(f"❌ 錯誤：找不到音訊檔案 '{audio_file_path}'")
        return

    try:
        # 從 .env 檔案載入環境變數 (API 金鑰)
        load_dotenv()
        
        # 初始化 OpenAI Client
        # Client 會自動從環境變數 OPENAI_API_KEY 讀取金鑰
        client = OpenAI()

        print(f"🎧 正在上傳並轉錄檔案：'{audio_file_path}'...")
        print("這可能會需要幾分鐘的時間，請稍候...")

        # 以二進位讀取模式開啟音訊檔案
        with open(audio_file_path, "rb") as audio_file:
            # 呼叫 OpenAI API
            # model="whisper-1" 是固定的模型名稱
            # response_format="verbose_json" 可以讓我們得到包含時間戳記的詳細資訊
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="verbose_json",
                prompt="這是一段台灣的 Podcast 節目，內容可能包含一些台灣用語、人名或地名，例如 PTT、Dcard、股癌、台積電。" # 提供提示(Prompt)可以提高準確率
            )
        
        print("\n🎉 轉錄成功！")
        
        # --- 顯示結果 ---
        print("\n📝【完整逐字稿】")
        # transcription['text'] 包含完整的逐字稿文字
        print(transcription['text'])
        
        print("\n🕒【部分時間戳記片段 (前5段)】")
        # transcription['segments'] 是一個列表，包含每一段的文字和時間
        for segment in transcription['segments'][:5]:
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text']
            print(f"[{start_time:.2f}s -> {end_time:.2f}s] {text}")
            
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")

# --- 主程式執行區 ---
if __name__ == "__main__":
    # --- 請修改成你下載的音檔路徑 ---
    # 假設你的音檔在 'podcast_downloads/Gooaye 股癌/...'
    # 這裡你需要手動指定一個你已經下載好的檔案來測試
    # 注意：請確保路徑和檔名是正確的
    TEST_AUDIO_FILE = os.path.join("podcast_downloads", "Gooaye 股癌", "NODATE - EP565  🦛.mp3")    
    # --------------------------------

    transcribe_audio_with_api(TEST_AUDIO_FILE)