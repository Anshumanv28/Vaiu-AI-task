/**
 * Date and time checking tool - returns current date and time for context awareness
 */
/**
 * Get current date and time for context awareness
 * Helps detect if users are trying to book in the past
 * @param {Object} params - Tool parameters (empty, no params needed)
 * @returns {Promise<Object>} Current date (YYYY-MM-DD) and time (HH:mm) in 24-hour format
 */
const execute = async (params) => {
  console.log(`🔧 [DATE_TIME_CHECK_TOOL] Getting current date and time`);

  try {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const todayStr = `${year}-${month}-${day}`;

    // Get current time in 24-hour format (HH:mm)
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    const currentTime = `${hours}:${minutes}`;

    console.log(
      `✅ [DATE_TIME_CHECK_TOOL] Current date: ${todayStr}, Current time: ${currentTime}`
    );

    return {
      success: true,
      data: {
        today: todayStr,
        date: todayStr, // Alias for convenience
        currentTime: currentTime,
        time: currentTime, // Alias for convenience
        dayOfWeek: now.toLocaleDateString("en-US", { weekday: "long" }),
        formatted: now.toLocaleDateString("en-US", {
          weekday: "long",
          year: "numeric",
          month: "long",
          day: "numeric",
        }),
        formattedTime: now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        }),
      },
    };
  } catch (error) {
    console.error(`❌ [DATE_TIME_CHECK_TOOL] Error:`, error.message);
    console.error("Stack trace:", error.stack);
    return {
      success: false,
      error: error.message || "Failed to get current date and time",
    };
  }
};

module.exports = {
  name: "check-date",
  description:
    "Get current date and time for context awareness. Use this to detect if users are trying to book in the past and to calculate relative dates like 'today', 'tomorrow', etc.",
  execute,
};
