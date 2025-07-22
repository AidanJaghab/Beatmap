const express = require("express");
const cors = require("cors");
const fs = require("fs").promises;
const path = require("path");
const { exec } = require("child_process");
const util = require("util");
const execPromise = util.promisify(exec);

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Serve today's events from GitHub
app.get("/api/events", async (req, res) => {
  try {
    const githubUrl = "https://raw.githubusercontent.com/AidanJaghab/Beatmap/main/backend/data/latest_events.json";
    
    const response = await fetch(githubUrl);
    
    if (!response.ok) {
      console.log("📄 No GitHub data available, returning empty array");
      return res.json([]);
    }
    
    const events = await response.json();
    
    console.log(`✅ Serving ${events.length} events from GitHub`);
    
    // If it's a list, return it directly
    if (Array.isArray(events)) {
      return res.json(events);
    }
    
    // If it's a dict, fallback to "events" key
    return res.json(events.events || []);
    
  } catch (error) {
    console.error("🔥 Error fetching from GitHub:", error.message);
    res.status(500).json({ error: "Failed to fetch events data from GitHub" });
  }
});

// Endpoint to trigger scraping
app.post("/api/scrape", async (req, res) => {
  try {
    console.log("🔄 Running EDMTrain scraper...");
    
    const { stdout, stderr } = await execPromise("python3 scraper.py");
    
    if (stderr) {
      console.error("Scraper stderr:", stderr);
    }
    
    console.log("Scraper output:", stdout);
    
    const eventsFile = path.join(__dirname, "data", "latest_events.json");
    const data = await fs.readFile(eventsFile, "utf8");
    const events = JSON.parse(data);
    
    res.json({
      success: true,
      message: "Scraping completed successfully",
      events_count: events.length,
      data: events
    });
  } catch (error) {
    console.error("🔥 Error running scraper:", error.message);
    res.status(500).json({ 
      error: "Failed to run scraper",
      details: error.message 
    });
  }
});

// Health check endpoint
app.get("/api/health", (req, res) => {
  res.json({ 
    status: "healthy",
    service: "EDMTrain NYC Event Scraper",
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
});