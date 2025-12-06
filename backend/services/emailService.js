const nodemailer = require("nodemailer");

/**
 * Send booking confirmation email to both customer and restaurant
 * Logs errors but doesn't throw - booking should succeed even if email fails
 * @param {Object} booking - Booking document from database
 */
const sendBookingConfirmation = async (booking) => {
  try {
    // Validate and clean environment variables
    const emailUser = process.env.EMAIL_USER?.trim();
    const emailPass = process.env.EMAIL_PASS?.trim();
    const restaurantEmail = process.env.RESTAURANT_EMAIL?.trim();

    if (!emailUser || !emailPass) {
      throw new Error(
        "Email configuration missing: EMAIL_USER and EMAIL_PASS must be set in environment variables"
      );
    }

    if (!restaurantEmail) {
      throw new Error("RESTAURANT_EMAIL must be set in environment variables");
    }

    // Debug: Check password length (app passwords are typically 16 characters)
    const passLength = emailPass.length;
    if (passLength !== 16) {
      console.warn(
        `⚠️  Warning: EMAIL_PASS length is ${passLength} characters. Gmail App Passwords are typically 16 characters.`
      );
    }

    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        user: emailUser,
        pass: emailPass,
      },
      // Add connection timeout and retry options
      connectionTimeout: 10000,
      greetingTimeout: 10000,
      socketTimeout: 10000,
    });

    // Verify transporter configuration
    await transporter.verify();
    console.log("Email transporter verified successfully");

    const bookingDate = new Date(booking.bookingDate).toLocaleDateString(
      "en-IN",
      {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
        timeZone: "Asia/Kolkata",
      }
    );

    // Email content for customer
    const customerEmailHtml = `
      <h2>Booking Confirmation</h2>
      <p>Dear ${booking.customerName},</p>
      <p>Thank you for your reservation! We're excited to serve you.</p>
      <h3>Booking Details</h3>
      <p><strong>Booking ID:</strong> ${booking.bookingId}</p>
      <p><strong>Number of Guests:</strong> ${booking.numberOfGuests}</p>
      <p><strong>Date:</strong> ${bookingDate}</p>
      <p><strong>Time:</strong> ${booking.bookingTime}</p>
      <p><strong>Cuisine Preference:</strong> ${
        booking.cuisinePreference || "Not specified"
      }</p>
      <p><strong>Special Requests:</strong> ${
        booking.specialRequests || "None"
      }</p>
      <p><strong>Seating Preference:</strong> ${booking.seatingPreference}</p>
      <p>We look forward to seeing you!</p>
      <p>Best regards,<br>The Restaurant Team</p>
    `;

    // Email content for restaurant
    const restaurantEmailHtml = `
      <h2>New Restaurant Booking</h2>
      <p><strong>Booking ID:</strong> ${booking.bookingId}</p>
      <p><strong>Customer Name:</strong> ${booking.customerName}</p>
      ${
        booking.customerEmail
          ? `<p><strong>Customer Email:</strong> ${booking.customerEmail}</p>`
          : ""
      }
      <p><strong>Number of Guests:</strong> ${booking.numberOfGuests}</p>
      <p><strong>Date:</strong> ${bookingDate}</p>
      <p><strong>Time:</strong> ${booking.bookingTime}</p>
      <p><strong>Cuisine Preference:</strong> ${
        booking.cuisinePreference || "Not specified"
      }</p>
      <p><strong>Special Requests:</strong> ${
        booking.specialRequests || "None"
      }</p>
      <p><strong>Seating Preference:</strong> ${booking.seatingPreference}</p>
      <p><strong>Status:</strong> ${booking.status}</p>
      ${
        booking.weatherInfo
          ? `
        <h3>Weather Information</h3>
        <p><strong>Condition:</strong> ${booking.weatherInfo.condition}</p>
        <p><strong>Temperature:</strong> ${booking.weatherInfo.temperature}°C</p>
        <p><strong>Description:</strong> ${booking.weatherInfo.description}</p>
      `
          : ""
      }
      <p><strong>Created At:</strong> ${new Date(
        booking.createdAt
      ).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}</p>
    `;

    // Send email to restaurant
    const restaurantMailOptions = {
      from: emailUser,
      to: restaurantEmail,
      subject: `New Booking - ${bookingDate} at ${booking.bookingTime}`,
      html: restaurantEmailHtml,
    };

    await transporter.sendMail(restaurantMailOptions);
    console.log(
      `Restaurant confirmation email sent for booking ${booking.bookingId}`
    );

    // Send email to customer if email is provided
    if (booking.customerEmail && booking.customerEmail.trim() !== "") {
      const customerMailOptions = {
        from: emailUser,
        to: booking.customerEmail,
        subject: `Booking Confirmation - ${bookingDate} at ${booking.bookingTime}`,
        html: customerEmailHtml,
      };

      await transporter.sendMail(customerMailOptions);
      console.log(
        `Customer confirmation email sent to ${booking.customerEmail} for booking ${booking.bookingId}`
      );
    } else {
      console.log(
        `No customer email provided for booking ${booking.bookingId} - skipping customer email`
      );
    }
  } catch (error) {
    // Log detailed error but don't throw - booking should succeed even if email fails
    console.error("Email sending failed:", error.message);

    // Provide helpful error messages for common issues
    if (
      error.message.includes("Application-specific password required") ||
      error.message.includes("Invalid login") ||
      error.code === "EAUTH"
    ) {
      console.error("\n⚠️  Gmail Authentication Error:");
      console.error("   Gmail requires an App Password when 2FA is enabled.");
      console.error("   Steps to fix:");
      console.error("   1. Go to: https://myaccount.google.com/apppasswords");
      console.error("   2. Generate an App Password for 'Mail'");
      console.error(
        "   3. Update EMAIL_PASS in your .env file with the 16-character app password"
      );
      console.error("   4. Restart your server\n");
    } else if (error.message.includes("Email configuration missing")) {
      console.error("\n⚠️  Email Configuration Error:");
      console.error(
        "   Please set EMAIL_USER, EMAIL_PASS, and RESTAURANT_EMAIL in your .env file\n"
      );
    } else {
      console.error("   Full error:", error);
    }

    // Don't throw error - booking creation should still succeed
  }
};

module.exports = { sendBookingConfirmation };
