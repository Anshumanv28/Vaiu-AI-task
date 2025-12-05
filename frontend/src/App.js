import React, { useState } from "react";
import { useLiveKit } from "./hooks/useLiveKit";
import VoiceInterface from "./components/VoiceInterface";
import Conversation from "./components/Conversation";
import BookingConfirmation from "./components/BookingConfirmation";
import "./App.css";

function App() {
  const {
    room,
    isConnected,
    isConnecting,
    error,
    transcript,
    connect,
    disconnect,
  } = useLiveKit();
  const [booking, setBooking] = useState(null);

  const handleConnect = async () => {
    await connect();
  };

  const handleDisconnect = async () => {
    await disconnect();
    setBooking(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Restaurant Voice Booking Agent</h1>
        <p className="subtitle">Book your table through natural conversation</p>
      </header>

      <main className="App-main">
        <div className="connection-section">
          {!isConnected && !isConnecting && (
            <button className="connect-button" onClick={handleConnect}>
              Connect to Agent
            </button>
          )}

          {isConnecting && (
            <div className="connecting">
              <div className="spinner"></div>
              <p>Connecting to agent...</p>
            </div>
          )}

          {isConnected && (
            <button className="disconnect-button" onClick={handleDisconnect}>
              Disconnect
            </button>
          )}

          {error && (
            <div className="error-message">
              <p>Error: {error}</p>
            </div>
          )}
        </div>

        {isConnected && (
          <>
            <VoiceInterface
              room={room}
              isConnected={isConnected}
              onTranscriptUpdate={(entry) => {
                // This will be handled by the conversation component
              }}
            />

            <div className="content-grid">
              <Conversation transcript={transcript} />
              {booking && <BookingConfirmation booking={booking} />}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
