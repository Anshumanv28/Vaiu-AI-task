/**
 * Email sending tool (standalone, separate from booking creation)
 */
const { sendBookingConfirmation } = require("../services/emailService");
const Booking = require("../models/Booking");

/**
 * Send email confirmation
 * @param {Object} params - Tool parameters
 * @param {string} params.bookingId - Booking ID to send confirmation for
 * @returns {Promise<Object>} Email sending status
 */
const execute = async (params) => {
  console.log(`🔧 [EMAIL_TOOL] Starting email send`);
  console.log(`📦 [EMAIL_TOOL] Params:`, JSON.stringify(params, null, 2));

  try {
    const { bookingId } = params;

    if (!bookingId) {
      const error = "Booking ID parameter is required";
      console.error(`❌ [EMAIL_TOOL] ${error}`);
      throw new Error(error);
    }

    // Find the booking
    console.log(`🔍 [EMAIL_TOOL] Finding booking with ID: ${bookingId}`);
    const booking = await Booking.findById(bookingId);
    if (!booking) {
      const error = "Booking not found";
      console.error(`❌ [EMAIL_TOOL] ${error}`);
      throw new Error(error);
    }

    // Send email confirmation
    console.log(
      `📧 [EMAIL_TOOL] Sending confirmation email to ${
        booking.customerEmail || "restaurant"
      }`
    );
    await sendBookingConfirmation(booking);

    console.log(`✅ [EMAIL_TOOL] Email sent successfully`);

    return {
      success: true,
      data: {
        bookingId,
        emailSent: true,
        customerEmail: booking.customerEmail || null,
        restaurantEmail: process.env.RESTAURANT_EMAIL || null,
      },
    };
  } catch (error) {
    // Log error but return structured response
    console.error(`❌ [EMAIL_TOOL] Error:`, error.message);
    console.error("Stack trace:", error.stack);
    return {
      success: false,
      error: error.message || "Failed to send email",
    };
  }
};

module.exports = {
  name: "send-email",
  description: "Send booking confirmation email",
  execute,
};
