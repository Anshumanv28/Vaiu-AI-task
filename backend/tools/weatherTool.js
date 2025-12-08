/**
 * Weather checking tool
 */
const { getWeatherForDate } = require("../services/weatherService");

/**
 * Check weather for a specific date and optionally time
 * @param {Object} params - Tool parameters
 * @param {string} params.date - Date in YYYY-MM-DD format
 * @param {string} [params.time] - Time in HH:mm format (24-hour, e.g., "19:00" for 7 PM)
 * @param {string} [params.location] - Location (defaults to RESTAURANT_LOCATION or "Mumbai")
 * @returns {Promise<Object>} Weather data with condition, temperature, description
 */
const execute = async (params) => {
  console.log(`🔧 [WEATHER_TOOL] Starting weather check`);
  console.log(`📦 [WEATHER_TOOL] Params:`, JSON.stringify(params, null, 2));

  try {
    const { date, time, location } = params;

    if (!date) {
      const error = "Date parameter is required";
      console.error(`❌ [WEATHER_TOOL] ${error}`);
      throw new Error(error);
    }

    // Validate date format
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      const error = "Invalid date format. Use YYYY-MM-DD";
      console.error(`❌ [WEATHER_TOOL] ${error}`);
      throw new Error(error);
    }

    // Validate time format if provided
    if (time && !/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/.test(time)) {
      const error = "Invalid time format. Use 24-hour format (HH:mm)";
      console.error(`❌ [WEATHER_TOOL] ${error}`);
      throw new Error(error);
    }

    const targetLocation =
      location || process.env.RESTAURANT_LOCATION || "Mumbai";
    const timeStr = time ? ` at ${time}` : "";
    console.log(
      `🌤️ [WEATHER_TOOL] Fetching weather for ${date}${timeStr} in ${targetLocation}`
    );

    const weatherData = await getWeatherForDate(date, targetLocation, time);

    console.log(
      `✅ [WEATHER_TOOL] Weather fetched successfully:`,
      JSON.stringify(weatherData, null, 2)
    );

    return {
      success: true,
      data: weatherData,
    };
  } catch (error) {
    console.error(`❌ [WEATHER_TOOL] Error:`, error.message);
    console.error("Stack trace:", error.stack);
    return {
      success: false,
      error: error.message || "Failed to fetch weather data",
    };
  }
};

module.exports = {
  name: "weather",
  description: "Check weather forecast for a specific date",
  execute,
};
