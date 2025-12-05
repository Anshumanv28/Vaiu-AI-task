import React from "react";
import "./Conversation.css";

const Conversation = ({ transcript }) => {
  return (
    <div className="conversation-container">
      <h3 className="conversation-title">Conversation</h3>
      <div className="conversation-messages">
        {transcript.length === 0 ? (
          <div className="empty-state">
            <p>Start speaking to begin the conversation...</p>
          </div>
        ) : (
          transcript.map((entry, index) => (
            <div
              key={index}
              className={`message ${
                entry.speaker === "user" ? "user-message" : "agent-message"
              }`}
            >
              <div className="message-header">
                <span className="speaker">
                  {entry.speaker === "user" ? "You" : "Agent"}
                </span>
                <span className="timestamp">
                  {entry.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <div className="message-content">{entry.text}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Conversation;
