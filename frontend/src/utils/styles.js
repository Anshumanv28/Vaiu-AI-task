/**
 * Style constants and utilities for inline styles
 * Colors are centralized via CSS variables defined in index.css
 */

// Helper function to get CSS variable name for a color
export const getColorVar = (colorName, shade = 500) => {
  // Handle kebab-case color names
  const varName = colorName.includes("-")
    ? `--${colorName}-${shade}`
    : `--${colorName}-${shade}`;
  return `var(${varName})`;
};

// Helper function to get semantic color CSS variable
export const getSemanticColor = (semanticName) => {
  return `var(--${semanticName})`;
};

// Color palette helpers (returns CSS variable references)
export const colors = {
  "baby-blue-ice": {
    50: "var(--baby-blue-ice-50)",
    100: "var(--baby-blue-ice-100)",
    200: "var(--baby-blue-ice-200)",
    300: "var(--baby-blue-ice-300)",
    400: "var(--baby-blue-ice-400)",
    500: "var(--baby-blue-ice-500)",
    600: "var(--baby-blue-ice-600)",
    700: "var(--baby-blue-ice-700)",
    800: "var(--baby-blue-ice-800)",
    900: "var(--baby-blue-ice-900)",
    950: "var(--baby-blue-ice-950)",
  },
  aquamarine: {
    50: "var(--aquamarine-50)",
    100: "var(--aquamarine-100)",
    200: "var(--aquamarine-200)",
    300: "var(--aquamarine-300)",
    400: "var(--aquamarine-400)",
    500: "var(--aquamarine-500)",
    600: "var(--aquamarine-600)",
    700: "var(--aquamarine-700)",
    800: "var(--aquamarine-800)",
    900: "var(--aquamarine-900)",
    950: "var(--aquamarine-950)",
  },
  "rosy-taupe": {
    50: "var(--rosy-taupe-50)",
    100: "var(--rosy-taupe-100)",
    200: "var(--rosy-taupe-200)",
    300: "var(--rosy-taupe-300)",
    400: "var(--rosy-taupe-400)",
    500: "var(--rosy-taupe-500)",
    600: "var(--rosy-taupe-600)",
    700: "var(--rosy-taupe-700)",
    800: "var(--rosy-taupe-800)",
    900: "var(--rosy-taupe-900)",
    950: "var(--rosy-taupe-950)",
  },
  "blush-rose": {
    50: "var(--blush-rose-50)",
    100: "var(--blush-rose-100)",
    200: "var(--blush-rose-200)",
    300: "var(--blush-rose-300)",
    400: "var(--blush-rose-400)",
    500: "var(--blush-rose-500)",
    600: "var(--blush-rose-600)",
    700: "var(--blush-rose-700)",
    800: "var(--blush-rose-800)",
    900: "var(--blush-rose-900)",
    950: "var(--blush-rose-950)",
  },
  "vintage-berry": {
    50: "var(--vintage-berry-50)",
    100: "var(--vintage-berry-100)",
    200: "var(--vintage-berry-200)",
    300: "var(--vintage-berry-300)",
    400: "var(--vintage-berry-400)",
    500: "var(--vintage-berry-500)",
    600: "var(--vintage-berry-600)",
    700: "var(--vintage-berry-700)",
    800: "var(--vintage-berry-800)",
    900: "var(--vintage-berry-900)",
    950: "var(--vintage-berry-950)",
  },
  gray: {
    50: "var(--gray-50)",
    100: "var(--gray-100)",
    200: "var(--gray-200)",
    300: "var(--gray-300)",
    400: "var(--gray-400)",
    500: "var(--gray-500)",
    600: "var(--gray-600)",
    700: "var(--gray-700)",
    800: "var(--gray-800)",
    900: "var(--gray-900)",
  },
};

// Semantic color mappings (using CSS variables)
export const semanticColors = {
  primary: "var(--primary)",
  accent: "var(--accent)",
  warm: "var(--warm)",
  highlight: "var(--highlight)",
  secondary: "var(--secondary)",
};

// Responsive breakpoints
export const breakpoints = {
  mobile: 640,
  tablet: 1024,
  desktop: 1440,
};

// Common style objects
export const shadows = {
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
  xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
  "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
};

export const borderRadius = {
  sm: "0.25rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
  "2xl": "1.5rem",
  full: "9999px",
};

export const spacing = {
  xs: "0.5rem",
  sm: "1rem",
  md: "1.5rem",
  lg: "2rem",
  xl: "3rem",
  "2xl": "4rem",
};

// Gradient helpers (using CSS variables)
export const gradients = {
  "baby-blue-ice": `linear-gradient(135deg, var(--baby-blue-ice-400), var(--baby-blue-ice-600))`,
  "baby-blue-ice-light": `linear-gradient(135deg, var(--baby-blue-ice-50), var(--aquamarine-50), var(--baby-blue-ice-100))`,
  aquamarine: `linear-gradient(135deg, var(--aquamarine-400), var(--aquamarine-600))`,
  "rosy-taupe": `linear-gradient(135deg, var(--rosy-taupe-400), var(--rosy-taupe-600))`,
  "vintage-berry": `linear-gradient(135deg, var(--vintage-berry-400), var(--vintage-berry-600))`,
  "text-gradient": `linear-gradient(to right, var(--baby-blue-ice-600), var(--aquamarine-600))`,
};

// Animation durations
export const transitions = {
  fast: "150ms",
  normal: "200ms",
  slow: "300ms",
  slower: "500ms",
};

// Helper function to get responsive styles
export const getResponsiveStyle = (mobile, tablet, desktop) => {
  return {
    "@media (max-width: 639px)": mobile,
    "@media (min-width: 640px) and (max-width: 1023px)": tablet,
    "@media (min-width: 1024px)": desktop,
  };
};

// Helper function to create gradient style using CSS variables
export const createGradient = (colorVar1, colorVar2, direction = "135deg") => {
  return `linear-gradient(${direction}, ${colorVar1}, ${colorVar2})`;
};

const styleUtils = {
  colors,
  semanticColors,
  breakpoints,
  shadows,
  borderRadius,
  spacing,
  gradients,
  transitions,
  getColorVar,
  getSemanticColor,
  createGradient,
};

export default styleUtils;
