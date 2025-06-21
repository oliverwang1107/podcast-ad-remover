#!/usr/bin/env python3
"""Podcast Ad Segment Detector

This script lets a user pick a downloaded‑podcast transcript (JSON produced by
Whisper or similar) from the ./podcast_downloads directory and sends the whole
transcript to Gemini 1.5 Flash via the Google AI Python SDK. The model is asked
to return a *pure* JSON object listing the start/end of every detected ad block
plus a short reason.  If no ads are found, it must return {"ads": []}.

Environment variables
---------------------
GOOGLE_API_KEY  – Your Google AI key (put it in a .env file or export it).

Usage
-----
$ python podcast_ads_detector.py

You will be prompted to pick a show folder and then a .json transcript inside
that folder.  The result is printed to stdout and also saved alongside the
transcript with the suffix .ads.json (so you never overwrite the original).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

BASE_DIR = Path("podcast_downloads")


# ──────────────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────────────

def error(msg: str, *, exit_: bool = False) -> None:
    """Print a bold red error message."""
    print(f"\033[91m❌ {msg}\033[0m")
    if exit_:
        sys.exit(1)


def pick_from_list(options: list[str], title: str) -> str | None:
    """Simple CLI selector – returns the chosen item or None."""
    if not options:
        error(f"在 {title!r} 中沒有可供選擇的項目。")
        return None
    print(f"\n--- {title} ---")
    for idx, opt in enumerate(options, 1):
        print(f"[{idx}] {opt}")
    try:
        choice = int(input("> 請輸入數字選擇: "))
        return options[choice - 1]
    except (ValueError, IndexError):
        error("選擇無效。")
        return None


def select_json_file() -> Path | None:
    """Interactive prompt allowing the user to pick the transcript to analyse."""
    if not BASE_DIR.exists() or not any(BASE_DIR.iterdir()):
        error(f"找不到 {BASE_DIR} 資料夾，或資料夾為空。", exit_=True)

    podcasts = [d.name for d in BASE_DIR.iterdir() if d.is_dir()]
    show = pick_from_list(podcasts, "請選擇要分析的 Podcast 節目")
    if not show:
        return None

    show_path = BASE_DIR / show
    json_files = [f.name for f in show_path.glob("*.json") if not f.name.endswith(".ads.json")]
    file_ = pick_from_list(json_files, f"請選擇 '{show}' 的一份逐字稿")
    if not file_:
        return None

    return show_path / file_


# ──────────────────────────────────────────────────────────────────────────────
# Core logic: talk to Gemini
# ──────────────────────────────────────────────────────────────────────────────

def compose_prompt(transcript_text: str) -> str:
    """Return the full prompt string we send to Gemini."""
    return f"""
你是一位專業的 Podcast 分析師，你的唯一任務是根據使用者提供的逐字稿，找出廣告時段，並以純粹的 JSON 格式回傳結果。

你的回覆**必須**是一個 JSON 物件，該物件只有一個名為 \"ads\" 的 key，其 value 是一個陣列。
陣列中的每個物件都代表一個廣告時段，並包含 'start_time' (秒), 'end_time' (秒), 和 'reason' (簡短原因)。
如果沒有廣告，\"ads\" 的 value 必須是一個空陣列 []。

### 範例輸出 (EXAMPLE OUTPUT) ###
```json
{{
  \"ads\": [
    {{
      \"start_time\": 1.50,
      \"end_time\": 97.00,
      \"reason\": \"由 Sharp 贊助，介紹新品家電。\"
    }}
  ]
}}
```

---
以下是逐字稿，請開始分析：
```text
{transcript_text}
```
"""


def analyse_transcript(path: Path) -> dict[str, Any] | None:
    """Run Gemini on the transcript and return the parsed JSON (or None)."""
    try:
        segments = json.loads(path.read_text(encoding="utf‑8"))
        transcript_text = "\n".join(f"[{s['start']:.2f}s - {s['end']:.2f}s] {s['text']}" for s in segments)
    except (json.JSONDecodeError, KeyError, OSError) as exc:
        error(f"讀取或解析 JSON 檔案時發生錯誤: {exc}")
        return None

    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        error("請在 .env 檔案中設定 GOOGLE_API_KEY", exit_=True)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = compose_prompt(transcript_text)
    print("\n⏳ 正在呼叫 Gemini API... 請稍候。")
    response = model.generate_content(prompt)

    if not response.text:
        error("Gemini 回傳空白內容。")
        return None

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as exc:
        error(f"Gemini 回傳結果無法解析為 JSON: {exc}\n原始內容如下:\n{response.text}")
        return None

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Script entrypoint
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    transcript_path = select_json_file()
    if not transcript_path:
        return

    result = analyse_transcript(transcript_path)
    if result is None:
        return

    print("\n🎉 分析完成，結果如下:\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    out_path = transcript_path.with_suffix(".ads.json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf‑8")
    print(f"\n💾 已將結果儲存至 {out_path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 已取消。再見！")
