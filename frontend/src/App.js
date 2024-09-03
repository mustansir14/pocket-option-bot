import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';  // Importing the CSS file

function App() {
  const [ssid, setSsid] = useState('');
  const [candlesToCheck, setCandlesToCheck] = useState(7);
  const [timeframe, setTimeframe] = useState(30);
  const [botRunning, setBotRunning] = useState(false);
  
  const BASE_HTTP_URL = "http://localhost:8000";

  useEffect(() => {
    const checkBotStatus = async () => {
      try {
        const response = await axios.get(BASE_HTTP_URL + '/bot-status');
        setBotRunning(response.data.bot_running);
      } catch (error) {
        console.error("Error checking bot status:", error.message);
      }
    };

    checkBotStatus();
  }, []);

  const startBot = async () => {
    try {
      const response = await axios.post(BASE_HTTP_URL + '/start-bot', {
        ssid,
        candles_to_check: candlesToCheck,
        timeframe
      });
      console.log(response.data);
      setBotRunning(true);
    } catch (error) {
      console.error("Error starting bot:", error.response ? error.response.data.detail : error.message);
      alert("Error starting bot: " + error.response ? error.response.data.detail : error.message);
    }
  };

  const stopBot = async () => {
    try {
      const response = await axios.post(BASE_HTTP_URL + '/stop-bot');
      console.log(response.data);
      setBotRunning(false);
    } catch (error) {
      console.error("Error stopping bot:", error.response ? error.response.data.detail : error.message);
      alert("Error stopping bot: " + error.response ? error.response.data.detail : error.message);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <h1>Pocket Option Bot</h1>
        <div className="input-group">
          <label>
            SSID:
            <input
              type="text"
              value={ssid}
              onChange={(e) => setSsid(e.target.value)}
              disabled={botRunning}
            />
          </label>
        </div>
        <div className="input-group">
          <label>
            Candles to Check:
            <input
              type="number"
              value={candlesToCheck}
              onChange={(e) => setCandlesToCheck(Number(e.target.value))}
              disabled={botRunning}
            />
          </label>
        </div>
        <div className="input-group">
          <label>
            Timeframe (in seconds):
            <input
              type="number"
              value={timeframe}
              onChange={(e) => setTimeframe(Number(e.target.value))}
              disabled={botRunning}
            />
          </label>
        </div>
        <button className={`btn ${botRunning ? 'stop' : 'start'}`} onClick={botRunning ? stopBot : startBot}>
          {botRunning ? 'Stop Bot' : 'Start Bot'}
        </button>
      </div>
    </div>
  );
}

export default App;
