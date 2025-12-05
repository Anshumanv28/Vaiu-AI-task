import { useState, useEffect, useCallback } from "react";
import { Room, RoomEvent, RemoteParticipant, Track } from "livekit-client";
import { getLiveKitConfig } from "../utils/livekitConfig";

export const useLiveKit = () => {
  const [room, setRoom] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);

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
        setIsAgentTyping(false);
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
            // Agent audio track subscribed - agent is about to speak
            console.log("Agent audio track subscribed");
            setIsAgentTyping(true);

            // Attach audio track to an audio element for playback
            // LiveKit tracks need to be attached to an HTMLAudioElement or HTMLVideoElement
            const audioElement = new Audio();
            audioElement.autoplay = true;
            audioElement.playsInline = true;

            // Attach the track to the audio element
            track.attach(audioElement);

            // Store reference for cleanup
            if (!newRoom._agentAudioElements) {
              newRoom._agentAudioElements = [];
            }
            newRoom._agentAudioElements.push(audioElement);

            console.log("✅ Agent audio track attached to audio element");

            // Ensure audio plays
            audioElement.play().catch((err) => {
              console.warn("Audio autoplay prevented:", err);
            });

            // Listen for when track actually starts playing
            track.on("started", () => {
              console.log("Agent audio started playing");
              setIsAgentTyping(false);
              setIsAgentSpeaking(true); // Agent is now speaking
            });

            track.on("ended", () => {
              console.log("Agent audio ended");
              setIsAgentTyping(false);
              setIsAgentSpeaking(false); // Agent finished speaking
            });

            // Also listen for when track is muted/unmuted
            track.on("muted", () => {
              setIsAgentSpeaking(false);
            });

            track.on("unmuted", () => {
              setIsAgentSpeaking(true);
            });
          }
        }
      );

      // Listen for data channel messages (transcripts from agent)
      newRoom.on(
        RoomEvent.DataReceived,
        (payload, participant, kind, topic) => {
          if (participant instanceof RemoteParticipant) {
            // This is from the agent
            try {
              const text = new TextDecoder().decode(payload);
              if (text && text.trim()) {
                // Try to parse as JSON first
                try {
                  const data = JSON.parse(text);
                  if (data.type === "transcript" || data.text || data.message) {
                    const transcriptText =
                      data.text || data.transcript || data.message;
                    const speaker = data.speaker || "agent";
                    if (transcriptText) {
                      // Agent message received, hide typing indicator
                      setIsAgentTyping(false);
                      setTranscript((prev) => [
                        ...prev,
                        {
                          speaker,
                          text: transcriptText,
                          timestamp: new Date(),
                        },
                      ]);
                    }
                  }
                } catch (parseError) {
                  // Not JSON, treat as plain text transcript
                  setIsAgentTyping(false);
                  setTranscript((prev) => [
                    ...prev,
                    {
                      speaker: "agent",
                      text: text.trim(),
                      timestamp: new Date(),
                    },
                  ]);
                }
              }
            } catch (e) {
              console.error("Error processing data channel message:", e);
            }
          }
        }
      );

      // Connect to room using JWT token
      await newRoom.connect(config.url, token);

      setRoom(newRoom);

      // Set up Web Speech API for user transcript capture
      if (
        "webkitSpeechRecognition" in window ||
        "SpeechRecognition" in window
      ) {
        const SpeechRecognition =
          window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = "en-US"; // Force English-only speech recognition
        recognition.maxAlternatives = 1; // Only return the best match

        recognition.onresult = (event) => {
          const last = event.results.length - 1;
          const text = event.results[last][0].transcript;
          if (text && text.trim()) {
            setTranscript((prev) => [
              ...prev,
              { speaker: "user", text: text.trim(), timestamp: new Date() },
            ]);
          }
        };

        recognition.onerror = (event) => {
          console.error("Speech recognition error:", event.error);
        };

        recognition.start();

        // Store recognition in room for cleanup
        newRoom._speechRecognition = recognition;
      }
    } catch (err) {
      console.error("LiveKit connection error:", err);
      setError(err.message);
      setIsConnecting(false);
    }
  }, [isConnecting, isConnected]);

  const disconnect = useCallback(async () => {
    if (room) {
      // Stop speech recognition if active
      if (room._speechRecognition) {
        room._speechRecognition.stop();
        delete room._speechRecognition;
      }
      // Clean up audio elements
      if (room._agentAudioElements) {
        room._agentAudioElements.forEach((audioEl) => {
          audioEl.pause();
          audioEl.srcObject = null;
        });
        delete room._agentAudioElements;
      }
      await room.disconnect();
      setRoom(null);
      setIsConnected(false);
      setTranscript([]);
      setIsAgentTyping(false);
    }
  }, [room]);

  const addTranscriptEntry = useCallback((speaker, text) => {
    setTranscript((prev) => [
      ...prev,
      { speaker, text, timestamp: new Date() },
    ]);
  }, []);

  const sendTextMessage = useCallback(
    async (text) => {
      if (!room || !isConnected || !text.trim()) {
        return;
      }

      try {
        // Add user message to transcript immediately
        addTranscriptEntry("user", text.trim());

        // Send message to agent via data channel
        const messageData = JSON.stringify({
          type: "user_message",
          text: text.trim(),
          timestamp: new Date().toISOString(),
        });

        await room.localParticipant.publishData(
          new TextEncoder().encode(messageData),
          { reliable: true }
        );

        console.log("✅ Text message sent to agent:", text.trim());
      } catch (error) {
        console.error("Error sending text message:", error);
        setError(`Failed to send message: ${error.message}`);
      }
    },
    [room, isConnected, addTranscriptEntry]
  );

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
    isAgentTyping,
    isAgentSpeaking,
    connect,
    disconnect,
    addTranscriptEntry,
    sendTextMessage,
  };
};
