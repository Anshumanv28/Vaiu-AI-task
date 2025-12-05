import React, { useState, useEffect, useRef } from "react";
import { createLocalAudioTrack } from "livekit-client";
import "./VoiceInterface.css";

const VoiceInterface = ({ room, isConnected, onTranscriptUpdate }) => {
  const [isMicEnabled, setIsMicEnabled] = useState(false);
  const [micError, setMicError] = useState(null);
  const localTrackRef = useRef(null);

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
    if (!room || !isConnected) return;

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

  return (
    <div className="voice-interface">
      <button
        className={`mic-button ${isMicEnabled ? "active" : ""}`}
        onClick={toggleMic}
        disabled={!isConnected}
        title={isMicEnabled ? "Mute microphone" : "Enable microphone"}
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
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
      <div className="mic-status">
        {micError ? (
          <span className="status-text error">{micError}</span>
        ) : isConnected ? (
          isMicEnabled ? (
            <span className="status-text">Microphone enabled</span>
          ) : (
            <span className="status-text">Microphone disabled</span>
          )
        ) : (
          <span className="status-text">Not connected</span>
        )}
      </div>
    </div>
  );
};

export default VoiceInterface;
