// frontend/src/App.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // 我們稍後會修改樣式

function App() {
  // 使用 state 來儲存從後端拿到的節目列表
  const [podcasts, setPodcasts] = useState([]);
  // 儲存錯誤訊息或載入狀態
  const [message, setMessage] = useState('正在從後端載入節目列表...');

  // useEffect 會在元件第一次載入時執行
  useEffect(() => {
    // 定義一個非同步函式來取得資料
    const fetchPodcasts = async () => {
      try {
        // 使用 axios 向我們的 FastAPI 後端發送請求
        // 注意：API 的 URL 是 http://127.0.0.1:8000
        const response = await axios.get('http://127.0.0.1:8000/podcasts');
        
        // 如果成功，將回傳的資料設定到 state 中
        setPodcasts(response.data);
        setMessage(''); // 清空訊息
      } catch (error) {
        // 如果失敗 (例如後端沒開)，顯示錯誤訊息
        console.error("無法連接到後端:", error);
        setMessage('❌ 無法連接到後端伺服器。請確認 FastAPI 服務 (uvicorn) 正在運行中。');
      }
    };

    // 呼叫這個函式
    fetchPodcasts();
  }, []); // 空的依賴陣列 [] 表示這個 effect 只會執行一次

  return (
    <div className="container">
      <h1>🎙️ AI Podcast 工具</h1>
      <div className="card">
        <h2>已下載的節目</h2>
        {message ? (
          <p className="message">{message}</p>
        ) : (
          <ul>
            {podcasts.map((podcast, index) => (
              <li key={index}>{podcast}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App;
