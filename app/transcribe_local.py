import os
import json
import time
import whisper # ★ 我們現在匯入的是開源版的 whisper

def select_mp3_file():
    """
    提供互動式選單，讓使用者選擇要轉錄的 .mp3 檔案。
    """
    # ... (這個函式的邏輯和之前選擇 .json 的很像) ...
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir) or not os.listdir(base_dir):
        print(f"❌ 錯誤：找不到 '{base_dir}' 資料夾，或資料夾為空。")
        return None
    podcasts = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not podcasts:
        print(f"❌ 錯誤：在 '{base_dir}' 中找不到任何節目資料夾。")
        return None
    print("\n--- 請選擇要轉錄的 Podcast 節目 ---")
    for i, podcast_name in enumerate(podcasts):
        print(f"[{i + 1}] {podcast_name}")
    try:
        choice = int(input("> 請輸入數字選擇節目: "))
        podcast_path = os.path.join(base_dir, podcasts[choice - 1])
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None
        
    # 只列出還沒有 .json 逐字稿的 mp3 檔案
    mp3_files = [f for f in os.listdir(podcast_path) if f.endswith(".mp3") and not os.path.exists(os.path.join(podcast_path, os.path.splitext(f)[0] + ".json"))]
    if not mp3_files:
        print(f"✅ 在 '{podcasts[choice - 1]}' 中沒有找到需要轉錄的新檔案。")
        return None

    print(f"\n--- 請選擇 '{podcasts[choice - 1]}' 要轉錄的一集 ---")
    for i, file_name in enumerate(mp3_files):
        print(f"[{i + 1}] {file_name}")
    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        return os.path.join(podcast_path, mp3_files[choice - 1])
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None

def select_model_size():
    """讓使用者選擇要使用的 Whisper 模型大小。"""
    sizes = ["tiny", "base", "small", "medium", "large"]
    print("\n--- 請選擇 Whisper 模型大小 ---")
    print("模型越大，準確率越高，但速度越慢，對硬體要求也越高。")
    print("建議初次使用 'base' 或 'small'。")
    for i, size in enumerate(sizes):
        print(f"[{i + 1}] {size}")
    try:
        choice = int(input("> 請輸入數字選擇模型: "))
        return sizes[choice - 1]
    except (ValueError, IndexError):
        print("❌ 選擇無效，將使用預設的 'base' 模型。")
        return "base"

def transcribe_with_local_whisper(audio_path, model_size):
    """
    使用本地的 Whisper 模型來轉錄音檔。
    """
    if not audio_path or not model_size:
        return

    try:
        print(f"\n🧠 正在載入 Whisper '{model_size}' 模型... (第一次使用會需要下載)")
        model = whisper.load_model(model_size)
        print("✅ 模型載入完成。")

        print(f"\n🎧 開始轉錄檔案: {os.path.basename(audio_path)} ...")
        print("這會消耗大量電腦資源，並可能需要很長的時間，請耐心等候...")
        
        start_time = time.time()
        # 執行轉錄，fp16=False 在 CPU 上更穩定，有 GPU 可設為 True
        result = model.transcribe(audio_path, fp16=False, verbose=True)
        end_time = time.time()
        
        print(f"\n🎉 轉錄完成！耗時: {end_time - start_time:.2f} 秒")
        
        # --- 儲存檔案 (格式與 API 版完全一致) ---
        base_filename = os.path.splitext(audio_path)[0]
        txt_path = base_filename + ".txt"
        json_path = base_filename + ".json"

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"💾 純文字逐字稿已儲存至：{txt_path}")
        
        # 為了下游腳本的相容性，我們把 segment 格式整理成跟 API 版一樣
        segments_data = [
            {
                "start": seg['start'],
                "end": seg['end'],
                "text": seg['text']
            } for seg in result['segments']
        ]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(segments_data, f, ensure_ascii=False, indent=4)
        print(f"💾 附時間戳記的 JSON 檔案已儲存至：{json_path}")

    except Exception as e:
        print(f"\n❌ 轉錄過程中發生錯誤: {e}")

if __name__ == "__main__":
    mp3_file = select_mp3_file()
    if mp3_file:
        model_name = select_model_size()
        if model_name:
            transcribe_with_local_whisper(mp3_file, model_name)