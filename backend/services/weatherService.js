const axios = require("axios");

/**
 * Fetch real weather forecast data from OpenWeatherMap API
 * No caching - fetches fresh data for each request
 * @param {string} date - Booking date in YYYY-MM-DD format
 * @param {string} location - City name (from RESTAURANT_LOCATION env var)
 * @returns {Promise<Object>} Weather data with condition, temperature, description
 */
const getWeatherForDate = async (date, location) => {
  try {
    const apiKey = process.env.OPENWEATHER_API_KEY;
    if (!apiKey) {
      throw new Error("OPENWEATHER_API_KEY is not configured");
    }

    // Convert date to timestamp for forecast API
    const targetDate = new Date(date);
    const targetTimestamp = Math.floor(targetDate.getTime() / 1000);

    // OpenWeatherMap Forecast API (5-day forecast)
    const url = `https://api.openweathermap.org/data/2.5/forecast?q=${encodeURIComponent(
      location
    )}&appid=${apiKey}&units=metric`;

    const response = await axios.get(url);

    if (!response.data || !response.data.list) {
      throw new Error("Invalid weather API response");
    }

    // Find the closest forecast to the target date
    const forecasts = response.data.list;
    let closestForecast = forecasts[0];
    let minDiff = Math.abs(
      new Date(forecasts[0].dt * 1000).getTime() - targetDate.getTime()
    );

    for (const forecast of forecasts) {
      const forecastDate = new Date(forecast.dt * 1000);
      const diff = Math.abs(forecastDate.getTime() - targetDate.getTime());
      if (diff < minDiff) {
        minDiff = diff;
        closestForecast = forecast;
      }
    }

    // Extract weather information
    const weather = closestForecast.weather[0];
    const main = closestForecast.main;

    return {
      condition: weather.main.toLowerCase(), // e.g., "clear", "rain", "clouds"
      temperature: Math.round(main.temp),
      description: weather.description,
    };
  } catch (error) {
    console.error("Weather API Error:", error.message);
    throw new Error(`Failed to fetch weather data: ${error.message}`);
  }
};

module.exports = { getWeatherForDate };
