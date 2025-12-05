import { useState, useEffect, useCallback } from "react";
import { Room, RoomEvent, RemoteParticipant, Track } from "livekit-client";
import { getLiveKitConfig } from "../utils/livekitConfig";

export const useLiveKit = () => {
  const [room, setRoom] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [transcript, setTranscript] = useState([]);

  const connect = useCallback(async () => {
    if (isConnecting || isConnected) return;

    try {
      setIsConnecting(true);
      setError(null);

      const config = getLiveKitConfig();

      // Generate a unique room name and participant name
      const roomName = `restaurant-booking-${Date.now()}`;
      const participantName = `user-${Date.now()}`;

      // Fetch JWT token from backend
      const tokenResponse = await fetch(
        `${config.backendUrl}/api/livekit/token`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            roomName,
            participantName,
          }),
        }
      );

      if (!tokenResponse.ok) {
        const errorData = await tokenResponse.json();
        throw new Error(errorData.error || "Failed to get access token");
      }

      const { token } = await tokenResponse.json();

      if (!token) {
        throw new Error("No token received from server");
      }

      // Create a new room
      const newRoom = new Room();

      // Set up event listeners
      newRoom.on(RoomEvent.Connected, () => {
        console.log("Connected to LiveKit room");
        setIsConnected(true);
        setIsConnecting(false);
      });

      newRoom.on(RoomEvent.Disconnected, () => {
        console.log("Disconnected from LiveKit room");
        setIsConnected(false);
        setIsConnecting(false);
      });

      newRoom.on(RoomEvent.ParticipantConnected, (participant) => {
        console.log("Participant connected:", participant.identity);
      });

      newRoom.on(
        RoomEvent.TrackSubscribed,
        (track, publication, participant) => {
          if (
            track.kind === Track.Kind.Audio &&
            participant instanceof RemoteParticipant
          ) {
            // Agent audio track subscribed
            console.log("Agent audio track subscribed");
          }
        }
      );

      // Connect to room using JWT token
      await newRoom.connect(config.url, token);

      setRoom(newRoom);
    } catch (err) {
      console.error("LiveKit connection error:", err);
      setError(err.message);
      setIsConnecting(false);
    }
  }, [isConnecting, isConnected]);

  const disconnect = useCallback(async () => {
    if (room) {
      await room.disconnect();
      setRoom(null);
      setIsConnected(false);
      setTranscript([]);
    }
  }, [room]);

  const addTranscriptEntry = useCallback((speaker, text) => {
    setTranscript((prev) => [
      ...prev,
      { speaker, text, timestamp: new Date() },
    ]);
  }, []);

  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect();
      }
    };
  }, [room]);

  return {
    room,
    isConnected,
    isConnecting,
    error,
    transcript,
    connect,
    disconnect,
    addTranscriptEntry,
  };
};
