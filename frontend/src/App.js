import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css"; // Importing the CSS file

const TRADING_STRATEGIES = [
  {
    name: "Moving Average",
    value: "MOVING_AVERAGE",
  },
  {
    name: "Last X Candles",
    value: "LAST_X_CANDLES",
  },
];

const ORDER_ACTIONS = [
  {
    name: "Telegram Signal",
    value: "TELEGRAM_SIGNAL",
  },
  {
    name: "Order Execution",
    value: "ORDER_EXECUTION",
  },
];

const BOT_TYPES = [
  {
    name: "Pocket Option",
    value: "POCKET_OPTION",
  },
  {
    name: "IQ Option",
    value: "IQ_OPTION",
  },
];

function App() {
  const [orderAction, setOrderAction] = useState(
    ORDER_ACTIONS[0].value
  );
  const [tradingStrategy, setTradingStrategy] = useState(
    TRADING_STRATEGIES[0].value
  );
  const [botType, setBotType] = useState(BOT_TYPES[0].value);
  const [ssid, setSsid] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
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
      // Build connection_info based on bot type
      let connectionInfo = {};
      if (botType === "POCKET_OPTION") {
        connectionInfo = { ssid: ssid };
      } else if (botType === "IQ_OPTION") {
        connectionInfo = { username: username, password: password };
      }

      const response = await axios.post(BASE_HTTP_URL + "/start-bot", {
        bot_type: botType,
        connection_info: connectionInfo,
        candles_to_check: candlesToCheck,
        timeframe,
        trading_strategy: tradingStrategy,
        fast_period: fastPeriod,
        slow_period: slowPeriod,
        order_action: orderAction,
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
            Bot Type:
            <select
              value={botType}
              onChange={(e) => setBotType(e.target.value)}
              disabled={botRunning}
            >
              {BOT_TYPES.map((bt) => (
                <option key={bt.value} value={bt.value}>{bt.name}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="input-group">
          <label>
            Order Action
            <select
              value={orderAction}
              onChange={(e) => setOrderAction(e.target.value)}
              disabled={botRunning}
            >
              {ORDER_ACTIONS.map((oa) => (
                <option key={oa.value} value={oa.value}>{oa.name}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="input-group">
          <label>
            Trading Strategy:
            <select
              value={tradingStrategy}
              onChange={(e) => setTradingStrategy(e.target.value)}
              disabled={botRunning}
            >
              {TRADING_STRATEGIES.map((ts) => (
                <option key={ts.value} value={ts.value}>{ts.name}</option>
              ))}
            </select>
          </label>
        </div>
        
        {botType === "POCKET_OPTION" && (
          <div className="input-group">
            <label>SSID</label>
            <input
              type="text"
              value={ssid}
              onChange={(e) => setSsid(e.target.value)}
              disabled={botRunning}
            />
          </div>
        )}

        {botType === "IQ_OPTION" && (
          <>
            <div className="input-group">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={botRunning}
              />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={botRunning}
              />
            </div>
          </>
        )}

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
