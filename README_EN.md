# Podcast Ad Remover Guide

This project provides a collection of Python scripts that help you download podcast episodes, transcribe audio and detect advertisement segments. It is recommended to run them in a Docker container to avoid complex dependency installation.

## Prerequisites

- **Docker** and **Docker Compose** (recommended)
- To run directly on your machine, install Python 3.10 or higher plus all packages listed in `requirements.txt`.

## Quick Start

1. Download or clone this repository.
2. In the `app/` folder create a `.env` file with your API keys, for example:
   ```env
   OPENAI_API_KEY=your_openai_key
   GROQ_API_KEY=your_groq_key
   GOOGLE_API_KEY=your_google_api_key
   OPENROUTER_API_KEY=your_openrouter_key
   AI_MODEL_NAME=deepseek/deepseek-r1-0528:free
   ```
3. From the project root run:
   ```bash
   docker compose up --build
   ```
   After entering the container you can interactively run the Python scripts.

If you do not use Docker, run `pip install -r requirements.txt` and call the scripts directly.

## Main Scripts

- **`podcast_downloader.py`**: Download podcast audio based on an RSS feed.
- **`transcribe_local.py`**: Transcribe MP3 files locally using the open-source Whisper model.
- **`groq_api.py`**: Perform high-speed transcription via Groq API.
- **`test_whisper_interactive.py`**: Use the OpenAI Whisper API and automatically compress files.
- **`compress_mp3.py`**: Compress MP3s to about 24.5 MB for easier upload.
- **`google_API.py`**: Analyze transcripts with Google Gemini to find ad segments.
- **`test_gemma_analyze.py`**: Analyze ads using a model from OpenRouter.

All scripts live in the `app/` folder and can be run as follows:
```bash
python script_name.py
```
An interactive menu will ask you to choose files or enter parameters.

## Data Storage

Downloaded podcasts and transcripts are stored under `podcast_downloads/`. This directory is listed in `.gitignore` and won't be committed to the repository.

## License

This project is released under the MIT License. See `LICENSE` for details, if present.
