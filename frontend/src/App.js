import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css"; // Importing the CSS file

const TRADING_STRATEGIES = [
  {
    name: "Last X Candles",
    value: "LAST_X_CANDLES",
  },
  {
    name: "Moving Average",
    value: "MOVING_AVERAGE",
  },
];

function App() {
  const [tradingStrategy, setTradingStrategy] = useState(
    TRADING_STRATEGIES[0].value
  );
  const [ssid, setSsid] = useState("");
  const [candlesToCheck, setCandlesToCheck] = useState(7);
  const [timeframe, setTimeframe] = useState(30);
  const [botRunning, setBotRunning] = useState(false);
  const [fastPeriod, setFastPeriod] = useState(5);
  const [slowPeriod, setSlowPeriod] = useState(10);

  const BASE_HTTP_URL = "http://localhost:8000";

  useEffect(() => {
    const checkBotStatus = async () => {
      try {
        const response = await axios.get(BASE_HTTP_URL + "/bot-status");
        setBotRunning(response.data.bot_running);
      } catch (error) {
        console.error("Error checking bot status:", error.message);
      }
    };

    checkBotStatus();
  }, []);

  const startBot = async () => {
    try {
      const response = await axios.post(BASE_HTTP_URL + "/start-bot", {
        ssid,
        candles_to_check: candlesToCheck,
        timeframe,
        trading_strategy: tradingStrategy,
        fast_period: fastPeriod,
        slow_period: slowPeriod,
      });
      console.log(response.data);
      setBotRunning(true);
    } catch (error) {
      console.error(
        "Error starting bot:",
        error.response ? error.response.data.detail : error.message
      );
      alert(
        "Error starting bot: " + error.response
          ? error.response.data.detail
          : error.message
      );
    }
  };

  const stopBot = async () => {
    try {
      const response = await axios.post(BASE_HTTP_URL + "/stop-bot");
      console.log(response.data);
      setBotRunning(false);
    } catch (error) {
      console.error(
        "Error stopping bot:",
        error.response ? error.response.data.detail : error.message
      );
      alert(
        "Error stopping bot: " + error.response
          ? error.response.data.detail
          : error.message
      );
    }
  };

  return (
    <div className="App">
      <div className="container">
        <h1>Pocket Option Bot</h1>
        <div className="input-group">
          <label>
            Trading Strategy:
            <select
              value={tradingStrategy}
              onChange={(e) => setTradingStrategy(e.target.value)}
              disabled={botRunning}
            >
              {TRADING_STRATEGIES.map((ts) => (
                <option value={ts.value}>{ts.name}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="input-group">
          <label>SSID</label>
          <input
            type="text"
            value={ssid}
            onChange={(e) => setSsid(e.target.value)}
            disabled={botRunning}
          />
        </div>

        {tradingStrategy === "LAST_X_CANDLES" && (
          <div className="input-group">
            <label>Candles to Check</label>
            <input
              type="number"
              value={candlesToCheck}
              onChange={(e) => setCandlesToCheck(Number(e.target.value))}
              disabled={botRunning}
            />
          </div>
        )}

        {tradingStrategy === "MOVING_AVERAGE" && (
          <>
            <div className="input-group">
              <label>Fast Period</label>
              <input
                type="number"
                value={fastPeriod}
                onChange={(e) => setFastPeriod(Number(e.target.value))}
                disabled={botRunning}
              />
            </div>

            <div className="input-group">
              <label>Slow Period</label>
              <input
                type="number"
                value={slowPeriod}
                onChange={(e) => setSlowPeriod(Number(e.target.value))}
                disabled={botRunning}
              />
            </div>
          </>
        )}

        <div className="input-group">
          <label>Timeframe</label>
          <input
            type="number"
            value={timeframe}
            onChange={(e) => setTimeframe(Number(e.target.value))}
            disabled={botRunning}
          />
        </div>
        <button
          className={`btn ${botRunning ? "stop" : "start"}`}
          onClick={botRunning ? stopBot : startBot}
        >
          {botRunning ? "Stop Bot" : "Start Bot"}
        </button>
      </div>
    </div>
  );
}

export default App;
