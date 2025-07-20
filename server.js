// server.js
const express = require("express");
const cors = require("cors");
const fetch = require("node-fetch");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;
const EDMTRAIN_API_KEY = process.env.EDMTRAIN_API_KEY;

app.use(cors());

// Test endpoint
app.get("/events", async (req, res) => {
  try {
    const lat = 40.7128;      // New York latitude
    const lon = -74.0060;     // New York longitude
    const radius = 50;        // 50-mile search radius
    const url = `https://api.edmtrain.com/events?lat=${lat}&lon=${lon}&radius=${radius}&client=${EDMTRAIN_API_KEY}`;

    console.log("🔍 Fetching EDMTrain data from:", url);

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`EDMTrain API error: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`✅ Found ${data.data?.length || 0} events`);
    res.json(data);
  } catch (error) {
    console.error("🔥 Error fetching EDMTrain data:", error.message);
    res.status(500).json({ error: "Failed to fetch EDMTrain data" });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
});



