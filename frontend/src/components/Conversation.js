import React, { useEffect, useRef, useState } from "react";
import { colors, shadows, borderRadius, gradients } from "../utils/styles";
import { useResponsive } from "../hooks/useResponsive";

const Conversation = ({
  transcript,
  isAgentTyping,
  isAgentSpeaking,
  onSendMessage,
  isConnected,
}) => {
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [inputValue, setInputValue] = useState("");
  const { isMobile, isTablet } = useResponsive();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript, isAgentTyping]);

  const handleSendMessage = () => {
    if (inputValue.trim() && onSendMessage) {
      onSendMessage(inputValue.trim());
      setInputValue("");
    }
  };

  // Container style
  const containerStyle = {
    backgroundColor: "rgba(255, 255, 255, 0.8)",
    backdropFilter: "blur(8px)",
    borderRadius: borderRadius["2xl"],
    boxShadow: shadows.lg,
    padding: isMobile ? "1rem" : "1.5rem",
    height: isMobile ? "400px" : isTablet ? "500px" : "600px",
    display: "flex",
    flexDirection: "column",
    width: "100%",
  };

  // Header style
  const headerStyle = {
    fontSize: isMobile ? "1.125rem" : "1.25rem",
    fontWeight: 700,
    color: colors["baby-blue-ice"][800],
    marginBottom: "1rem",
    paddingBottom: "0.5rem",
    borderBottom: `2px solid ${colors["baby-blue-ice"][200]}`,
  };

  // Messages container style
  const messagesContainerStyle = {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "1rem",
    paddingRight: "0.5rem",
    marginBottom: isConnected ? "1rem" : "0",
  };

  // Empty state style
  const emptyStateStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
  };

  const emptyStateTextStyle = {
    color: colors.gray[500],
    textAlign: "center",
    fontStyle: "italic",
  };

  // Message bubble container
  const getMessageContainerStyle = (speaker) => ({
    display: "flex",
    justifyContent: speaker === "user" ? "flex-end" : "flex-start",
    animation: "fadeInSlide 0.3s ease-out forwards",
  });

  // Message bubble style
  const getMessageBubbleStyle = (speaker) => {
    const isUser = speaker === "user";
    return {
      maxWidth: isMobile ? "85%" : "75%",
      borderRadius: borderRadius["2xl"],
      padding: isMobile ? "0.75rem 1rem" : "0.875rem 1.25rem",
      boxShadow: shadows.md,
      background: isUser ? gradients["baby-blue-ice"] : gradients.aquamarine,
      color: "white",
      borderBottomRightRadius: isUser ? borderRadius.sm : borderRadius["2xl"],
      borderBottomLeftRadius: isUser ? borderRadius["2xl"] : borderRadius.sm,
    };
  };

  // Message header style
  const messageHeaderStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "0.25rem",
  };

  const speakerNameStyle = {
    fontSize: "0.75rem",
    fontWeight: 600,
    opacity: 0.9,
  };

  const timestampStyle = {
    fontSize: "0.75rem",
    opacity: 0.75,
    marginLeft: "0.5rem",
  };

  // Message text style
  const messageTextStyle = {
    fontSize: isMobile ? "0.875rem" : "0.9375rem",
    lineHeight: 1.6,
  };

  // Typing indicator container
  const typingContainerStyle = {
    display: "flex",
    justifyContent: "flex-start",
    animation: "fadeIn 0.3s ease-out forwards",
  };

  // Typing indicator bubble
  const typingBubbleStyle = {
    background: gradients.aquamarine,
    color: "white",
    borderRadius: borderRadius["2xl"],
    borderBottomLeftRadius: borderRadius.sm,
    padding: isMobile ? "0.75rem 1rem" : "0.875rem 1.25rem",
    boxShadow: shadows.md,
  };

  // Typing dots container
  const typingDotsStyle = {
    display: "flex",
    gap: "0.25rem",
    alignItems: "center",
    marginTop: "0.25rem",
  };

  // Typing dot style
  const getTypingDotStyle = (delay) => ({
    width: "8px",
    height: "8px",
    backgroundColor: "white",
    borderRadius: "50%",
    animation: `bounce 0.6s infinite alternate`,
    animationDelay: `${delay}s`,
  });

  // Input container style
  const inputContainerStyle = {
    display: "flex",
    gap: "0.5rem",
    paddingTop: "1rem",
    borderTop: `2px solid ${colors["baby-blue-ice"][200]}`,
    alignItems: "center",
  };

  // Input style
  const inputStyle = {
    flex: 1,
    padding: isMobile ? "0.75rem" : "0.875rem 1rem",
    borderRadius: borderRadius.lg,
    border: `2px solid ${colors["baby-blue-ice"][300]}`,
    fontSize: isMobile ? "0.875rem" : "0.9375rem",
    outline: "none",
    transition: "all 0.2s ease",
    backgroundColor: "white",
    color: colors.gray[800],
  };

  // Send button style
  const sendButtonStyle = {
    padding: isMobile ? "0.75rem 1.25rem" : "0.875rem 1.5rem",
    borderRadius: borderRadius.lg,
    border: "none",
    background: gradients["baby-blue-ice"],
    color: "white",
    fontSize: isMobile ? "0.875rem" : "0.9375rem",
    fontWeight: 600,
    cursor: isConnected && inputValue.trim() ? "pointer" : "not-allowed",
    opacity: isConnected && inputValue.trim() ? 1 : 0.6,
    transition: "all 0.2s ease",
    boxShadow: shadows.sm,
  };

  return (
    <div style={containerStyle}>
      <h3 style={headerStyle}>Conversation</h3>

      <div style={messagesContainerStyle}>
        {transcript.length === 0 ? (
          <div style={emptyStateStyle}>
            <p style={emptyStateTextStyle}>
              Start speaking to begin the conversation...
            </p>
          </div>
        ) : (
          <>
            {transcript.map((entry, index) => (
              <div key={index} style={getMessageContainerStyle(entry.speaker)}>
                <div style={getMessageBubbleStyle(entry.speaker)}>
                  <div style={messageHeaderStyle}>
                    <span style={speakerNameStyle}>
                      {entry.speaker === "user" ? "You" : "Agent"}
                    </span>
                    <span style={timestampStyle}>
                      {entry.timestamp
                        ? new Date(entry.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : ""}
                    </span>
                  </div>
                  <div style={messageTextStyle}>{entry.text}</div>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isAgentTyping && (
              <div style={typingContainerStyle}>
                <div style={typingBubbleStyle}>
                  <span style={speakerNameStyle}>Agent</span>
                  <div style={typingDotsStyle}>
                    <div style={getTypingDotStyle(0)} aria-hidden="true" />
                    <div style={getTypingDotStyle(0.15)} aria-hidden="true" />
                    <div style={getTypingDotStyle(0.3)} aria-hidden="true" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Text Input Panel */}
      {isConnected && (
        <div style={inputContainerStyle}>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && inputValue.trim()) {
                handleSendMessage();
              }
            }}
            placeholder={
              isAgentSpeaking
                ? "Agent is speaking..."
                : "Type your message here (or speak)..."
            }
            style={inputStyle}
            disabled={!isConnected || isAgentSpeaking}
          />
          <button
            onClick={handleSendMessage}
            disabled={!isConnected || !inputValue.trim() || isAgentSpeaking}
            style={sendButtonStyle}
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
};

export default Conversation;
