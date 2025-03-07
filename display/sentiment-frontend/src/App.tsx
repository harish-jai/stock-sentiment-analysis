import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const API_BASE = import.meta.env.REACT_APP_API_BASE || "http://localhost:5000";
console.log(API_BASE);

interface Ticker {
  ticker: string;
}

interface SentimentData {
  subreddit: string;
  sentiment: number;
  calculated_at: string;
}

function App() {
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);

  useEffect(() => {
    axios.get<Ticker[]>(`${API_BASE}/tickers`).then((res) => setTickers(res.data));
  }, []);

  useEffect(() => {
    if (selectedTicker) {
      axios.get<SentimentData[]>(`${API_BASE}/sentiment/${selectedTicker}`)
        .then((res) => setSentimentData(res.data));
    }
    console.log(selectedTicker);
  }, [selectedTicker]);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-2xl font-bold mb-4">📊 Sentiment Dashboard</h1>
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

      {sentimentData.length > 0 && (
        <div className="mt-6 grid grid-cols-2 gap-6">
          {/* Left Panel: Aggregate Sentiment */}
          <div className="bg-gray-800 p-4 rounded-lg">
            <h2 className="text-lg font-semibold">📈 Aggregate Sentiment</h2>
            <p className="text-4xl font-bold">
              {sentimentData[0].sentiment.toFixed(2)}
            </p>
            <p>Last updated: {new Date(sentimentData[0].calculated_at).toLocaleString()}</p>

            <LineChart width={400} height={200} data={[...sentimentData].reverse()}>
              <CartesianGrid stroke="#ccc" />
              <XAxis dataKey="calculated_at" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="sentiment" stroke="#82ca9d" />
            </LineChart>
          </div>

          {/* Right Panel: Sentiment Per Subreddit */}
          <div className="bg-gray-800 p-4 rounded-lg">
            <h2 className="text-lg font-semibold">💬 Sentiment Per Subreddit</h2>
            {sentimentData.map((s) => (
              <div key={s.subreddit} className="mt-2 p-2 bg-gray-700 rounded">
                <p className="font-semibold">{s.subreddit}</p>
                <p>Sentiment: {s.sentiment.toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
