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
    json_files = [f for f in os.listdir(podcast_path) if f.endswith(".json") and not f.endswith(".ads.json")]
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
    使用 Google AI Studio 的原生 API 來分析逐字稿 JSON 檔案。
    """
    if not json_transcript_path:
        return
        
    try:
        with open(json_transcript_path, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        transcript_text = "\n".join([f"[{s['start']:.2f}s - {s['end']:.2f}s] {s['text']}" for s in segments])
    except Exception as e:
        print(f"❌ 讀取或解析 JSON 檔案時發生錯誤: {e}")
        return

    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ 錯誤：請在 .env 檔案中設定 GOOGLE_API_KEY")
        return

    try:
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # ★★★ 全新的、更穩健的 Prompt 組合方式 ★★★
        # 我們將指令拆成一個列表，再用換行符號組合起來，以避免多行字串的語法錯誤。
        prompt_lines = [
            '你是一位專業的 Podcast 分析師，你的唯一任務是根據使用者提供的逐字稿，找出廣告時段，並以純粹的 JSON 格式回傳結果。',
            '',
            '你的回覆**必須**是一個 JSON 物件，該物件只有一個名為 "ads" 的 key，其 value 是一個陣列。',
            "陣列中的每個物件都代表一個廣告時段，並包含 'start_time' (秒), 'end_time' (秒), 和 'reason' (簡短原因)。",
            '如果沒有廣告，"ads" 的 value 必須是一個空陣列 `[]`。',
            '',
            '### 範例輸出 (EXAMPLE OUTPUT) ###',
            '```json',
            '{',
            '  "ads": [',
            '    {',
            '      "start_time": 1.50,',
            '      "end_time": 97.00,',
            '      "reason": "由 Sharp 贊助，介紹新品家電。"',
            '    }',
            '  ]',
            '}',
            '```',
            '**重要提醒：絕對不要在你的回覆中包含任何 JSON 以外的文字、解釋或 markdown 格式。你的輸出必須能被直接解析成 JSON。**',
            '',
            '--- 逐字稿開始 ---',
            transcript_text,
            '--- 逐字稿結束 ---'
        ]
        full_prompt = "\n".join(prompt_lines)
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

        print("\n🤖 正在將逐字稿發送給 Google Gemini 進行分析，請稍候...")

        response = model.generate_content(full_prompt)
        result_content = response.text

        if result_content.startswith("```json"):
            result_content = result_content.strip("```json\n").strip("```")

        print("\n✅ Gemini 分析完成！")
        print("--- AI 回傳的原始結果 ---")
        print(result_content)

        ad_segments_obj = json.loads(result_content)
        base_filename = os.path.splitext(json_transcript_path)[0]
        output_json_path = base_filename + ".analysis.json"
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(ad_segments_obj, f, ensure_ascii=False, indent=4)
        print(f"\n💾 AI 分析結果已儲存至：{output_json_path}")
        
        ad_segments = ad_segments_obj.get('ads', [])
        print("\n--- 解析後的廣告時段 ---")
        if ad_segments:
            for ad in ad_segments:
                print(f"發現廣告：從 {ad.get('start_time', 'N/A')} 秒 到 {ad.get('end_time', 'N/A')} 秒，原因：{ad.get('reason', 'N/A')}")
        else:
            print("分析結果為：未發現廣告。")
            
    except json.JSONDecodeError:
        print("\n⚠️ 警告：AI 回傳的內容不是有效的 JSON 格式。")
    except Exception as e:
        print(f"❌ 呼叫 Google AI API 時發生錯誤: {e}")

if __name__ == "__main__":
    selected_json_file = select_json_file()
    if selected_json_file:
        analyze_transcript_with_google_api(selected_json_file)