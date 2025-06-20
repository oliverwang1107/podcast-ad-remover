# 使用官方的 Python 3.10 slim 作為基礎映像檔
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴，特別是 ffmpeg，pydub 會需要它
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 檔案到工作目錄
COPY requirements.txt .

# 安裝 Python 依賴
# --no-cache-dir 可以讓映像檔小一點
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式的其餘程式碼到工作目錄
COPY . .

# 當容器啟動時，預設執行的指令
CMD ["python", "main.py"]