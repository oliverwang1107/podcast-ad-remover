import os
import json
import openai
from dotenv import load_dotenv

# ... select_json_file() 函式保持不變 ...
def select_json_file():
    base_dir = "podcast_downloads"
    if not os.path.exists(base_dir) or not os.listdir(base_dir): return None
    podcasts = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not podcasts: return None
    print("\n--- 請選擇要分析的 Podcast 節目 ---")
    for i, podcast_name in enumerate(podcasts): print(f"[{i + 1}] {podcast_name}")
    try:
        choice = int(input("> 請輸入數字選擇節目: "))
        selected_podcast_dir = podcasts[choice - 1]
    except (ValueError, IndexError): return None
    podcast_path = os.path.join(base_dir, selected_podcast_dir)
    json_files = [f for f in os.listdir(podcast_path) if f.endswith(".json") and not f.endswith(".ads.json")]
    if not json_files: return None
    print(f"\n--- 請選擇 '{selected_podcast_dir}' 的一份逐字稿 ---")
    for i, file_name in enumerate(json_files): print(f"[{i + 1}] {file_name}")
    try:
        choice = int(input("> 請輸入數字選擇檔案: "))
        selected_file = json_files[choice - 1]
    except (ValueError, IndexError): return None
    return os.path.join(podcast_path, selected_file)


def analyze_transcript_with_gemma(json_transcript_path):
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
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("❌ 錯誤：請在 .env 檔案中設定 OPENROUTER_API_KEY")
        return

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key,
    )

    system_prompt = "你是一位專業的 Podcast 分析師..." # (提示詞內容不變)
    user_prompt = f"""
請根據以下這份 Podcast 逐字稿，找出所有的廣告時段...
--- 逐字稿開始 ---
{transcript_text}
--- 逐字稿結束 ---
"""

    print(f"\n🤖 正在將逐字稿發送給 {os.getenv('AI_MODEL_NAME', 'AI')} 進行分析，請稍候...")

    try:
        response = client.chat.completions.create(
            model=os.getenv("AI_MODEL_NAME", "deepseek/deepseek-r1-0528:free"), # 從環境變數讀取模型或使用預設值
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"}, 
        )

        result_content = response.choices[0].message.content
        print(f"\n✅ {os.getenv('AI_MODEL_NAME', 'AI')} 分析完成！")
        print("--- AI 回傳的原始結果 ---")
        print(result_content)

        try:
            ad_segments_obj = json.loads(result_content)
            
            # ★★★ 這就是儲存 JSON 的地方 ★★★
            # 1. 決定儲存的檔名
            base_filename = os.path.splitext(json_transcript_path)[0]
            output_json_path = base_filename + ".ads.json"

            # 2. 將 Python 物件寫入 .ads.json 檔案
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(ad_segments_obj, f, ensure_ascii=False, indent=4)
            print(f"\n💾 AI 分析結果已儲存至：{output_json_path}")
            # ★★★★★★★★★★★★★★★★★★★★★★★

            ad_segments = ad_segments_obj.get('ads', [])
            print("\n--- 解析後的廣告時段 ---")
            if ad_segments:
                for ad in ad_segments:
                    print(f"發現廣告：從 {ad.get('start_time', 'N/A')} 秒 到 {ad.get('end_time', 'N/A')} 秒，原因：{ad.get('reason', 'N/A')}")
            else:
                print("分析結果為：未發現廣告。")
        except (json.JSONDecodeError, AttributeError):
            print("\n⚠️ 警告：AI 回傳的內容不是預期的 JSON 格式。")

    except Exception as e:
        print(f"❌ 呼叫 OpenRouter API 時發生錯誤: {e}")


if __name__ == "__main__":
    selected_json_file = select_json_file()
    if selected_json_file:
        analyze_transcript_with_gemma(selected_json_file)