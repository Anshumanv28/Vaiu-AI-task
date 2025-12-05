"""
LiveKit voice agent for restaurant booking
"""
import asyncio
import os
import json
from dotenv import load_dotenv
from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice import Agent, AgentSession
try:
    from livekit.plugins.openai import STT, TTS, LLM as OpenAILLM
    from livekit.plugins.silero import VAD
except ImportError:
    # Fallback for older versions - plugins might be in different location
    print("WARNING: livekit.plugins not found. Please install: pip install livekit-plugins-openai livekit-plugins-silero")
    raise

from conversation import BookingContext, ConversationState
from prompts import BOOKING_AGENT_SYSTEM_PROMPT
from utils.api_client import BackendAPIClient

# Load environment variables
load_dotenv()

# Initialize backend API client
api_client = BackendAPIClient()


class RestaurantBookingAgent(Agent):
    """Voice agent for restaurant bookings"""
    
    def __init__(self):
        super().__init__(
            instructions=BOOKING_AGENT_SYSTEM_PROMPT,
        )
        self.booking_context = BookingContext()
        self._agent_session = None  # Store session reference
    
    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Handle user turn completion events"""
        try:
            # Extract user text from new_message
            user_text = ""
            if hasattr(new_message, 'content'):
                content = new_message.content
                # Handle if content is a list (like ['Hallo.'])
                if isinstance(content, list):
                    user_text = " ".join(str(item) for item in content if item)
                elif isinstance(content, str):
                    user_text = content
                else:
                    user_text = str(content)
            elif hasattr(new_message, 'text'):
                user_text = new_message.text
            elif isinstance(new_message, str):
                user_text = new_message
            else:
                # Try to get from message object
                user_text = str(new_message)
            
            # Clean up the text
            if isinstance(user_text, list):
                user_text = " ".join(str(item) for item in user_text if item)
            user_text = str(user_text).strip()
                
            if not user_text:
                print(f"⚠️ Could not extract user text from message: {new_message}")
                return
            
            # Provide feedback that we received the user's message
            print(f"🎤 User said: {user_text}")
            print(f"📊 Current booking state: {self.booking_context.state.value}")
            print(f"💬 Processing user input...")
            
            # Update context based on conversation state
            await self._update_context_from_message(user_text)
            
            # Handle state-specific logic
            if self.booking_context.state == ConversationState.FETCHING_WEATHER:
                await self._fetch_weather_and_suggest_seating()
            elif self.booking_context.state == ConversationState.CONFIRMING:
                # User confirmed, create booking
                if "yes" in user_text.lower() or "confirm" in user_text.lower():
                    await self._create_booking()
            elif self.booking_context.state == ConversationState.CREATING_BOOKING:
                # Booking is being created, wait for completion
                pass
        except Exception as e:
            print(f"❌ Error in user speech handler: {e}")
            import traceback
            traceback.print_exc()
    
    async def _update_context_from_message(self, user_text: str):
        """Extract booking information from user message using LLM"""
        # Use LLM to extract structured data from user message
        extraction_prompt = f"""Extract booking information from this user message: "{user_text}"

Current context:
- Number of guests: {self.booking_context.number_of_guests or 'Not set'}
- Date: {self.booking_context.booking_date or 'Not set'}
- Time: {self.booking_context.booking_time or 'Not set'}
- Cuisine: {self.booking_context.cuisine_preference or 'Not set'}
- Special requests: {self.booking_context.special_requests or 'Not set'}

Current state: {self.booking_context.state.value}

Extract and return ONLY a JSON object with any new information provided:
{{
  "number_of_guests": <number or null>,
  "booking_date": "<YYYY-MM-DD or null>",
  "booking_time": "<HH:mm in 24-hour format or null>",
  "cuisine_preference": "<string or null>",
  "special_requests": "<string or null>"
}}

Only include fields that are mentioned in the message. Return valid JSON only."""

        try:
            # Get LLM from session if available
            session = self.session if hasattr(self, 'session') else self._agent_session
            if session and hasattr(session, 'llm'):
                print(f"🤖 Processing user message with LLM...")
                # Create a chat context with the extraction prompt
                from livekit.agents import llm
                chat_ctx = llm.ChatContext().append(
                    role="user",
                    text=extraction_prompt
                )
                # Use the LLM chat method correctly - it returns a stream
                stream = session.llm.chat(chat_ctx=chat_ctx)
                # Collect the response from the stream
                response_text = ""
                try:
                    async for chunk in stream:
                        # Check different possible attributes
                        if hasattr(chunk, 'content') and chunk.content:
                            response_text += str(chunk.content)
                        elif hasattr(chunk, 'text') and chunk.text:
                            response_text += str(chunk.text)
                        elif hasattr(chunk, 'delta') and chunk.delta:
                            # Some streams use 'delta' for incremental content
                            if hasattr(chunk.delta, 'content'):
                                response_text += str(chunk.delta.content)
                            elif isinstance(chunk.delta, str):
                                response_text += chunk.delta
                        elif isinstance(chunk, str):
                            response_text += chunk
                except Exception as stream_error:
                    print(f"⚠️ Error reading LLM stream: {stream_error}")
                    # Try to get the full response if available
                    if hasattr(stream, 'content'):
                        response_text = str(stream.content)
            else:
                # Fallback: simple extraction without LLM
                print(f"⚠️ LLM not available, using simple extraction for: {user_text}")
                return
            
            if not response_text:
                print(f"⚠️ No response from LLM")
                return
            
            print(f"📝 LLM response received: {response_text[:100]}...")
            
            # Try to extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                try:
                    extracted = json.loads(json_str)
                    print(f"✅ Extracted booking data: {extracted}")
                    
                    # Update context
                    updated_fields = []
                    if extracted.get('number_of_guests'):
                        self.booking_context.number_of_guests = int(extracted['number_of_guests'])
                        updated_fields.append(f"guests: {self.booking_context.number_of_guests}")
                    if extracted.get('booking_date'):
                        self.booking_context.booking_date = extracted['booking_date']
                        updated_fields.append(f"date: {self.booking_context.booking_date}")
                        # After getting date, fetch weather
                        if self.booking_context.state == ConversationState.COLLECTING_DATE:
                            self.booking_context.state = ConversationState.FETCHING_WEATHER
                            print(f"🌤️ Date received, will fetch weather for: {self.booking_context.booking_date}")
                    if extracted.get('booking_time'):
                        self.booking_context.booking_time = extracted['booking_time']
                        updated_fields.append(f"time: {self.booking_context.booking_time}")
                    if extracted.get('cuisine_preference'):
                        self.booking_context.cuisine_preference = extracted['cuisine_preference']
                        updated_fields.append(f"cuisine: {self.booking_context.cuisine_preference}")
                    if extracted.get('special_requests'):
                        self.booking_context.special_requests = extracted['special_requests']
                        updated_fields.append(f"requests: {self.booking_context.special_requests}")
                    
                    if updated_fields:
                        print(f"📋 Updated booking context: {', '.join(updated_fields)}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse JSON from LLM response: {e}")
                    print(f"   Response was: {response_text}")
            else:
                print(f"⚠️ No JSON found in LLM response")
        except Exception as e:
            print(f"❌ Error extracting context: {e}")
            import traceback
            traceback.print_exc()
    
    async def _fetch_weather_and_suggest_seating(self):
        """Fetch weather and suggest seating preference"""
        try:
            weather_data = await api_client.get_weather(self.booking_context.booking_date)
            self.booking_context.weather_info = weather_data
            
            # Suggest seating based on weather
            condition = weather_data.get('condition', '').lower()
            temperature = weather_data.get('temperature', 20)
            description = weather_data.get('description', '')
            
            if condition in ['clear', 'sunny'] and temperature > 20:
                suggestion = "The weather looks perfect for outdoor dining! It's sunny and warm. Would you prefer outdoor seating?"
                self.booking_context.seating_preference = "outdoor"
            elif condition in ['rain', 'rainy', 'storm'] or temperature < 15:
                suggestion = f"The weather forecast shows {description.lower()}. I'd recommend our cozy indoor area for your comfort."
                self.booking_context.seating_preference = "indoor"
            else:
                suggestion = f"The weather is {description.lower()} with a temperature of {temperature}°C. Would you prefer indoor or outdoor seating?"
            
            self.booking_context.state = ConversationState.SUGGESTING_SEATING
            
            # Ask for confirmation after suggesting seating
            if self.booking_context.is_complete():
                await self._confirm_booking_details()
            else:
                session = self.session if hasattr(self, 'session') else self._agent_session
                if session:
                    await session.generate_reply(instructions=suggestion)
        except Exception as e:
            print(f"Error fetching weather: {e}")
            session = self.session if hasattr(self, 'session') else self._agent_session
            if session:
                await session.generate_reply(
                    instructions="I'm having trouble checking the weather, but we can still proceed. Would you prefer indoor or outdoor seating?"
                )
    
    async def _confirm_booking_details(self):
        """Confirm all booking details with the user"""
        self.booking_context.state = ConversationState.CONFIRMING
        
        confirmation_text = f"""Let me confirm your booking details:

- Number of guests: {self.booking_context.number_of_guests}
- Date: {self.booking_context.booking_date}
- Time: {self.booking_context.booking_time}
- Cuisine preference: {self.booking_context.cuisine_preference or 'Not specified'}
- Special requests: {self.booking_context.special_requests or 'None'}
- Seating: {self.booking_context.seating_preference}

Does this look correct? Say 'yes' to confirm or let me know if you'd like to change anything."""

        session = self.session if hasattr(self, 'session') else self._agent_session
        if session:
            await session.generate_reply(instructions=confirmation_text)
    
    async def _create_booking(self):
        """Create the booking via backend API"""
        self.booking_context.state = ConversationState.CREATING_BOOKING
        
        try:
            booking_data = self.booking_context.to_booking_data()
            booking = await api_client.create_booking(booking_data)
            
            self.booking_context.booking_id = booking.get('bookingId')
            self.booking_context.state = ConversationState.COMPLETED
            
            success_message = (
                f"Perfect! Your booking has been confirmed. Your booking ID is {self.booking_context.booking_id}. "
                f"We're looking forward to serving {self.booking_context.number_of_guests} guests on {self.booking_context.booking_date} at {self.booking_context.booking_time}. "
                "You'll receive a confirmation email shortly. Is there anything else I can help you with?"
            )
            
            session = self.session if hasattr(self, 'session') else self._agent_session
            if session:
                await session.generate_reply(instructions=success_message)
        except Exception as e:
            self.booking_context.state = ConversationState.ERROR
            self.booking_context.error_message = str(e)
            
            error_msg = str(e).lower()
            session = self.session if hasattr(self, 'session') else self._agent_session
            if session:
                if "time slot" in error_msg or "already booked" in error_msg:
                    await session.generate_reply(
                        instructions="I'm sorry, but that time slot is already booked. Would you like to choose a different date or time?"
                    )
                else:
                    await session.generate_reply(
                        instructions="I'm sorry, there was an error creating your booking. Please try again or contact us directly."
                    )


async def entrypoint(ctx: JobContext):
    """Entry point for the LiveKit agent"""
    await ctx.connect()
    
    # Check if OpenAI API key is available
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key.strip() == "":
        print("WARNING: OPENAI_API_KEY not set. Agent will not function properly.")
        print("Please set OPENAI_API_KEY in your .env file to enable voice interaction.")
        return
    
    # Create agent instance
    agent = RestaurantBookingAgent()
    
    try:
        # Create session with plugins
        session = AgentSession(
            vad=VAD.load(),
            stt=STT(),
            llm=OpenAILLM(model="gpt-3.5-turbo"),
            tts=TTS(),
        )
        
        # Store session reference in agent (using private attribute)
        agent._agent_session = session
        
        # Start the session
        await session.start(room=ctx.room, agent=agent)
        print("Restaurant booking agent started")
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "401" in error_msg or "invalid" in error_msg:
            print(f"ERROR: Invalid OpenAI API key. Please check your OPENAI_API_KEY in .env file.")
            print(f"Error details: {e}")
        else:
            print(f"ERROR starting agent: {e}")
            raise


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
