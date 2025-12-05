import React, { useState, useEffect, useRef } from "react";
import { createLocalAudioTrack } from "livekit-client";
import {
  colors,
  shadows,
  borderRadius,
  transitions,
  gradients,
} from "../utils/styles";
import { useResponsive } from "../hooks/useResponsive";

const VoiceInterface = ({
  room,
  isConnected,
  isAgentSpeaking,
  onTranscriptUpdate,
}) => {
  const [isMicEnabled, setIsMicEnabled] = useState(false);
  const [micError, setMicError] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevels, setAudioLevels] = useState([0, 0, 0, 0, 0]);
  const localTrackRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const { isMobile } = useResponsive();

  // Get frequency-based color for each bar (returns CSS variable)
  const getBarColor = (index) => {
    const baseColors = [
      colors.aquamarine[300], // Low frequencies - lighter
      colors.aquamarine[400],
      colors.aquamarine[500], // Mid frequencies - medium
      colors.aquamarine[600],
      colors["baby-blue-ice"][500], // High frequencies - different color
    ];
    return baseColors[index] || colors.aquamarine[500];
  };

  // Analyze audio levels for equalizer visualization
  useEffect(() => {
    if (!isMicEnabled || !localTrackRef.current) {
      setIsSpeaking(false);
      setAudioLevels([0, 0, 0, 0, 0]);
      return;
    }

    const analyzeAudio = async () => {
      try {
        const stream = localTrackRef.current.mediaStream;
        if (!stream) return;

        const audioContext = new (window.AudioContext ||
          window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);

        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.85; // Smoother transitions
        source.connect(analyser);

        analyserRef.current = analyser;
        audioContextRef.current = audioContext;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        const updateLevels = () => {
          if (!analyserRef.current) return;

          analyserRef.current.getByteFrequencyData(dataArray);

          // Get average levels for 5 frequency bands
          const bandSize = Math.floor(dataArray.length / 5);
          const levels = [];
          let maxLevel = 0;

          for (let i = 0; i < 5; i++) {
            let sum = 0;
            for (let j = 0; j < bandSize; j++) {
              sum += dataArray[i * bandSize + j];
            }
            const avg = sum / bandSize;
            levels.push(avg);
            maxLevel = Math.max(maxLevel, avg);
          }

          // Normalize to 0-100 with smoother scaling
          const normalizedLevels = levels.map((level) =>
            Math.min(100, (level / 255) * 100)
          );
          setAudioLevels(normalizedLevels);

          // Consider speaking if any level is above threshold
          setIsSpeaking(maxLevel > 30);

          animationFrameRef.current = requestAnimationFrame(updateLevels);
        };

        updateLevels();
      } catch (error) {
        console.error("Error analyzing audio:", error);
      }
    };

    analyzeAudio();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      analyserRef.current = null;
      audioContextRef.current = null;
    };
  }, [isMicEnabled]);

  useEffect(() => {
    if (!room || !isConnected) return;

    const enableMic = async () => {
      try {
        setMicError(null);
        const track = await createLocalAudioTrack();
        await room.localParticipant.publishTrack(track);
        localTrackRef.current = track;
        setIsMicEnabled(true);
        console.log("Microphone enabled successfully");
      } catch (error) {
        console.error("Error enabling microphone:", error);
        let errorMessage = "Failed to enable microphone";

        if (
          error.name === "NotAllowedError" ||
          error.message?.includes("permission")
        ) {
          errorMessage =
            "Microphone permission denied. Please allow microphone access in your browser settings.";
        } else if (
          error.name === "NotFoundError" ||
          error.message?.includes("device")
        ) {
          errorMessage =
            "No microphone found. Please connect a microphone and try again.";
        } else if (error.message) {
          errorMessage = error.message;
        }

        setMicError(errorMessage);
        setIsMicEnabled(false);
      }
    };

    enableMic();

    return () => {
      if (
        localTrackRef.current &&
        typeof localTrackRef.current.stop === "function"
      ) {
        try {
          localTrackRef.current.stop();
        } catch (error) {
          console.warn("Error stopping track in cleanup:", error);
        }
        localTrackRef.current = null;
      }
    };
  }, [room, isConnected]);

  const toggleMic = async () => {
    if (!room || !isConnected || isAgentSpeaking) return; // Don't allow toggling while agent is speaking

    try {
      setMicError(null);
      if (isMicEnabled) {
        // Disable mic
        const tracks = room.localParticipant.audioTracks;
        for (const [, publication] of tracks) {
          if (publication && publication.track) {
            try {
              await room.localParticipant.unpublishTrack(publication.track);
              if (typeof publication.track.stop === "function") {
                publication.track.stop();
              }
            } catch (error) {
              console.warn("Error unpublishing track:", error);
            }
          }
        }
        if (
          localTrackRef.current &&
          typeof localTrackRef.current.stop === "function"
        ) {
          try {
            localTrackRef.current.stop();
          } catch (error) {
            console.warn("Error stopping local track:", error);
          }
          localTrackRef.current = null;
        }
        setIsMicEnabled(false);
        setIsSpeaking(false);
        setAudioLevels([0, 0, 0, 0, 0]);
        console.log("Microphone disabled");
      } else {
        // Enable mic
        const track = await createLocalAudioTrack();
        await room.localParticipant.publishTrack(track);
        localTrackRef.current = track;
        setIsMicEnabled(true);
        console.log("Microphone enabled");
      }
    } catch (error) {
      console.error("Error toggling microphone:", error);
      let errorMessage = "Failed to toggle microphone";

      if (
        error.name === "NotAllowedError" ||
        error.message?.includes("permission")
      ) {
        errorMessage =
          "Microphone permission denied. Please allow microphone access in your browser settings.";
      } else if (
        error.name === "NotFoundError" ||
        error.message?.includes("device")
      ) {
        errorMessage =
          "No microphone found. Please connect a microphone and try again.";
      } else if (error.message) {
        errorMessage = error.message;
      }

      setMicError(errorMessage);
      setIsMicEnabled(false);
    }
  };

  // Container styles
  const containerStyle = {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: isMobile ? "1.5rem" : "2rem",
    backgroundColor: "rgba(255, 255, 255, 0.8)",
    backdropFilter: "blur(8px)",
    borderRadius: borderRadius["2xl"],
    boxShadow: shadows.lg,
    width: "100%",
    maxWidth: isMobile ? "100%" : "400px",
  };

  // Button container
  const buttonContainerStyle = {
    position: "relative",
    marginBottom: "1rem",
  };

  // Pulsing ring style
  const pulsingRingStyle = {
    position: "absolute",
    inset: 0,
    borderRadius: "50%",
    backgroundColor: colors.aquamarine[400], // CSS variable
    animation: "ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite",
    opacity: 0.75,
  };

  // Button base style
  const getButtonStyle = () => {
    const baseStyle = {
      position: "relative",
      zIndex: 10,
      width: isMobile ? "64px" : "80px",
      height: isMobile ? "64px" : "80px",
      borderRadius: "50%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      border: "none",
      cursor: isConnected ? "pointer" : "not-allowed",
      transition: `all ${transitions.slow} ease-in-out`,
      transform: "scale(1)",
      outline: "none",
      boxShadow: shadows.lg,
    };

    if (micError) {
      return {
        ...baseStyle,
        background: `linear-gradient(135deg, ${colors["rosy-taupe"][500]}, ${colors["rosy-taupe"][600]})`, // CSS variables
        color: "white",
      };
    }

    if (!isConnected) {
      return {
        ...baseStyle,
        backgroundColor: colors.gray[300], // Using CSS variable
        color: colors.gray[600], // Using CSS variable
      };
    }

    if (isMicEnabled) {
      if (isSpeaking) {
        return {
          ...baseStyle,
          background: gradients.aquamarine, // Using centralized gradient
          color: "white",
          boxShadow: `${shadows.lg}, 0 0 20px rgba(38, 217, 145, 0.3)`, // Using rgba for opacity
        };
      } else {
        return {
          ...baseStyle,
          background: gradients["baby-blue-ice"], // Using centralized gradient
          color: "white",
        };
      }
    }

    return {
      ...baseStyle,
      backgroundColor: colors.gray[300], // Using CSS variable
      color: colors.gray[600], // Using CSS variable
    };
  };

  // Equalizer container
  const equalizerContainerStyle = {
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "center",
    gap: "0.25rem",
    height: "48px",
    marginBottom: "1rem",
    width: "100%",
  };

  // Equalizer bar style
  const getBarStyle = (index, level) => {
    const height = Math.max(8, level);
    const color = getBarColor(index); // CSS variable
    const opacity = Math.min(1, level / 50 + 0.3);

    return {
      width: isMobile ? "6px" : "8px",
      height: `${height}%`,
      minHeight: "8px",
      backgroundColor: color,
      borderRadius: `${borderRadius.sm} ${borderRadius.sm} 0 0`,
      transition: `height ${transitions.fast} ease-out, background-color ${transitions.fast} ease-out`,
      opacity,
      boxShadow: level > 20 ? `0 2px 4px rgba(38, 217, 145, 0.25)` : "none", // Using rgba for opacity
    };
  };

  // Status text style
  const statusTextStyle = {
    textAlign: "center",
    fontSize: isMobile ? "0.875rem" : "0.9375rem",
    fontWeight: 500,
  };

  return (
    <div style={containerStyle}>
      {/* Microphone Button with Voice Activity Indicator */}
      <div style={buttonContainerStyle}>
        {/* Pulsing ring when speaking */}
        {isSpeaking && isMicEnabled && (
          <div style={pulsingRingStyle} aria-hidden="true" />
        )}

        {/* Main mic button */}
        <button
          onClick={toggleMic}
          disabled={!isConnected || isAgentSpeaking}
          style={getButtonStyle()}
          onMouseEnter={(e) => {
            if (isConnected && !micError) {
              e.currentTarget.style.transform = "scale(1.1)";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
          }}
          onFocus={(e) => {
            e.currentTarget.style.outline = `3px solid ${colors["baby-blue-ice"][300]}`;
            e.currentTarget.style.outlineOffset = "2px";
          }}
          onBlur={(e) => {
            e.currentTarget.style.outline = "none";
          }}
          title={isMicEnabled ? "Mute microphone" : "Enable microphone"}
          aria-label={isMicEnabled ? "Mute microphone" : "Enable microphone"}
          aria-pressed={isMicEnabled}
        >
          <svg
            width={isMobile ? "24" : "32"}
            height={isMobile ? "24" : "32"}
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ pointerEvents: "none" }}
          >
            {isMicEnabled ? (
              <path
                d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
                fill="currentColor"
              />
            ) : (
              <path
                d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27 7.73 9H3v6h4c0 1.66 1.34 3 3 3s3-1.34 3-3v-1.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4c-.28 0-.5.22-.5.5v3.17l1 1V4.5c0-.28-.22-.5-.5-.5zm5.5 6.5c0 .28.22.5.5.5s.5-.22.5-.5-.22-.5-.5-.5-.5.22-.5.5z"
                fill="currentColor"
              />
            )}
          </svg>
        </button>
      </div>

      {/* Equalizer Bars - Voice Activity Indicator */}
      {isMicEnabled && (
        <div
          style={equalizerContainerStyle}
          aria-label="Voice activity indicator"
        >
          {audioLevels.map((level, index) => (
            <div
              key={index}
              style={getBarStyle(index, level)}
              role="presentation"
            />
          ))}
        </div>
      )}

      {/* Status Text */}
      <div style={statusTextStyle}>
        {micError ? (
          <span style={{ color: colors["blush-rose"][600] }}>{micError}</span>
        ) : isConnected ? (
          isAgentSpeaking ? (
            <span style={{ color: colors["baby-blue-ice"][600] }}>
              Agent is speaking...
            </span>
          ) : isMicEnabled ? (
            <span style={{ color: colors.aquamarine[700] }}>
              {isSpeaking ? "Listening..." : "Microphone enabled"}
            </span>
          ) : (
            <span style={{ color: colors.gray[600] }}>Microphone disabled</span>
          )
        ) : (
          <span style={{ color: colors.gray[500] }}>Not connected</span>
        )}
      </div>
    </div>
  );
};

export default VoiceInterface;
