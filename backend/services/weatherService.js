const axios = require("axios");

/**
 * Fetch real weather forecast data from OpenWeatherMap API
 * No caching - fetches fresh data for each request
 * @param {string} date - Booking date in YYYY-MM-DD format
 * @param {string} location - City name (from RESTAURANT_LOCATION env var)
 * @param {string} [time] - Booking time in HH:mm format (24-hour, e.g., "19:00" for 7 PM)
 * @returns {Promise<Object>} Weather data with condition, temperature, description
 */
const getWeatherForDate = async (date, location, time = null) => {
  try {
    const apiKey = process.env.OPENWEATHER_API_KEY;
    if (!apiKey) {
      throw new Error("OPENWEATHER_API_KEY is not configured");
    }

    // Build target datetime - if time is provided, use it for more accurate prediction
    let targetDateTime;
    if (time) {
      // Parse time (HH:mm format)
      const [hours, minutes] = time.split(":").map(Number);
      targetDateTime = new Date(date);
      targetDateTime.setHours(hours, minutes, 0, 0);
    } else {
      // Default to noon if no time provided
      targetDateTime = new Date(date);
      targetDateTime.setHours(12, 0, 0, 0);
    }

    // OpenWeatherMap Forecast API (5-day forecast with 3-hour intervals)
    const url = `https://api.openweathermap.org/data/2.5/forecast?q=${encodeURIComponent(
      location
    )}&appid=${apiKey}&units=metric`;

    const response = await axios.get(url);

    if (!response.data || !response.data.list) {
      throw new Error("Invalid weather API response");
    }

    // Find the closest forecast to the target date and time
    const forecasts = response.data.list;
    let closestForecast = forecasts[0];
    let minDiff = Math.abs(
      new Date(forecasts[0].dt * 1000).getTime() - targetDateTime.getTime()
    );

    for (const forecast of forecasts) {
      const forecastDateTime = new Date(forecast.dt * 1000);
      const diff = Math.abs(
        forecastDateTime.getTime() - targetDateTime.getTime()
      );
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
      time: time || null, // Include the time that was used for prediction
    };
  } catch (error) {
    console.error("Weather API Error:", error.message);
    throw new Error(`Failed to fetch weather data: ${error.message}`);
  }
};

module.exports = { getWeatherForDate };
