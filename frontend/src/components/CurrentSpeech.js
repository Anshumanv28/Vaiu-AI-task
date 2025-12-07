import React from "react";
import { colors, shadows, borderRadius } from "../utils/styles";
import { useResponsive } from "../hooks/useResponsive";

const CurrentSpeech = ({ text, isVisible }) => {
  const { isMobile } = useResponsive();

  if (!isVisible || !text || text.trim() === "") {
    return null;
  }

  // Container style - fixed at bottom of viewport
  const containerStyle = {
    position: "fixed",
    bottom: isMobile ? "1rem" : "1.5rem",
    left: "50%",
    transform: "translateX(-50%)",
    maxWidth: isMobile ? "90%" : "800px",
    width: "100%",
    zIndex: 100,
    backgroundColor: "rgba(255, 255, 255, 0.95)",
    backdropFilter: "blur(8px)",
    borderRadius: borderRadius["2xl"],
    boxShadow: shadows.xl,
    padding: isMobile ? "0.75rem 1rem" : "1rem 1.5rem",
    border: `2px solid ${colors["baby-blue-ice"][300]}`,
    animation: "fadeInUp 0.3s ease-out forwards",
  };

  // Label style
  const labelStyle = {
    fontSize: "0.75rem",
    fontWeight: 600,
    color: colors["baby-blue-ice"][600],
    marginBottom: "0.5rem",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  };

  // Text style
  const textStyle = {
    fontSize: isMobile ? "0.875rem" : "0.9375rem",
    color: colors["baby-blue-ice"][800],
    lineHeight: 1.6,
    fontStyle: "italic",
  };

  return (
    <div style={containerStyle}>
      <div style={labelStyle}>Agent Speaking</div>
      <div style={textStyle}>{text}</div>
    </div>
  );
};

export default CurrentSpeech;
