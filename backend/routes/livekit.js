const express = require("express");
const router = express.Router();
const { AccessToken } = require("livekit-server-sdk");

/**
 * POST /api/livekit/token
 * Generate LiveKit access token for frontend connection
 */
router.post("/token", async (req, res) => {
  try {
    const { roomName, participantName } = req.body;

    if (!roomName || !participantName) {
      return res.status(400).json({
        success: false,
        error: "roomName and participantName are required",
      });
    }

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;

    if (!apiKey || !apiSecret) {
      return res.status(500).json({
        success: false,
        error: "LiveKit credentials not configured",
      });
    }

    const at = new AccessToken(apiKey, apiSecret, {
      identity: participantName,
    });

    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    });

    const token = await at.toJwt();

    res.json({
      success: true,
      token,
    });
  } catch (error) {
    console.error("Token generation error:", error);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to generate token",
    });
  }
});

module.exports = router;
