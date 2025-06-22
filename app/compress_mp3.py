import os
from pydub import AudioSegment

def select_any_mp3_file():
    """
    提供互動式選單，讓使用者從所有下載的節目中選擇任何一個 MP3 檔案。
    """
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir) or not os.listdir(base_dir):
        print(f"❌ 錯誤：找不到 '{base_dir}' 資料夾，或資料夾為空。")
        return None

    all_mp3_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            # 我們只處理非壓縮過的原始檔
            if file.endswith(".mp3") and not file.startswith("compressed_") and not file.endswith(".ad_free.mp3"):
                relative_path = os.path.relpath(os.path.join(root, file), base_dir)
                all_mp3_files.append(relative_path)

    if not all_mp3_files:
        print("❌ 錯誤：找不到任何原始 .mp3 檔案可供壓縮。")
        return None
    
    print("\n--- 請選擇要進行智慧壓縮的 MP3 檔案 ---")
    for i, file_path in enumerate(all_mp3_files[:30]):
        print(f"[{i + 1}] {file_path}")

    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        selected_relative_path = all_mp3_files[choice - 1]
        return os.path.join(base_dir, selected_relative_path)
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None

def compress_to_target_size(input_path, target_mb=24.5, min_bitrate_kbps=32):
    """
    智慧壓縮音檔，使其大小約等於目標大小。
    """
    if not input_path:
        return

    print("\n--- 正在處理 ---")
    print(f"原始檔案: {input_path}")
    
    try:
        limit_bytes = target_mb * 1024 * 1024
        original_size_bytes = os.path.getsize(input_path)
        original_size_mb = original_size_bytes / 1024 / 1024
        
        print(f"原始大小: {original_size_mb:.2f} MB")
        
        # 1. 檢查是否需要壓縮
        if original_size_bytes <= limit_bytes:
            print(f"✅ 檔案大小未超過 {target_mb}MB，無需壓縮。")
            return

        print(f"⚠️ 檔案大小超過 {target_mb}MB，開始進行智慧壓縮...")
        
        # 2. 載入音檔並計算所需位元速率
        audio = AudioSegment.from_mp3(input_path)
        duration_sec = len(audio) / 1000.0
        
        if duration_sec == 0:
            print("❌ 錯誤：無法讀取音檔時長。")
            return

        # 公式: bitrate (kbps) = (目標大小(bytes) * 8) / 時長(sec) / 1000
        target_bitrate_kbps = (limit_bytes * 8) / duration_sec / 1000
        
        # 確保不會低於最低品質
        final_bitrate_kbps = max(target_bitrate_kbps, min_bitrate_kbps)
        bitrate_str = f"{int(final_bitrate_kbps)}k"
        
        print(f"🕒 音檔時長: {duration_sec:.2f} 秒")
        print(f"🧮 計算目標位元速率為: {bitrate_str}")
        
        # 3. 產生輸出路徑並匯出
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}.compressed{ext}"
        
        print(f"🚀 正在以 {bitrate_str} 位元速率進行壓縮並匯出...")
        audio.export(output_path, format="mp3", bitrate=bitrate_str)
        
        compressed_size_mb = os.path.getsize(output_path) / 1024 / 1024
        print("\n🎉 壓縮完成！")
        print(f"   新檔案大小: {compressed_size_mb:.2f} MB")
        print(f"💾 新檔案已儲存至: {output_path}")

    except Exception as e:
        print(f"❌ 壓縮過程中發生錯誤: {e}")

if __name__ == "__main__":
    file_to_compress = select_any_mp3_file()
    
    if file_to_compress:
        compress_to_target_size(file_to_compress)