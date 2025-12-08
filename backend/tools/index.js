/**
 * Tool registry - exports all available tools
 */
const weatherTool = require("./weatherTool");
const bookingTool = require("./bookingTool");
const emailTool = require("./emailTool");
const dateAvailabilityTool = require("./dateAvailabilityTool");
const dateCheckTool = require("./dateCheckTool");

module.exports = {
  weatherTool,
  bookingTool,
  emailTool,
  dateAvailabilityTool,
  dateCheckTool,
};
