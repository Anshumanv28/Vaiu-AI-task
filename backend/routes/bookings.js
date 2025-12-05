const express = require("express");
const router = express.Router();
const Booking = require("../models/Booking");
const { sendBookingConfirmation } = require("../services/emailService");

/**
 * POST /api/bookings
 * Create a new booking with inline duplicate check
 */
router.post("/", async (req, res) => {
  try {
    const {
      numberOfGuests,
      bookingDate,
      bookingTime,
      cuisinePreference,
      specialRequests,
      weatherInfo,
      seatingPreference,
      customerEmail,
    } = req.body;

    // Validation
    if (!numberOfGuests || !bookingDate || !bookingTime) {
      return res.status(400).json({
        success: false,
        error: "numberOfGuests, bookingDate, and bookingTime are required",
      });
    }

    // Validate time format (24-hour HH:mm)
    if (!/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/.test(bookingTime)) {
      return res.status(400).json({
        success: false,
        error: "Invalid time format. Use 24-hour format (HH:mm)",
      });
    }

    // Inline duplicate check - exact date + time match only
    const existing = await Booking.findOne({
      bookingDate: new Date(bookingDate),
      bookingTime: bookingTime,
    });

    if (existing) {
      return res.status(409).json({
        success: false,
        error: "That exact time slot is already booked",
      });
    }

    // Create booking (customerName defaults to "Guest" in schema)
    const booking = await Booking.create({
      numberOfGuests,
      bookingDate: new Date(bookingDate),
      bookingTime,
      cuisinePreference: cuisinePreference || "",
      specialRequests: specialRequests || "",
      weatherInfo: weatherInfo || null,
      seatingPreference: seatingPreference || "indoor",
      customerEmail: customerEmail || "",
      status: "pending",
    });

    // Send email confirmation (log errors but don't fail booking)
    try {
      await sendBookingConfirmation(booking);
    } catch (emailError) {
      console.error("Email failed but booking created:", emailError.message);
      // Don't throw - booking still succeeds
    }

    res.status(201).json({
      success: true,
      data: booking,
    });
  } catch (error) {
    console.error("Booking creation error:", error);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to create booking",
    });
  }
});

/**
 * GET /api/bookings
 * Get all bookings
 */
router.get("/", async (req, res) => {
  try {
    const bookings = await Booking.find().sort({ createdAt: -1 });
    res.json({
      success: true,
      count: bookings.length,
      data: bookings,
    });
  } catch (error) {
    console.error("Get bookings error:", error);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to fetch bookings",
    });
  }
});

/**
 * GET /api/bookings/:id
 * Get a specific booking by ID
 */
router.get("/:id", async (req, res) => {
  try {
    const booking = await Booking.findById(req.params.id);

    if (!booking) {
      return res.status(404).json({
        success: false,
        error: "Booking not found",
      });
    }

    res.json({
      success: true,
      data: booking,
    });
  } catch (error) {
    console.error("Get booking error:", error);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to fetch booking",
    });
  }
});

/**
 * DELETE /api/bookings/:id
 * Cancel a booking
 */
router.delete("/:id", async (req, res) => {
  try {
    const booking = await Booking.findByIdAndUpdate(
      req.params.id,
      { status: "cancelled" },
      { new: true }
    );

    if (!booking) {
      return res.status(404).json({
        success: false,
        error: "Booking not found",
      });
    }

    res.json({
      success: true,
      data: booking,
      message: "Booking cancelled successfully",
    });
  } catch (error) {
    console.error("Cancel booking error:", error);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to cancel booking",
    });
  }
});

module.exports = router;
