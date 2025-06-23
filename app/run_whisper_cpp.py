import os
import subprocess
import time

def select_mp3_file():
    """
    提供互動式選單，讓使用者選擇要轉錄的 .mp3 檔案。
    只列出尚未產生 .json 逐字稿的檔案。
    """
    base_dir = "podcast_downloads"
    # 為了簡化路徑，我們直接從使用者的家目錄開始找
    home_dir = os.path.expanduser("~/podcast-ad-remover")
    search_dir = os.path.join(home_dir, base_dir)

    if not os.path.exists(search_dir) or not os.listdir(search_dir):
        print(f"❌ 錯誤：找不到 '{search_dir}' 資料夾，或資料夾為空。")
        return None
        
    podcasts = [d for d in os.listdir(search_dir) if os.path.isdir(os.path.join(search_dir, d))]
    if not podcasts:
        print(f"❌ 錯誤：在 '{search_dir}' 中找不到任何節目資料夾。")
        return None

    print("\n--- 請選擇要轉錄的 Podcast 節目 ---")
    for i, podcast_name in enumerate(podcasts):
        print(f"[{i + 1}] {podcast_name}")
    try:
        choice = int(input("> 請輸入數字選擇節目: "))
        podcast_path = os.path.join(search_dir, podcasts[choice - 1])
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None
        
    # 只列出還沒有 .json 逐字稿的 mp3 檔案
    mp3_files = [f for f in os.listdir(podcast_path) if f.endswith(".mp3") and not os.path.exists(os.path.join(podcast_path, f + ".json"))]
    if not mp3_files:
        print(f"✅ 在 '{podcasts[choice - 1]}' 中沒有找到需要轉錄的新檔案。")
        return None

    print(f"\n--- 請選擇 '{podcasts[choice - 1]}' 要轉錄的一集 ---")
    for i, file_name in enumerate(mp3_files):
        print(f"[{i + 1}] {file_name}")
    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        # 回傳檔案的絕對路徑
        return os.path.join(podcast_path, mp3_files[choice - 1])
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None

def select_model_size():
    """讓使用者選擇要使用的 Whisper 模型大小。"""
    sizes = ["tiny", "base", "small", "medium"]
    print("\n--- 請選擇 Whisper 模型大小 (在 Radxa 上建議 base 或 small) ---")
    for i, size in enumerate(sizes):
        print(f"[{i + 1}] {size}")
    try:
        choice = int(input("> 請輸入數字選擇模型 [預設為 base]: "))
        return sizes[choice - 1]
    except (ValueError, IndexError):
        print("選擇無效，將使用預設的 'base' 模型。")
        return "base"

def transcribe_with_whisper_cpp(audio_path, model_size):
    """
    使用 Python 的 subprocess 模組來呼叫 whisper.cpp 的執行檔。
    """
    if not audio_path or not model_size:
        return

    home_dir = os.path.expanduser("~")
    whisper_cpp_dir = os.path.join(home_dir, "whisper.cpp")
    
    # 根據我們之前的結論，使用新的 whisper-cli 執行檔
    executable_path = os.path.join(whisper_cpp_dir, "build", "bin", "whisper-cli")
    model_path = os.path.join(whisper_cpp_dir, "models", f"ggml-{model_size}.bin")

    if not os.path.exists(executable_path):
        print(f"❌ 錯誤：找不到 whisper.cpp 執行檔於 '{executable_path}'")
        print("請確認你是否已經成功編譯 whisper.cpp。")
        return
    if not os.path.exists(model_path):
        print(f"❌ 錯誤：找不到模型檔案 '{model_path}'")
        print(f"請先執行 'bash ./models/download-ggml-model.sh {model_size}' 以下載模型。")
        return

    print("\n" + "="*50)
    print(f"準備執行 whisper.cpp 轉錄...")
    print(f"  - 模型: {model_size}")
    print(f"  - 檔案: {os.path.basename(audio_path)}")
    print("="*50 + "\n")
    
    # ★★★ 核心指令 ★★★
    # 我們組合出要在終端機執行的完整指令
    # -oj, --output-json : 告訴程式要輸出 .json 檔案
    command = [
        executable_path,
        "-m", model_path,
        "-f", audio_path,
        "-l", "auto", # 自動偵測語言
        "-oj" # ★ 關鍵：這個參數會讓它產生 .json 輸出！
    ]

    try:
        start_time = time.time()
        # 使用 subprocess.run 來執行外部指令
        # check=True 表示如果指令執行失敗，Python 會拋出例外
        subprocess.run(command, check=True)
        end_time = time.time()
        
        output_json_path = audio_path + ".json"
        print("\n" + "*"*50)
        print("🎉🎉🎉 轉錄成功！ 🎉🎉🎉")
        print(f"總耗時: {end_time - start_time:.2f} 秒")
        print(f"💾 附時間戳記的 JSON 檔案已儲存至: {output_json_path}")
        print("*"*50)

    except FileNotFoundError:
        # 這個錯誤通常發生在 subprocess 找不到 command[0] 的執行檔時
        print(f"❌ 執行錯誤：系統找不到指令 '{command[0]}'")
    except subprocess.CalledProcessError as e:
        # 如果 whisper.cpp 執行過程中回傳了非零的結束碼 (代表出錯)
        print(f"❌ whisper.cpp 執行過程中發生錯誤，錯誤碼: {e.returncode}")
    except Exception as e:
        print(f"❌ 發生未知錯誤: {e}")

if __name__ == "__main__":
    mp3_file_to_process = select_mp3_file()
    
    if mp3_file_to_process:
        chosen_model_size = select_model_size()
        if chosen_model_size:
            transcribe_with_whisper_cpp(mp3_file_to_process, chosen_model_size)