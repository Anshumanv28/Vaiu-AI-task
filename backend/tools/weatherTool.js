/**
 * Weather checking tool
 */
const { getWeatherForDate } = require("../services/weatherService");

/**
 * Check weather for a specific date
 * @param {Object} params - Tool parameters
 * @param {string} params.date - Date in YYYY-MM-DD format
 * @param {string} [params.location] - Location (defaults to RESTAURANT_LOCATION or "Mumbai")
 * @returns {Promise<Object>} Weather data with condition, temperature, description
 */
const execute = async (params) => {
  console.log(`🔧 [WEATHER_TOOL] Starting weather check`);
  console.log(`📦 [WEATHER_TOOL] Params:`, JSON.stringify(params, null, 2));

  try {
    const { date, location } = params;

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

    const targetLocation =
      location || process.env.RESTAURANT_LOCATION || "Mumbai";
    console.log(
      `🌤️ [WEATHER_TOOL] Fetching weather for ${date} in ${targetLocation}`
    );

    const weatherData = await getWeatherForDate(date, targetLocation);

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
