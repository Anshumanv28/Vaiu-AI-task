const express = require("express");
const router = express.Router();
const { getWeatherForDate } = require("../services/weatherService");

/**
 * GET /api/weather/:date
 * Fetch weather forecast for a specific date and optionally time
 * Date format: YYYY-MM-DD
 * Query param: time (optional) - HH:mm format (24-hour, e.g., "19:00")
 */
router.get("/:date", async (req, res) => {
  const startTime = Date.now();
  console.log(`🌐 [BACKEND] GET /api/weather/:date`);
  console.log(
    `📦 [BACKEND] Params: date=${req.params.date}, time=${
      req.query.time || "none"
    }`
  );

  try {
    const { date } = req.params;
    const { time } = req.query; // Optional time parameter
    const location = process.env.RESTAURANT_LOCATION || "Mumbai";

    // Validate date format
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return res.status(400).json({
        success: false,
        error: "Invalid date format. Use YYYY-MM-DD",
      });
    }

    // Validate time format if provided
    if (time && !/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/.test(time)) {
      return res.status(400).json({
        success: false,
        error: "Invalid time format. Use HH:mm (24-hour format)",
      });
    }

    const weatherData = await getWeatherForDate(date, location, time);
    const duration = Date.now() - startTime;

    console.log(`✅ [BACKEND] Weather fetched successfully in ${duration}ms`);
    console.log(
      `🌤️ [BACKEND] Weather result:`,
      JSON.stringify(weatherData, null, 2)
    );

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
