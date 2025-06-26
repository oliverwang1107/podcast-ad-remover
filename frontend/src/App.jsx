// frontend/src/App.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // 我們稍後會修改樣式

function App() {
  // 使用 state 來儲存從後端拿到的節目列表
  const [podcasts, setPodcasts] = useState([]);
  // 儲存錯誤訊息或載入狀態
  const [message, setMessage] = useState('正在從後端載入節目列表...');
  // 新增一個 state 來追蹤正在處理的檔案，防止重複點擊
  const [processingFile, setProcessingFile] = useState(null);

  // 將 fetchPodcasts 獨立出來，以便重複使用
  const fetchPodcasts = async () => {
    try {
      // 使用 axios 向我們的 FastAPI 後端發送請求
      const response = await axios.get('http://127.0.0.1:8000/podcasts');
      
      // 如果成功，將回傳的資料設定到 state 中
      setPodcasts(response.data);
      // 避免清除操作過程中的狀態訊息
      if (message.startsWith('正在從後端載入')) {
        setMessage('');
      }
    } catch (error) {
      // 如果失敗 (例如後端沒開)，顯示錯誤訊息
      console.error("無法連接到後端:", error);
      setMessage('❌ 無法連接到後端伺服器。請確認 FastAPI 服務 (uvicorn) 正在運行中。');
    }
  };

  // useEffect 會在元件第一次載入時執行
  useEffect(() => {
    fetchPodcasts();
  }, []); // 空的依賴陣列 [] 表示這個 effect 只會執行一次

  // 新增：處理分析請求的函式
  const handleAnalyze = async (podcastName) => {
    setProcessingFile(podcastName);
    setMessage(`⏳ 正在分析 ${podcastName}，這可能需要幾分鐘...`);
    try {
      // 假設後端有 /analyze 端點來處理分析請求
      await axios.post('http://127.0.0.1:8000/analyze', { filename: podcastName });
      setMessage(`✅ ${podcastName} 分析完成！`);
      fetchPodcasts(); // 重新整理列表以顯示新產生的 .json 檔案
    } catch (error) {
      console.error(`分析 ${podcastName} 失敗:`, error);
      setMessage(`❌ 分析 ${podcastName} 失敗。詳情請查看後端日誌。`);
    } finally {
      setProcessingFile(null);
    }
  };

  // 新增：處理剪輯請求的函式
  const handleSplice = async (podcastName) => {
    setProcessingFile(podcastName);
    setMessage(`⏳ 正在為 ${podcastName} 移除廣告...`);
    try {
      // 假設後端有 /splice 端點來處理剪輯請求
      const response = await axios.post('http://127.0.0.1:8000/splice', { filename: podcastName });
      setMessage(`✅ 廣告移除完成！新檔案：${response.data.output_filename}`);
      fetchPodcasts(); // 重新整理列表以顯示移除廣告後的新檔案
    } catch (error) {
      console.error(`移除廣告 ${podcastName} 失敗:`, error);
      setMessage(`❌ 移除廣告 ${podcastName} 失敗。請先確認分析已完成。`);
    } finally {
      setProcessingFile(null);
    }
  };

  return (
    <div className="container">
      <h1>🎙️ AI Podcast 工具</h1>
      <div className="card">
        <h2>已下載的節目</h2>
        {/* 將訊息顯示移到列表外部，使其成為一個全域狀態顯示 */}
        {message && <p className="message">{message}</p>}
        <ul>
          {podcasts.map((podcast, index) => (
            <li key={index}>
              <span>{podcast}</span>
              {/* 為 .mp3 檔案加上操作按鈕 */}
              {podcast.endsWith('.mp3') && (
                <div style={{ display: 'inline-block', marginLeft: '1rem' }}>
                  <button
                    onClick={() => handleAnalyze(podcast)}
                    disabled={!!processingFile}
                  >
                    {processingFile === podcast ? '分析中...' : '1. 分析廣告'}
                  </button>
                  <button
                    onClick={() => handleSplice(podcast)}
                    disabled={!!processingFile}
                    style={{ marginLeft: '0.5rem' }}
                  >
                    {processingFile === podcast ? '處理中...' : '2. 移除廣告'}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
