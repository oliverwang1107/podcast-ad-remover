# filepath: /home/yaya/podcast-ad-remover/app/main.py
import os
import json
import subprocess
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# --- 核心處理邏輯 (從其他腳本整合而來) ---
# 為了方便管理，我們將 pydub 和 google-generativeai 的匯入放在需要它們的函式內部
# 這樣可以避免在沒有安裝這些套件時，整個應用程式無法啟動。

# --- 資料夾與路徑設定 ---
# 使用 Path 物件來處理路徑，更安全且跨平台
BASE_DIR = Path.home() / "podcast-ad-remover" / "podcast_downloads"
WHISPER_CPP_DIR = Path.home() / "whisper.cpp"
# 確保下載目錄存在
BASE_DIR.mkdir(parents=True, exist_ok=True)


# --- FastAPI 應用程式初始化 ---
app = FastAPI(
    title="Podcast AI Processor API",
    description="處理 Podcast 下載、轉錄、分析與剪輯的後端服務。",
    version="1.0.0",
)

# --- CORS 中介軟體設定 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # 根據您的 React 開發伺服器位址調整
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic 模型 (用於請求和回應的資料驗證) ---
class ProcessRequest(BaseModel):
    filename: str

class SpliceResponse(BaseModel):
    output_filename: str

class DownloadRequest(BaseModel):
    rss_url: str
    num_episodes: Optional[int] = None

# --- 輔助函式 ---
def find_file(filename: str) -> Optional[Path]:
    """在 BASE_DIR 中遞迴搜尋檔案並返回其 Path 物件。"""
    for path_object in BASE_DIR.rglob(filename):
        if path_object.is_file():
            return path_object
    return None

def sanitize_filename(filename: str) -> str:
    """清除檔名中的無效字元。"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)


# --- 背景任務函式 ---

def task_run_whisper_transcription(audio_path: Path):
    """
    (背景任務) 執行 whisper.cpp 進行語音轉錄。
    """
    print(f"背景任務：開始轉錄 {audio_path.name}...")
    try:
        from pydub import AudioSegment # 檢查音檔時長時可能需要
    except ImportError:
        print("錯誤：pydub 未安裝，無法執行某些音訊檢查。請執行 `pip install pydub`")
        return

    model_size = "base"  # 在 Radxa 上建議使用 'base' 或 'small'
    executable_path = WHISPER_CPP_DIR / "build" / "bin" / "whisper-cli"
    model_path = WHISPER_CPP_DIR / "models" / f"ggml-{model_size}.bin"

    if not executable_path.exists() or not model_path.exists():
        print(f"錯誤：找不到 whisper.cpp 執行檔或模型。請檢查路徑：{executable_path}")
        return

    output_json_path = audio_path.with_suffix(audio_path.suffix + ".json")
    if output_json_path.exists():
        print(f"資訊：轉錄稿 '{output_json_path.name}' 已存在，跳過轉錄。")
        return

    command = [str(executable_path), "-m", str(model_path), "-f", str(audio_path), "-l", "auto", "-oj"]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"背景任務：轉錄成功 -> {output_json_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"錯誤：whisper.cpp 執行失敗。返回碼: {e.returncode}")
        print(f"錯誤訊息: {e.stderr}")

def task_analyze_transcript(transcript_path: Path):
    """
    (背景任務) 使用 Google Gemini API 分析逐字稿。
    """
    print(f"背景任務：開始分析 {transcript_path.name}...")
    try:
        import google.generativeai as genai
    except ImportError:
        print("錯誤：google-generativeai 未安裝。請執行 `pip install google-generativeai`")
        return

    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("錯誤：找不到 GOOGLE_API_KEY 環境變數。")
        return

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = data.get('transcription', [])
        if not segments:
            print(f"警告：在 {transcript_path.name} 中找不到逐字稿內容。")
            return
            
        parts = [f"[{s['offsets']['from']/1000:.2f}s - {s['offsets']['to']/1000:.2f}s] {s['text'].strip()}" for s in segments]
        transcript_text = "\n".join(parts)

        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel("gemini-1.5-pro-latest") # 使用支援長上下文的模型
        
        full_prompt = """你是一位專業的 Podcast 分析師，你的唯一任務是根據使用者提供的逐字稿，找出廣告時段，並以純粹的 JSON 格式回傳結果。你的回覆**必須**是一個 JSON 物件，該物件只有一個名為 "ads" 的 key，其 value 是一個陣列。陣列中的每個物件都代表一個廣告時段，並包含 'start_time' (秒), 'end_time' (秒), 和 'reason' (簡短原因)。如果沒有廣告，"ads" 的 value 必須是一個空陣列 `[]`。"""
        
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content([full_prompt, "### 逐字稿 (TRANSCRIPT) ###", transcript_text], generation_config=generation_config)
        
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result_json = json.loads(cleaned_text)

        output_filename = transcript_path.with_suffix('.analysis.json')
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)
        print(f"背景任務：分析成功 -> {output_filename.name}")

    except Exception as e:
        print(f"錯誤：在分析 {transcript_path.name} 過程中發生錯誤: {e}")

def task_splice_audio(analysis_json_path: Path):
    """
    (背景任務) 根據分析檔剪輯音訊，移除廣告。
    """
    print(f"背景任務：開始剪輯 {analysis_json_path.name}...")
    try:
        from pydub import AudioSegment
    except ImportError:
        print("錯誤：pydub 未安裝，無法執行剪輯。請執行 `pip install pydub`")
        return

    original_mp3_path = Path(str(analysis_json_path).replace('.analysis.json', ''))
    output_mp3_path = Path(str(original_mp3_path).replace('.mp3', '_no_ads.mp3'))

    if not original_mp3_path.exists():
        print(f"錯誤：找不到對應的音檔 {original_mp3_path.name}")
        return

    try:
        with open(analysis_json_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        ad_segments = analysis_data.get("ads", [])
        if not ad_segments:
            print(f"資訊：在 {analysis_json_path.name} 中未找到廣告，無需剪輯。")
            return

        podcast = AudioSegment.from_mp3(original_mp3_path)
        ad_timestamps_ms = sorted([(ad['start_time'] * 1000, ad['end_time'] * 1000) for ad in ad_segments])
        
        non_ad_parts = []
        last_cut_end = 0
        for start, end in ad_timestamps_ms:
            if start > last_cut_end:
                non_ad_parts.append(podcast[last_cut_end:start])
            last_cut_end = end
        if last_cut_end < len(podcast):
            non_ad_parts.append(podcast[last_cut_end:])

        if not non_ad_parts:
            print(f"警告：計算後沒有剩餘音訊片段，可能整個音檔都被標記為廣告。")
            return

        final_podcast = sum(non_ad_parts)
        final_podcast.export(output_mp3_path, format="mp3")
        print(f"背景任務：剪輯成功 -> {output_mp3_path.name}")

    except Exception as e:
        print(f"錯誤：在剪輯 {original_mp3_path.name} 過程中發生錯誤: {e}")

def task_download_from_rss(rss_url: str, num_to_download: Optional[int]):
    """
    (背景任務) 從 RSS Feed 下載 Podcast。
    """
    print(f"背景任務：開始從 {rss_url} 下載...")
    try:
        response = requests.get(rss_url, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        podcast_title = sanitize_filename(root.findtext('./channel/title', 'Untitled Podcast'))
        podcast_dir = BASE_DIR / podcast_title
        podcast_dir.mkdir(exist_ok=True)
        
        all_items = root.findall('./channel/item')
        items_to_process = all_items[:num_to_download] if num_to_download else all_items
        
        for item in items_to_process:
            ep_title = sanitize_filename(item.findtext('title', 'Untitled Episode'))
            enclosure = item.find('enclosure')
            if enclosure is None or 'url' not in enclosure.attrib:
                continue
            
            audio_url = enclosure.attrib['url']
            pub_date_str = item.findtext('pubDate', '')
            date_prefix = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d') if pub_date_str else 'NODATE'
            
            filename = f"{date_prefix} - {ep_title}.mp3"
            filepath = podcast_dir / filename
            
            if not filepath.exists():
                download_response = requests.get(audio_url, stream=True, timeout=30)
                download_response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"背景任務：下載成功 -> {filename}")
            else:
                print(f"資訊：檔案已存在，跳過下載 -> {filename}")

    except Exception as e:
        print(f"錯誤：在下載 {rss_url} 過程中發生錯誤: {e}")


# --- API 端點 (Endpoints) ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Podcast AI 處理器後端服務運行中！"}

@app.get("/podcasts", response_model=List[str])
def list_files():
    """
    (已修正) 遞迴地列出下載資料夾中所有的 .mp3 和 .json 檔案名稱。
    這將為前端提供一個完整的檔案列表。
    """
    if not BASE_DIR.exists():
        return []
    
    file_list = [p.name for p in BASE_DIR.rglob('*') if p.is_file() and p.suffix in ['.mp3', '.json']]
    return sorted(list(set(file_list)), reverse=True)

@app.post("/analyze", status_code=202)
def trigger_analysis(req: ProcessRequest, background_tasks: BackgroundTasks):
    """
    觸發一個非同步的背景任務來轉錄和分析指定的音檔。
    """
    audio_file_path = find_file(req.filename)
    if not audio_file_path:
        raise HTTPException(status_code=404, detail=f"檔案 '{req.filename}' 不存在。")

    # 建立一個完整的處理管線
    def full_analysis_pipeline():
        task_run_whisper_transcription(audio_file_path)
        transcript_path = audio_file_path.with_suffix(audio_file_path.suffix + ".json")
        if transcript_path.exists():
            task_analyze_transcript(transcript_path)

    background_tasks.add_task(full_analysis_pipeline)
    return {"message": f"分析任務已為 '{req.filename}' 在背景啟動。"}

@app.post("/splice", status_code=202, response_model=SpliceResponse)
def trigger_splicing(req: ProcessRequest, background_tasks: BackgroundTasks):
    """
    觸發一個非同步的背景任務來剪輯指定的音檔。
    """
    # 我們需要找到 .analysis.json 檔案來執行剪輯
    analysis_filename = req.filename + ".analysis.json"
    analysis_file_path = find_file(analysis_filename)

    if not analysis_file_path:
        raise HTTPException(status_code=404, detail=f"找不到分析檔 '{analysis_filename}'。請先執行分析。")

    background_tasks.add_task(task_splice_audio, analysis_file_path)
    
    output_filename = req.filename.replace('.mp3', '_no_ads.mp3')
    return {"output_filename": output_filename}

@app.post("/download", status_code=202)
def trigger_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    """
    觸發一個非同步的背景任務來從 RSS Feed 下載 Podcast。
    """
    if not req.rss_url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="無效的 RSS Feed URL。")
    
    background_tasks.add_task(task_download_from_rss, req.rss_url, req.num_episodes)
    return {"message": f"已開始從 '{req.rss_url}' 下載。"}

# --- 如何執行 ---
# 在終端機中，進入包含此 main.py 的 app 資料夾
# 執行指令: uvicorn main:app --reload
