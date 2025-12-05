require("dotenv").config();
const express = require("express");
const cors = require("cors");
const connectDB = require("./config/database");
const errorHandler = require("./middleware/errorHandler");

// Import routes
const bookingsRoutes = require("./routes/bookings");
const weatherRoutes = require("./routes/weather");
const livekitRoutes = require("./routes/livekit");

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 5000;

// Connect to MongoDB
connectDB();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get("/", (req, res) => {
  res.json({
    message: "Restaurant Booking API",
    version: "1.0.0",
    endpoints: {
      bookings: "/api/bookings",
      weather: "/api/weather/:date",
    },
  });
});

app.use("/api/bookings", bookingsRoutes);
app.use("/api/weather", weatherRoutes);
app.use("/api/livekit", livekitRoutes);

// Error handling middleware (must be last)
app.use(errorHandler);

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
