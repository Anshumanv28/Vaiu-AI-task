import React from "react";
import {
  colors,
  shadows,
  borderRadius,
  gradients,
  transitions,
} from "../utils/styles";
import { useResponsive } from "../hooks/useResponsive";

const OptionSelector = ({ options, message, onSelect, isVisible }) => {
  const { isMobile } = useResponsive();
  const [hoveredIndex, setHoveredIndex] = React.useState(null);

  if (!isVisible || !options || options.length === 0) {
    return null;
  }

  // Container style
  const containerStyle = {
    backgroundColor: "rgba(255, 255, 255, 0.95)",
    backdropFilter: "blur(8px)",
    borderRadius: borderRadius["2xl"],
    boxShadow: shadows.lg,
    padding: isMobile ? "1rem" : "1.5rem",
    marginTop: "1rem",
    animation: "fadeInSlide 0.3s ease-out forwards",
  };

  // Message style
  const messageStyle = {
    fontSize: isMobile ? "0.875rem" : "0.9375rem",
    color: colors["baby-blue-ice"][700],
    marginBottom: "1rem",
    fontWeight: 500,
  };

  // Options container style
  const optionsContainerStyle = {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  };

  // Option button style
  const getOptionButtonStyle = (isHovered) => ({
    width: "100%",
    padding: isMobile ? "0.75rem 1rem" : "0.875rem 1.25rem",
    borderRadius: borderRadius.lg,
    border: `2px solid ${colors["baby-blue-ice"][300]}`,
    background: isHovered ? gradients["baby-blue-ice"] : "white",
    color: isHovered ? "white" : colors["baby-blue-ice"][700],
    fontSize: isMobile ? "0.875rem" : "0.9375rem",
    fontWeight: 500,
    cursor: "pointer",
    transition: `all ${transitions.normal} ease-in-out`,
    boxShadow: isHovered ? shadows.md : shadows.sm,
    textAlign: "left",
    outline: "none",
  });

  return (
    <div style={containerStyle}>
      {message && <p style={messageStyle}>{message}</p>}
      <div style={optionsContainerStyle}>
        {options.map((option, index) => (
          <button
            key={index}
            onClick={() => onSelect && onSelect(option)}
            onMouseEnter={() => setHoveredIndex(index)}
            onMouseLeave={() => setHoveredIndex(null)}
            style={getOptionButtonStyle(hoveredIndex === index)}
            onFocus={(e) => {
              e.currentTarget.style.outline = `3px solid ${colors["baby-blue-ice"][300]}`;
              e.currentTarget.style.outlineOffset = "2px";
            }}
            onBlur={(e) => {
              e.currentTarget.style.outline = "none";
            }}
            aria-label={`Select option: ${option}`}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
};

export default OptionSelector;
