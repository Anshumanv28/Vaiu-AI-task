const express = require("express");
const router = express.Router();
const { getWeatherForDate } = require("../services/weatherService");

/**
 * GET /api/weather/:date
 * Fetch weather forecast for a specific date
 * Date format: YYYY-MM-DD
 */
router.get("/:date", async (req, res) => {
  try {
    const { date } = req.params;
    const location = process.env.RESTAURANT_LOCATION || "Mumbai";

    // Validate date format
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return res.status(400).json({
        success: false,
        error: "Invalid date format. Use YYYY-MM-DD",
      });
    }

    const weatherData = await getWeatherForDate(date, location);

    res.json({
      success: true,
      data: weatherData,
    });
  } catch (error) {
    console.error("Weather route error:", error);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to fetch weather data",
    });
  }
});

module.exports = router;
