const mongoose = require("mongoose");

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI, {
      serverSelectionTimeoutMS: 10000, // 10 seconds timeout
      socketTimeoutMS: 45000,
    });
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error(`MongoDB Connection Error: ${error.message}`);

    // Provide helpful error messages
    if (error.message.includes("IP") || error.message.includes("whitelist")) {
      console.error("\n⚠️  MongoDB Atlas IP Whitelist Issue:");
      console.error(
        "   Your current IP address is not whitelisted in MongoDB Atlas."
      );
      console.error(
        "   For deployment, add 0.0.0.0/0 to allow all IPs (or use specific Render IPs)"
      );
      console.error(
        "   Atlas Dashboard → Network Access → Add IP Address → 0.0.0.0/0"
      );
    }

    // Don't exit in production - allow server to start and retry
    // The server can still run, and MongoDB will retry on first request
    if (process.env.NODE_ENV === "production") {
      console.warn(
        "   Server will continue running. MongoDB will retry connection on first request."
      );
      console.warn(
        "   Make sure to whitelist your deployment platform's IP addresses in MongoDB Atlas.\n"
      );
    } else {
      // In development, exit to catch configuration issues early
      console.error(
        "   Exiting in development mode. Fix MongoDB connection and restart.\n"
      );
      process.exit(1);
    }
  }
};

module.exports = connectDB;
