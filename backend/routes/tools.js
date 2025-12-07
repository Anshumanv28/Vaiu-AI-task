/**
 * Tool orchestration endpoint
 * Routes tool calls to appropriate tool modules
 */
const express = require("express");
const router = express.Router();
const {
  weatherTool,
  bookingTool,
  emailTool,
  dateAvailabilityTool,
} = require("../tools");

// Tool registry mapping
const toolRegistry = {
  weather: weatherTool,
  "check-availability": dateAvailabilityTool,
  "send-email": emailTool,
  "create-booking": bookingTool,
};

/**
 * POST /api/tools/:toolName
 * Execute a specific tool
 */
router.post("/:toolName", async (req, res) => {
  const startTime = Date.now();
  const { toolName } = req.params;
  const params = req.body;

  console.log(`🔧 [BACKEND] Tool execution request: ${toolName}`);
  console.log(`📦 [BACKEND] Tool params:`, JSON.stringify(params, null, 2));

  try {
    // Find tool in registry
    const tool = toolRegistry[toolName];

    if (!tool) {
      console.error(`❌ [BACKEND] Tool '${toolName}' not found`);
      return res.status(404).json({
        success: false,
        error: `Tool '${toolName}' not found. Available tools: ${Object.keys(
          toolRegistry
        ).join(", ")}`,
      });
    }

    // Execute tool
    const result = await tool.execute(params);
    const duration = Date.now() - startTime;

    if (result.success) {
      console.log(
        `✅ [BACKEND] Tool '${toolName}' executed successfully in ${duration}ms`
      );
    } else {
      console.error(`❌ [BACKEND] Tool '${toolName}' failed: ${result.error}`);
    }

    // Return result with appropriate status code
    const statusCode = result.success ? 200 : 400;
    res.status(statusCode).json(result);
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(
      `❌ [BACKEND] Tool execution error for '${toolName}' (${duration}ms):`,
      error
    );
    console.error("Stack trace:", error.stack);
    res.status(500).json({
      success: false,
      error: error.message || "Failed to execute tool",
    });
  }
});

/**
 * GET /api/tools
 * List all available tools
 */
router.get("/", (req, res) => {
  const tools = Object.keys(toolRegistry).map((name) => {
    const tool = toolRegistry[name];
    return {
      name: tool.name,
      description: tool.description,
    };
  });

  res.json({
    success: true,
    data: tools,
  });
});

module.exports = router;
