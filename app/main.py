# app/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List

# --- 初始化 FastAPI 應用 ---
app = FastAPI(
    title="Podcast AI Processor API",
    description="處理 Podcast 下載、轉錄、分析與剪輯的後端服務。",
    version="0.1.0",
)

# --- 設定 CORS (跨來源資源共用) ---
# 這非常重要，它允許我們的 React 前端 (未來會在不同埠號) 與後端 API 溝通
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在開發中允許所有來源，未來可以收緊
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 資料夾路徑設定 ---
BASE_DIR = Path.home() / "podcast-ad-remover" / "podcast_downloads"


# --- API 端點 (Endpoints) ---

@app.get("/")
def read_root():
    """
    根目錄端點，用來確認伺服器是否正在運行。
    """
    return {"status": "ok", "message": "Podcast AI 處理器後端服務運行中！"}


@app.get("/podcasts", response_model=List[str])
def list_podcasts():
    """
    列出所有已下載的 Podcast 節目資料夾名稱。
    """
    if not BASE_DIR.exists():
        raise HTTPException(status_code=404, detail="下載資料夾不存在。")
    
    try:
        podcasts = [d.name for d in BASE_DIR.iterdir() if d.is_dir()]
        return podcasts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取節目列表時發生錯誤: {e}")

# ... 未來我們會在這裡加入更多強大的 API 端點 ...
# 例如：
# @app.post("/process/transcribe")
# def transcribe_episode(file_path: str):
#     # 這裡會呼叫 whisper.cpp 的邏輯
#     pass
#
# @app.post("/process/analyze")
# def analyze_transcript(transcript_path: str):
#     # 這裡會呼叫 Gemini API 的邏輯
#     pass
