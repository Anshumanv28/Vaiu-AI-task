import React from "react";
import "./BookingConfirmation.css";

const BookingConfirmation = ({ booking }) => {
  if (!booking) return null;

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-IN", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="booking-confirmation">
      <h3 className="confirmation-title">Booking Confirmed!</h3>
      <div className="confirmation-details">
        <div className="detail-row">
          <span className="detail-label">Booking ID:</span>
          <span className="detail-value">{booking.bookingId}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Customer:</span>
          <span className="detail-value">{booking.customerName}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Number of Guests:</span>
          <span className="detail-value">{booking.numberOfGuests}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Date:</span>
          <span className="detail-value">
            {formatDate(booking.bookingDate)}
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Time:</span>
          <span className="detail-value">{booking.bookingTime}</span>
        </div>
        {booking.cuisinePreference && (
          <div className="detail-row">
            <span className="detail-label">Cuisine:</span>
            <span className="detail-value">{booking.cuisinePreference}</span>
          </div>
        )}
        <div className="detail-row">
          <span className="detail-label">Seating:</span>
          <span className="detail-value capitalize">
            {booking.seatingPreference}
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Status:</span>
          <span className="detail-value status-badge">{booking.status}</span>
        </div>
        {booking.weatherInfo && (
          <div className="weather-info">
            <h4>Weather Forecast</h4>
            <p>
              {booking.weatherInfo.description} -{" "}
              {booking.weatherInfo.temperature}°C
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BookingConfirmation;
