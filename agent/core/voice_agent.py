"""
Core voice agent class - handles TTS/STT communication only
Delegates business logic to tool handlers
"""
from livekit.agents import function_tool, RunContext
from livekit.agents.voice import Agent, AgentSession
from utils.tool_executor import ToolExecutor
from utils.frontend_communicator import FrontendCommunicator
from typing import Dict, Any, Optional


class VoiceAgent(Agent):
    """Core voice agent handling TTS/STT communication"""
    
    def __init__(self, instructions: str = ""):
        super().__init__(instructions=instructions)
        self.tool_executor = ToolExecutor()
        self.frontend_comm = FrontendCommunicator()
        self._session = None
        self._room = None
    
    @function_tool()
    async def check_weather(
        self,
        ctx: RunContext,
        date: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check weather forecast for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format (e.g., "2024-01-15")
            location: Optional location (defaults to restaurant location)
        
        Returns:
            Weather data including condition, temperature, and description
        """
        params = {'date': date}
        if location:
            params['location'] = location
        result = await self.tool_executor.execute('weather', params)
        return result.get('data', {}) if result.get('success') else {'error': result.get('error', 'Unknown error')}
    
    @function_tool()
    async def check_availability(
        self,
        ctx: RunContext,
        date: str,
        time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if a date/time slot is available for booking.
        
        Args:
            date: Date in YYYY-MM-DD format (e.g., "2024-01-15")
            time: Optional time in HH:mm format (24-hour, e.g., "19:00" for 7 PM)
        
        Returns:
            Availability status with available boolean and existing bookings count
        """
        params = {'date': date}
        if time:
            params['time'] = time
        result = await self.tool_executor.execute('check-availability', params)
        return result.get('data', {}) if result.get('success') else {'error': result.get('error', 'Unknown error')}
    
    @function_tool()
    async def create_booking(
        self,
        ctx: RunContext,
        numberOfGuests: int,
        bookingDate: str,
        bookingTime: str,
        cuisinePreference: Optional[str] = None,
        specialRequests: Optional[str] = None,
        seatingPreference: Optional[str] = None,
        customerName: Optional[str] = None,
        customerEmail: Optional[str] = None,
        customerContact: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new restaurant booking.
        
        Args:
            numberOfGuests: Number of guests (required)
            bookingDate: Date in YYYY-MM-DD format (required)
            bookingTime: Time in HH:mm format, 24-hour (required, e.g., "19:00" for 7 PM)
            cuisinePreference: Optional cuisine preference
            specialRequests: Optional special requests or dietary restrictions
            seatingPreference: Optional seating preference ("indoor" or "outdoor")
            customerName: Optional customer name
            customerEmail: Optional customer email for confirmation
            customerContact: Optional customer contact number
        
        Returns:
            Created booking data including booking ID
        """
        params = {
            'numberOfGuests': numberOfGuests,
            'bookingDate': bookingDate,
            'bookingTime': bookingTime
        }
        if cuisinePreference:
            params['cuisinePreference'] = cuisinePreference
        if specialRequests:
            params['specialRequests'] = specialRequests
        if seatingPreference:
            params['seatingPreference'] = seatingPreference
        if customerName:
            params['customerName'] = customerName
        if customerEmail:
            params['customerEmail'] = customerEmail
        if customerContact:
            params['customerContact'] = customerContact
        
        result = await self.tool_executor.execute('create-booking', params)
        return result.get('data', {}) if result.get('success') else {'error': result.get('error', 'Unknown error')}
    
    @function_tool()
    async def send_email(
        self,
        ctx: RunContext,
        bookingId: str
    ) -> Dict[str, Any]:
        """Send booking confirmation email.
        
        Args:
            bookingId: The booking ID to send confirmation for
        
        Returns:
            Email sending status
        """
        params = {'bookingId': bookingId}
        result = await self.tool_executor.execute('send-email', params)
        return result.get('data', {}) if result.get('success') else {'error': result.get('error', 'Unknown error')}
    
    async def on_agent_turn(self, turn_ctx):
        """
        Allow LLM to generate responses naturally.
        Transcripts are captured via _conversation_item_added callback.
        """
        # Call super() to allow LLM to generate responses
        await super().on_agent_turn(turn_ctx)
    
    async def on_message(self, message):
        """
        Allow LLM to process messages naturally.
        The base Agent class will handle message processing and LLM response generation.
        """
        # Call super() to allow LLM to process messages and generate responses
        await super().on_message(message)
    
    async def on_agent_start(self, session: AgentSession, room=None):
        """Called when agent starts"""
        self._session = session
        self._room = room
        self.frontend_comm.set_session(session, room)
        
        # Intercept agent speech via conversation_item_added callback
        # This is called when the LLM adds messages to the conversation history
        if session and hasattr(session, '_conversation_item_added'):
            original_callback = session._conversation_item_added
            
            def wrapped_callback(item):
                """Intercept conversation items to capture agent responses"""
                # Check if this is an agent/assistant message
                if hasattr(item, 'role') and hasattr(item, 'content'):
                    if item.role == 'assistant' or item.role == 'agent':
                        # Extract text from content (may be string or list)
                        text = None
                        if isinstance(item.content, list):
                            # Join list items into a single string
                            text = ' '.join([str(part) for part in item.content if part]).strip()
                        elif isinstance(item.content, str):
                            text = item.content.strip()
                        else:
                            text = str(item.content).strip()
                        
                        # Send transcript to frontend
                        if text:
                            import asyncio
                            asyncio.create_task(self.send_transcript('agent', text))
                
                # Call original callback if it exists
                if original_callback:
                    return original_callback(item)
            
            session._conversation_item_added = wrapped_callback
        
        # Set up data channel listener for option selections and other messages
        if room:
            import asyncio
            # Listen for data received events - use sync callback that creates async task
            # LiveKit's .on() requires a sync callback, so we wrap the async handler
            def on_data_received(data: bytes, participant, kind, topic):
                # Create async task from sync callback
                asyncio.create_task(self._on_data_received(data, participant, kind, topic))
            
            room.on("data_received", on_data_received)
        
        await self._on_start()
    
    async def _on_data_received(self, data: bytes, participant, kind, topic):
        """Handle data channel messages from frontend"""
        try:
            # Process messages from remote participants (users)
            # In LiveKit, the agent is the local participant, users are remote
            if participant and not participant.is_local:
                import json
                message = json.loads(data.decode('utf-8'))
                
                # Handle option selection
                if message.get('type') == 'option_selected':
                    await self.on_option_selected(message.get('option'))
                
                # Handle user message (typed input) - this is also handled by on_user_turn_completed
                elif message.get('type') == 'user_message':
                    # Log it but let on_user_turn_completed handle it
                    print(f"📨 [AGENT] Received user message via data channel: {message.get('text')}")
        except Exception as e:
            print(f"Error handling data channel message: {e}")
    
    async def on_option_selected(self, option: str):
        """Override this method in subclasses to handle option selections"""
        pass
    
    async def _on_start(self):
        """Override this method in subclasses for custom startup logic"""
        pass
    
    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Override this method in subclasses to handle user input"""
        pass
    
    async def execute_tool(self, tool_name: str, params: dict) -> dict:
        """
        Execute a tool
        Args:
            tool_name: Name of the tool
            params: Tool parameters
        Returns:
            Tool execution result
        """
        # Send state update
        await self.frontend_comm.send_state_update('processing', f'Executing {tool_name}...')
        
        result = await self.tool_executor.execute(tool_name, params)
        
        # Clear processing state
        await self.frontend_comm.send_state_update(None)
        
        return result
    
    async def send_options(self, options: list, message: str = None):
        """Send selectable options to frontend"""
        await self.frontend_comm.send_options(options, message)
    
    async def send_current_speech(self, text: str):
        """Send current speech text to frontend"""
        await self.frontend_comm.send_current_speech(text)
    
    async def send_state_update(self, state: str, message: str = None):
        """Send state update to frontend"""
        await self.frontend_comm.send_state_update(state, message)
    
    async def send_transcript(self, speaker: str, text: str):
        """Send transcript entry to frontend"""
        await self.frontend_comm.send_transcript(speaker, text)
