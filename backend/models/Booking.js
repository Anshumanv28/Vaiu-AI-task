const mongoose = require("mongoose");

const bookingSchema = new mongoose.Schema({
  bookingId: {
    type: String,
    default: function () {
      return this._id.toString();
    },
  },
  customerName: {
    type: String,
    default: "Guest",
    required: true,
  },
  numberOfGuests: {
    type: Number,
    required: true,
    min: 1,
  },
  bookingDate: {
    type: Date,
    required: true,
  },
  bookingTime: {
    type: String,
    required: true,
    match: /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/, // 24-hour format HH:mm
  },
  cuisinePreference: {
    type: String,
    default: "",
  },
  specialRequests: {
    type: String,
    default: "",
  },
  weatherInfo: {
    condition: String,
    temperature: Number,
    description: String,
  },
  seatingPreference: {
    type: String,
    enum: ["indoor", "outdoor"],
    default: "indoor",
  },
  status: {
    type: String,
    enum: ["pending", "confirmed", "cancelled"],
    default: "pending",
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
});

// Set bookingId after document is created
bookingSchema.post("save", function () {
  if (!this.bookingId || this.bookingId === this._id.toString()) {
    this.bookingId = this._id.toString();
  }
});

module.exports = mongoose.model("Booking", bookingSchema);
