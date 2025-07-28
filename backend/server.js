const express = require("express");
const cors = require("cors");
const fs = require("fs").promises;
const path = require("path");
const { exec } = require("child_process");
const util = require("util");
const execPromise = util.promisify(exec);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Serve today's events from scraped data
app.get("/api/events", async (req, res) => {
  try {
    const eventsFile = path.join(__dirname, "data", "latest_events.json");
    
    try {
      const data = await fs.readFile(eventsFile, "utf8");
      const events = JSON.parse(data);
      
      console.log(`✅ Serving ${events.length} scraped events`);
      res.json({
        success: true,
        data: events,
        source: "scraped",
        last_updated: events[0]?.scraped_at || new Date().toISOString()
      });
    } catch (fileError) {
      console.log("📄 No scraped data available, returning empty array");
      res.json({
        success: true,
        data: [],
        source: "none",
        message: "No events data available. Run the scraper to fetch today's events."
      });
    }
  } catch (error) {
    console.error("🔥 Error serving events:", error.message);
    res.status(500).json({ error: "Failed to serve events data" });
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