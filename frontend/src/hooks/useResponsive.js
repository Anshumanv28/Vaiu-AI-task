import { useState, useEffect } from "react";
import { breakpoints } from "../utils/styles";

/**
 * Custom hook for responsive design
 * Returns current breakpoint and boolean flags for each breakpoint
 */
export const useResponsive = () => {
  const [windowWidth, setWindowWidth] = useState(
    typeof window !== "undefined" ? window.innerWidth : 1024
  );

  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const isMobile = windowWidth < breakpoints.mobile;
  const isTablet =
    windowWidth >= breakpoints.mobile && windowWidth < breakpoints.tablet;
  const isDesktop =
    windowWidth >= breakpoints.tablet && windowWidth < breakpoints.desktop;
  const isLargeDesktop = windowWidth >= breakpoints.desktop;

  const breakpoint = isMobile
    ? "mobile"
    : isTablet
    ? "tablet"
    : isDesktop
    ? "desktop"
    : "largeDesktop";

  return {
    windowWidth,
    breakpoint,
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
  };
};

export default useResponsive;
