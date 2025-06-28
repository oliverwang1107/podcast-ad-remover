import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

def select_json_file():
    """
    提供一個互動式選單，讓使用者選擇要分析的 .json 逐字稿檔案。
    """
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir) or not os.listdir(base_dir):
        print(f"❌ 錯誤：找不到 '{base_dir}' 資料夾，或資料夾為空。")
        return None
    podcasts = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not podcasts:
        print(f"❌ 錯誤：在 '{base_dir}' 中找不到任何節目資料夾。")
        return None
    print("\n--- 請選擇要分析的 Podcast 節目 ---")
    for i, podcast_name in enumerate(podcasts):
        print(f"[{i + 1}] {podcast_name}")
    try:
        choice = int(input("> 請輸入數字選擇節目: "))
        selected_podcast_dir = podcasts[choice - 1]
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None
    podcast_path = os.path.join(base_dir, selected_podcast_dir)
    # 精準尋找由 whisper.cpp 產生的 .mp3.json 檔案
    json_files = [f for f in os.listdir(podcast_path) if f.endswith(".mp3.json") and not f.endswith(".analysis.json")]
    if not json_files:
        print(f"❌ 錯誤：在 '{podcast_path}' 中找不到任何可供分析的 .json 逐字稿檔案。")
        return None
    print(f"\n--- 請選擇 '{selected_podcast_dir}' 的一份逐字稿 ---")
    for i, file_name in enumerate(json_files):
        print(f"[{i + 1}] {file_name}")
    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        selected_file = json_files[choice - 1]
    except (ValueError, IndexError):
        print("❌ 選擇無效。")
        return None
    return os.path.join(podcast_path, selected_file)


def analyze_transcript_with_google_api(json_transcript_path):
    """
    使用 Google AI Studio 的原生 API，來分析由 whisper.cpp 產生的逐字稿 JSON 檔案。
    """
    if not json_transcript_path:
        return
        
    try:
        print(f"📄 正在讀取並解析檔案: {os.path.basename(json_transcript_path)}")
        with open(json_transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # ★★★ 全新、精準的解析邏輯，完美適配你的 JSON 格式 ★★★
        if 'transcription' not in data or not isinstance(data['transcription'], list):
            print(f"❌ 錯誤：在 JSON 檔案中找不到 'transcription' 列表。")
            return

        segments = data['transcription']
        
        transcript_text_parts = []
        for s in segments:
            # 從 offsets 物件中讀取時間 (毫秒)
            start_ms = s.get('offsets', {}).get('from', 0)
            end_ms = s.get('offsets', {}).get('to', 0)
            text = s.get('text', '').strip() # 取得文字並去除前後空格
            
            # 組合傳送給 AI 的格式化文字稿
            transcript_text_parts.append(f"[{start_ms/1000:.2f}s - {end_ms/1000:.2f}s] {text}")
        
        transcript_text = "\n".join(transcript_text_parts)
        
        if not transcript_text.strip():
            print("⚠️ 警告：逐字稿內容為空，終止分析。")
            return

    except Exception as e:
        print(f"❌ 讀取或解析 JSON 檔案時發生錯誤: {e}")
        return

    # --- 後續的 Google API 呼叫、結果處理和儲存邏輯保持不變 ---
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ 錯誤：請在 .env 檔案中設定 GOOGLE_API_KEY")
        return

    try:
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        full_prompt = f"""
你是一位專業的 Podcast 分析師，你的唯一任務是根據使用者提供的逐字稿，找出廣告時段，並以純粹的 JSON 格式回傳結果。
你的回覆**必須**是一個 JSON 物件，該物件只有一個名為 "ads" 的 key，其 value 是一個陣列。
陣列中的每個物件都代表一個廣告時段，並包含 'start_time' (秒), 'end_time' (秒), 和 'reason' (簡短原因)。
如果沒有廣告，"ads" 的 value 必須是一個空陣列 `[]`。

### 範例輸出 (EXAMPLE OUTPUT) ###
```json
{{
  "ads": [
    {{
      "start_time": 1.50,
      "end_time": 97.00,
      "reason": "由 Sharp 贊助，介紹新品家電。"
    }}
  ]
}}
```
"""

        # 啟用 JSON 模式
        generation_config = genai.GenerationConfig(response_mime_type="application/json")

        print("🤖 正在呼叫 Google AI 進行分析 (模型: gemini-2.0-flash)...")
        # 將逐字稿內容傳遞給模型
        response = model.generate_content(
            [full_prompt, "### 逐字稿 (TRANSCRIPT) ###", transcript_text],
            generation_config=generation_config
        )

        # --- 防禦性解析 ---
        # 1. 移除常見的 Markdown 區塊標記
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        # 2. 解析 JSON
        print("✅ AI 回應接收完成，正在解析 JSON...")
        result_json = json.loads(cleaned_text)

        # 將分析結果儲存到新的 .analysis.json 檔案中
        output_filename = os.path.splitext(json_transcript_path)[0] + '.analysis.json'
        
        # 美化 JSON 輸出
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)

        print(f"💾 分析結果已成功儲存至: {output_filename}")

    except json.JSONDecodeError as e:
        print(f"❌ 解析 AI 回應的 JSON 時失敗: {e}")
        print("收到的原始文字:", response.text)
    except Exception as e:
        print(f"❌ 呼叫 Google API 或處理回應時發生錯誤: {e}")


if __name__ == '__main__':
    # 讓使用者選擇檔案
    target_file = select_json_file()
    # 如果使用者有選擇檔案，就執行分析
    if target_file:
        analyze_transcript_with_google_api(target_file)