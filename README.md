# Podcast Ad Remover 使用說明
(English README available in README_EN.md)

本專案提供一系列 Python 腳本，協助你下載 Podcast 節目、轉錄音檔並分析其中的廣告段落。建議透過 Docker 容器執行，以免安裝複雜的依賴套件。

## 先決條件

- **Docker** 與 **Docker Compose**（推薦）
- 若要在本機執行腳本，需自行安裝 Python 3.10 以上版本以及 `requirements.txt` 中列出的套件

## 快速開始

1. 下載或複製此專案。
2. 在 `app/` 目錄建立 `.env` 檔案，填入所需的 API 金鑰，例如：
   ```env
   OPENAI_API_KEY=your_openai_key
   GROQ_API_KEY=your_groq_key
   GOOGLE_API_KEY=your_google_api_key
   OPENROUTER_API_KEY=your_openrouter_key
   AI_MODEL_NAME=deepseek/deepseek-r1-0528:free
   ```
3. 於專案根目錄執行：
   ```bash
   docker compose up --build
   ```
   進入容器後即可互動式地執行各種 Python 腳本。

若不使用 Docker，可改在本機執行 `pip install -r requirements.txt` 後直接呼叫腳本。

## 主要腳本簡介

- **`podcast_downloader.py`**：根據 RSS Feed 下載 Podcast 音檔。
- **`transcribe_local.py`**：使用開源 Whisper 模型在本機轉錄 MP3。
- **`groq_api.py`**：透過 Groq API 進行高速轉錄。
- **`test_whisper_interactive.py`**：使用 OpenAI Whisper API 轉錄並自動壓縮檔案。
- **`compress_mp3.py`**：將 MP3 壓縮至約 24.5MB，方便上傳。
- **`google_API.py`**：利用 Google Gemini 分析逐字稿，找出廣告時段。
- **`test_gemma_analyze.py`**：使用 OpenRouter 上的模型分析廣告。

所有腳本皆位於 `app/` 目錄，執行方式如下：
```bash
python script_name.py
```
執行過程會以互動式選單引導你選擇檔案或輸入參數。

## 資料儲存

下載的 Podcast 與產生的逐字稿都會放在 `podcast_downloads/` 目錄。此資料夾已在 `.gitignore` 中排除，不會被提交到版本庫。

## 授權

本專案以 MIT 授權釋出，詳見 `LICENSE` 檔案（若存在）。
