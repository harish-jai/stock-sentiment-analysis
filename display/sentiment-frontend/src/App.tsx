import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";
console.log(API_BASE);

interface Ticker {
  ticker: string;
}

interface Subreddit {
  subreddit: string;
}

interface SentimentData {
  sentiment: number;
  calculated_at: string;
  date_str: string;
}

type SentimentMap = Record<string, Record<string, number>>; // { subreddit: { timestamp: sentiment } }

function App() {
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [subreddits, setSubreddits] = useState<Subreddit[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [sentimentMap, setSentimentMap] = useState<SentimentMap>({});

  useEffect(() => {
    axios.get<Ticker[]>(`${API_BASE}/tickers`).then((res) => setTickers(res.data));
  }, []);

  useEffect(() => {
    axios.get<Subreddit[]>(`${API_BASE}/subreddits`).then((res) => {
      setSubreddits(res.data);
    });
  }, []);

  useEffect(() => {
    if (!selectedTicker || subreddits.length === 0) return;

    const fetchSentimentData = async () => {
      const sentimentDataMap: SentimentMap = {};

      await Promise.all(
        subreddits.map(async (sub) => {
          try {
            const res = await axios.get<SentimentData[]>(`${API_BASE}/sentiment/${selectedTicker}/${sub.subreddit}`);
            sentimentDataMap[sub.subreddit] = res.data
              .filter(entry => entry.date_str !== null) // Filter out entries with null date
              .reduce((acc, entry) => {
                acc[entry.date_str] = entry.sentiment;
                return acc;
              }, {} as Record<string, number>);
          } catch (error) {
            console.error(`Error fetching sentiment for ${sub.subreddit}:`, error);
          }
        })
      );

      setSentimentMap(sentimentDataMap);
      console.log(sentimentDataMap);
    };

    fetchSentimentData();
  }, [selectedTicker, subreddits]);

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">Moodi: Stock Sentiment Dashboard</h1>

      {/* Radio buttons to select ticker */}
      <div className="ticker-selection">
        {tickers.map((t) => (
          <label key={t.ticker} className="ticker-label">
            <input
              type="radio"
              name="ticker"
              value={t.ticker}
              onChange={() => setSelectedTicker(t.ticker)}
              className="ticker-radio"
            />
            <span>{t.ticker}</span>
          </label>
        ))}
      </div>

      {/* Display sentiment data for subreddit "all" */}
      {sentimentMap["all"] && Object.keys(sentimentMap["all"]).length > 0 && (
        <div className="sentiment-card">
          <h2 className="sentiment-title">📈 All Subreddits Sentiment</h2>
          <LineChart width={800} height={400} data={Object.entries(sentimentMap["all"]).map(([timestamp, sentiment]) => ({
            calculated_at: new Date(timestamp).toLocaleString(),
            sentiment,
          }))}>
            <CartesianGrid stroke="#ccc" />
            <XAxis dataKey="calculated_at" tick={{ fontSize: 10 }} />
            <YAxis />
            <Tooltip formatter={(value, _, props) => [`Sentiment: ${value}`, `Date: ${props.payload.calculated_at}`]} />
            <Line type="monotone" dataKey="sentiment" stroke="#82ca9d" dot={false} />
          </LineChart>
        </div>
      )}

      {/* Display sentiment time series per subreddit except for "all" */}
      <div className="sentiment-grid">
        {Object.entries(sentimentMap).map(([subreddit, data]) => {
          if (subreddit === "all") return null;
          const chartData = Object.entries(data).map(([timestamp, sentiment]) => ({
            calculated_at: new Date(timestamp).toLocaleString(),
            sentiment,
          }));

          return (
            <div key={subreddit} className="sentiment-card">
              <h2 className="sentiment-title">📈 {subreddit} Sentiment</h2>
              <LineChart width={400} height={200} data={chartData}>
                <CartesianGrid stroke="#ccc" />
                <XAxis dataKey="calculated_at" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip formatter={(value, _, props) => [`Sentiment: ${value}`, `Date: ${props.payload.calculated_at}`]} />
                <Line type="monotone" dataKey="sentiment" stroke="#82ca9d" dot={false}/>
              </LineChart>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;
