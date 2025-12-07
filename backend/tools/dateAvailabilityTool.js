/**
 * Date/time availability checking tool
 */
const Booking = require("../models/Booking");

/**
 * Check if a date/time slot is available
 * @param {Object} params - Tool parameters
 * @param {string} params.date - Date in YYYY-MM-DD format
 * @param {string} [params.time] - Time in HH:mm format (optional, checks all times for date if not provided)
 * @returns {Promise<Object>} Availability status
 */
const execute = async (params) => {
  console.log(`🔧 [AVAILABILITY_TOOL] Starting availability check`);
  console.log(
    `📦 [AVAILABILITY_TOOL] Params:`,
    JSON.stringify(params, null, 2)
  );

  try {
    const { date, time } = params;

    if (!date) {
      const error = "Date parameter is required";
      console.error(`❌ [AVAILABILITY_TOOL] ${error}`);
      throw new Error(error);
    }

    // Validate date format
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      const error = "Invalid date format. Use YYYY-MM-DD";
      console.error(`❌ [AVAILABILITY_TOOL] ${error}`);
      throw new Error(error);
    }

    // Validate time format if provided
    if (time && !/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/.test(time)) {
      const error = "Invalid time format. Use 24-hour format (HH:mm)";
      console.error(`❌ [AVAILABILITY_TOOL] ${error}`);
      throw new Error(error);
    }

    const query = {
      bookingDate: new Date(date),
      status: { $ne: "cancelled" }, // Don't count cancelled bookings
    };

    if (time) {
      query.bookingTime = time;
    }

    console.log(
      `🔍 [AVAILABILITY_TOOL] Checking for existing bookings with query:`,
      JSON.stringify(query, null, 2)
    );
    const existingBookings = await Booking.find(query);

    const isAvailable = existingBookings.length === 0;

    console.log(
      `✅ [AVAILABILITY_TOOL] Found ${existingBookings.length} existing booking(s). Available: ${isAvailable}`
    );

    return {
      success: true,
      data: {
        available: isAvailable,
        date,
        time: time || null,
        existingBookings: existingBookings.length,
      },
    };
  } catch (error) {
    console.error(`❌ [AVAILABILITY_TOOL] Error:`, error.message);
    console.error("Stack trace:", error.stack);
    return {
      success: false,
      error: error.message || "Failed to check availability",
    };
  }
};

module.exports = {
  name: "check-availability",
  description: "Check if a date/time slot is available for booking",
  execute,
};
