# Podcast AI Processor

A tool to download, transcribe, analyze, and manage podcast episodes.

## Features

*   **Podcast Downloading**: Download episodes from RSS feeds.
*   **Audio Transcription**:
    *   Local `whisper.cpp` (CPU-based).
    *   Groq API (cloud-based, ultra-fast).
*   **Ad Segment Detection**: Uses Google Gemini API to identify ad segments in transcripts.
*   **MP3 Compression**: Reduce MP3 file sizes.
*   **Backend**: Built with FastAPI.
*   **Frontend**: User interface built with React.

## Project Structure

*   `app/`: Contains the Python backend code.
    *   `main.py`: FastAPI application entry point.
    *   `podcast_downloader.py`: Script to download podcast episodes.
    *   `run_whisper_cpp.py`: Script for local transcription using `whisper.cpp`.
    *   `groq_api.py`: Script for transcription using Groq API.
    *   `google_API.py`: Script for ad analysis using Google Gemini API.
    *   `compress_mp3.py`: Script for compressing MP3 files.
*   `frontend/`: Contains the React frontend code.
*   `podcast_downloads/`: Default directory where downloaded and processed podcast files are stored (created automatically).
*   `requirements.txt`: Python dependencies for the backend.
*   `docker-compose.yml`: For running the application using Docker.
*   `.env.example`: Example file for environment variables (you should create a `.env` file).

## Getting Started

### Prerequisites

*   Python 3.7+
*   Node.js and npm (for the frontend)
*   Docker and Docker Compose (optional, for containerized setup)
*   `ffmpeg` (required by `pydub` for audio processing, and `whisper.cpp`)

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory by copying `.env.example` (if it exists, otherwise create a new one with the content below). Add the following keys if you plan to use the respective services:
    ```env
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    GROQ_API_KEY="YOUR_GROQ_API_KEY"
    ```
    An example file `app/.env.example` is provided in the `app` directory, you can copy it to the root directory as `.env`.


5.  **Set up `whisper.cpp` (for local transcription):**
    *   Ensure `ffmpeg` is installed and accessible in your PATH (required by `whisper.cpp` for audio processing).
    *   Clone the `whisper.cpp` repository:
        ```bash
        git clone https://github.com/ggerganov/whisper.cpp.git ~/whisper.cpp
        ```
    *   Follow the `whisper.cpp` instructions to compile it (typically involves running `make`).
    *   Download the desired model (e.g., `bash ./models/download-ggml-model.sh base`). The scripts assume models are in `~/whisper.cpp/models/`.
    *   Ensure `ffmpeg` is installed and accessible in your PATH.

6.  **Run the backend server:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The API documentation will be available at `http://localhost:8000/docs`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install npm dependencies:**
    ```bash
    npm install
    ```

3.  **Run the frontend development server:**
    ```bash
    npm run dev
    ```
    The frontend will usually be available at `http://localhost:5173`.

### Docker Setup

1.  Ensure Docker and Docker Compose are installed.
2.  Make sure you have a `.env` file with necessary API keys in the root directory.
3.  Build and run the services:
    ```bash
    docker-compose up --build
    ```
    This will start the backend (port 8000) and frontend (port 5173).

## Usage

The application is designed to be used through its various components:

*   **Backend API**: The FastAPI server provides endpoints for various operations. You can explore these via the auto-generated docs at `http://localhost:8000/docs` when the server is running.
*   **Command-line Scripts**: The `app/` directory contains several standalone Python scripts that can be run directly for specific tasks:
    *   `python app/podcast_downloader.py`: Interactively download podcast episodes.
    *   `python app/compress_mp3.py`: Interactively select and compress an MP3 file.
    *   `python app/run_whisper_cpp.py`: Interactively select an MP3 and transcribe it using local `whisper.cpp`.
    *   `python app/groq_api.py`: Interactively select an MP3 and transcribe it using the Groq API.
    *   `python app/google_API.py`: Interactively select a JSON transcript and analyze it for ad segments using Gemini.
*   **Frontend Application**: Once the frontend and backend are running, you can access the user interface in your browser (typically `http://localhost:5173`).

## Future Enhancements

*   Integrate the individual script functionalities into the FastAPI backend with dedicated API endpoints.
*   Develop the frontend to consume these API endpoints for a seamless user experience.
*   Implement a database to store podcast metadata, transcripts, and analysis results.
*   Add more sophisticated ad detection techniques.
*   Support for more audio formats.
*   User authentication and management.

---

_This README was partially generated by an AI assistant._
