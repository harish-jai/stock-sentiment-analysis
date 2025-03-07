require('dotenv').config({ path: "/home/harishj/stock-sentiment-analysis/stock-sentiment-analysis/.env" });
const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
app.use(cors());
app.use(express.json());

// PostgreSQL connection
const pool = new Pool({
    connectionString: process.env.NEON_CONNECTION_STRING,
    ssl: { rejectUnauthorized: false },
});

// Fetch available tickers
app.get('/tickers', async (req, res) => {
    try {
        const result = await pool.query('SELECT DISTINCT ticker FROM ticker_sentiment');
        res.json(result.rows);
        console.log(result.rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Fetch available subreddits
app.get('/subreddits', async (req, res) => {
    try {
        const result = await pool.query('SELECT DISTINCT subreddit FROM ticker_sentiment');
        res.json(result.rows);
        console.log(result.rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Fetch sentiment data for a specific ticker
app.get('/sentiment/:ticker', async (req, res) => {
    try {
        const { ticker } = req.params;
        const result = await pool.query(
            'SELECT * FROM ticker_sentiment WHERE ticker = $1 ORDER BY calculated_at DESC',
            [ticker]
        );
        res.json(result.rows);
        console.log(result.rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Fetch data based on ticker and subreddit
app.get('/sentiment/:ticker/:subreddit', async (req, res) => {
    try {
        const { ticker, subreddit } = req.params;
        const search_key = `${ticker}_${subreddit}`;
        const result = await pool.query(
            'SELECT * FROM ticker_sentiment WHERE id=$1 ORDER BY calculated_at DESC',
            [search_key]
        );
        res.json(result.rows);
        console.log(result.rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
console.log('Connection String:', process.env.NEON_CONNECTION_STRING);
