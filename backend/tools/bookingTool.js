/**
 * Booking creation and management tool
 */
const Booking = require("../models/Booking");
const { sendBookingConfirmation } = require("../services/emailService");

/**
 * Create a new booking
 * @param {Object} params - Tool parameters
 * @param {number} params.numberOfGuests - Number of guests
 * @param {string} params.bookingDate - Date in YYYY-MM-DD format
 * @param {string} params.bookingTime - Time in HH:mm format
 * @param {string} [params.cuisinePreference] - Cuisine preference
 * @param {string} [params.specialRequests] - Special requests
 * @param {Object} [params.weatherInfo] - Weather information
 * @param {string} [params.seatingPreference] - Seating preference (indoor/outdoor)
 * @param {string} [params.customerName] - Customer name
 * @param {string} [params.customerEmail] - Customer email
 * @returns {Promise<Object>} Created booking data
 */
const execute = async (params) => {
  console.log(`🔧 [BOOKING_TOOL] Starting booking creation`);
  console.log(`📦 [BOOKING_TOOL] Params:`, JSON.stringify(params, null, 2));

  try {
    const {
      numberOfGuests,
      bookingDate,
      bookingTime,
      cuisinePreference,
      specialRequests,
      weatherInfo,
      seatingPreference,
      customerName,
      customerEmail,
      customerContact,
    } = params;

    // Validation
    if (!numberOfGuests || !bookingDate || !bookingTime) {
      const error = "numberOfGuests, bookingDate, and bookingTime are required";
      console.error(`❌ [BOOKING_TOOL] Validation failed: ${error}`);
      throw new Error(error);
    }

    // Validate time format (24-hour HH:mm)
    if (!/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/.test(bookingTime)) {
      throw new Error("Invalid time format. Use 24-hour format (HH:mm)");
    }

    // Normalize seating preference to lowercase and validate
    let normalizedSeatingPreference = "indoor"; // default
    if (seatingPreference) {
      const normalized = seatingPreference.toLowerCase().trim();
      if (normalized === "indoor" || normalized === "outdoor") {
        normalizedSeatingPreference = normalized;
      } else {
        console.warn(
          `⚠️ [BOOKING_TOOL] Invalid seating preference "${seatingPreference}", defaulting to "indoor"`
        );
      }
    }

    // Check for duplicates
    console.log(
      `🔍 [BOOKING_TOOL] Checking for existing bookings on ${bookingDate} at ${bookingTime}`
    );
    const existing = await Booking.findOne({
      bookingDate: new Date(bookingDate),
      bookingTime: bookingTime,
      status: { $ne: "cancelled" },
    });

    if (existing) {
      console.error(
        `❌ [BOOKING_TOOL] Time slot already booked. Existing booking ID: ${existing._id}`
      );
      throw new Error("That exact time slot is already booked");
    }

    // Create booking
    console.log(`📝 [BOOKING_TOOL] Creating new booking...`);
    console.log(
      `📋 [BOOKING_TOOL] Seating preference: "${seatingPreference}" → normalized to "${normalizedSeatingPreference}"`
    );
    const booking = await Booking.create({
      numberOfGuests,
      bookingDate: new Date(bookingDate),
      bookingTime,
      cuisinePreference: cuisinePreference || "",
      specialRequests: specialRequests || "",
      weatherInfo: weatherInfo || null,
      seatingPreference: normalizedSeatingPreference,
      customerName: customerName || "Guest",
      customerEmail: customerEmail || "",
      customerContact: customerContact || "",
      status: "pending",
    });

    console.log(
      `✅ [BOOKING_TOOL] Booking created successfully! Booking ID: ${
        booking._id || booking.bookingId
      }`
    );

    // Send email confirmation (non-blocking)
    let emailStatus = { sent: false, error: null };
    if (customerEmail) {
      console.log(
        `📧 [BOOKING_TOOL] Sending confirmation email to ${customerEmail}`
      );
      try {
        await sendBookingConfirmation(booking);
        emailStatus.sent = true;
        console.log(`✅ [BOOKING_TOOL] Email sent successfully`);
      } catch (emailError) {
        console.error(
          `❌ [BOOKING_TOOL] Email failed but booking created:`,
          emailError.message
        );
        emailStatus.error = emailError.message;
        // Don't throw - booking still succeeds
      }
    } else {
      console.log(
        `ℹ️ [BOOKING_TOOL] No email provided, skipping email confirmation`
      );
    }

    return {
      success: true,
      data: {
        booking,
        emailStatus,
      },
    };
  } catch (error) {
    console.error(`❌ [BOOKING_TOOL] Error creating booking:`, error.message);
    console.error("Stack trace:", error.stack);
    return {
      success: false,
      error: error.message || "Failed to create booking",
    };
  }
};

module.exports = {
  name: "create-booking",
  description: "Create a new restaurant booking",
  execute,
};
