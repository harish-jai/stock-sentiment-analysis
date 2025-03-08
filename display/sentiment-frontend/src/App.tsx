import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

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
    axios.get<Subreddit[]>(`${API_BASE}/subreddits`).then((res) => setSubreddits(res.data));
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
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-2xl font-bold mb-4">📊 Sentiment Dashboard</h1>

      {/* Dropdown to select ticker */}
      <select
        className="p-2 rounded bg-gray-700"
        onChange={(e) => setSelectedTicker(e.target.value)}
      >
        <option value="">Select a ticker</option>
        {tickers.map((t) => (
          <option key={t.ticker} value={t.ticker}>
            {t.ticker}
          </option>
        ))}
      </select>

      {/* Display sentiment time series per subreddit */}
      <div className="mt-6 grid grid-cols-2 gap-6">
        {Object.entries(sentimentMap).map(([subreddit, data]) => {
          const chartData = Object.entries(data).map(([timestamp, sentiment]) => ({
            calculated_at: new Date(timestamp).toLocaleString(),
            sentiment,
          }));

          return (
            <div key={subreddit} className="bg-gray-800 p-4 rounded-lg">
              <h2 className="text-lg font-semibold">📈 {subreddit} Sentiment</h2>
              <LineChart width={400} height={200} data={chartData}>
                <CartesianGrid stroke="#ccc" />
                <XAxis dataKey="calculated_at" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="sentiment" stroke="#82ca9d" />
              </LineChart>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;
