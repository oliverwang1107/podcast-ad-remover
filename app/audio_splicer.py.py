import os
import json
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

def select_analysis_file():
    """
    提供一個互動式選單，讓使用者選擇要處理的 .analysis.json 檔案。
    """
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir):
        print(f"❌ 錯誤：找不到 '{base_dir}' 資料夾。")
        return None

    analysis_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".analysis.json"):
                analysis_files.append(os.path.join(root, file))

    if not analysis_files:
        print(f"❌ 錯誤：在 '{base_dir}' 中找不到任何 .analysis.json 檔案可供處理。")
        return None

    print("\n--- 請選擇要剪輯廣告的分析檔 ---")
    for i, file_path in enumerate(analysis_files):
        # 顯示相對路徑，讓介面更簡潔
        print(f"[{i + 1}] {os.path.relpath(file_path)}")

    try:
        choice = int(input("> 請輸入數字選擇檔案: ")) - 1
        if 0 <= choice < len(analysis_files):
            return analysis_files[choice]
        else:
            print("❌ 選擇無效。")
            return None
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None

def splice_audio_based_on_analysis(analysis_json_path):
    """
    根據 .analysis.json 檔案中的時間戳，剪輯對應的 MP3 檔案並移除廣告。
    """
    if not analysis_json_path:
        return

    print(f"📄 正在處理分析檔: {os.path.basename(analysis_json_path)}")

    # 1. 推導原始 MP3 路徑和輸出路徑
    # e.g., from '.../podcast.mp3.analysis.json' to '.../podcast.mp3'
    original_mp3_path = analysis_json_path.replace('.analysis.json', '')
    # e.g., to '.../podcast_no_ads.mp3'
    output_mp3_path = original_mp3_path.replace('.mp3', '_no_ads.mp3')

    # 2. 檢查必要檔案是否存在
    if not os.path.exists(original_mp3_path):
        print(f"❌ 錯誤：找不到對應的音檔 '{os.path.basename(original_mp3_path)}'")
        return

    try:
        # 3. 讀取 JSON 分析結果
        with open(analysis_json_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        ad_segments = analysis_data.get("ads", [])
        if not ad_segments:
            print("✅ 分析檔中未標記任何廣告，無需剪輯。")
            return

        # 4. 載入音檔
        print(f"🎧 正在載入音檔: {os.path.basename(original_mp3_path)}...")
        # 增加 pydub 對 ffmpeg 的路徑設定，提高相容性
        # AudioSegment.converter = "/path/to/your/ffmpeg" # 如果 ffmpeg 不在系統 PATH 中，請取消註解此行並填寫路徑
        podcast = AudioSegment.from_mp3(original_mp3_path)
        print("✅ 音檔載入完成。")

        # 5. 計算非廣告片段
        # 將廣告時間點從秒轉換為毫秒
        ad_timestamps_ms = [(ad['start_time'] * 1000, ad['end_time'] * 1000) for ad in ad_segments]
        # 根據開始時間排序，確保處理順序正確
        ad_timestamps_ms.sort(key=lambda x: x[0])

        non_ad_parts = []
        last_cut_end = 0
        podcast_duration = len(podcast)

        print("✂️ 正在計算剪輯片段...")
        for start, end in ad_timestamps_ms:
            # 添加上一個剪輯點到這個廣告開始前的片段
            if start > last_cut_end:
                non_ad_parts.append(podcast[last_cut_end:start])
            last_cut_end = end
        
        # 添加最後一個廣告結束到音檔結尾的片段
        if last_cut_end < podcast_duration:
            non_ad_parts.append(podcast[last_cut_end:])

        if not non_ad_parts:
            print("⚠️ 警告：計算後沒有剩餘的音訊片段，可能整個音檔都被標記為廣告。")
            return

        # 6. 拼接非廣告片段
        print("🧩 正在拼接無廣告音訊...")
        final_podcast = sum(non_ad_parts)

        # 7. 匯出新檔案
        print(f"💾 正在匯出新檔案至: {os.path.basename(output_mp3_path)}...")
        final_podcast.export(output_mp3_path, format="mp3")
        print("🎉 成功！已產生無廣告版本的 Podcast！")

    except json.JSONDecodeError:
        print(f"❌ 錯誤：解析 JSON 檔案 '{os.path.basename(analysis_json_path)}' 失敗。")
    except CouldntDecodeError:
        print(f"❌ 錯誤：無法解碼 MP3 檔案 '{os.path.basename(original_mp3_path)}'。")
        print("👉 提示：請確認您已安裝 ffmpeg，並且 pydub 可以找到它。")
    except Exception as e:
        print(f"❌ 處理過程中發生未預期的錯誤: {e}")


if __name__ == '__main__':
    target_file = select_analysis_file()
    if target_file:
        splice_audio_based_on_analysis(target_file)