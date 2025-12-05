"""
LiveKit voice agent for restaurant booking
"""
import asyncio
import os
import json
from datetime import datetime, timedelta
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
        self._greeting_sent = False  # Track if initial greeting was sent
        self._room = None  # Store room reference for data channel
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to YYYY-MM-DD format"""
        if not date_str or date_str.lower() in ['null', 'none', '']:
            return None
        
        date_str = date_str.strip().lower()
        
        # Handle relative dates - check if "today" appears anywhere in the string
        if 'today' in date_str:
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"📅 Normalized '{date_str}' to today: {today}")
            return today
        elif 'tomorrow' in date_str:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"📅 Normalized '{date_str}' to tomorrow: {tomorrow}")
            return tomorrow
        
        # Try to parse as YYYY-MM-DD
        try:
            # Check if it's already in YYYY-MM-DD format
            parsed = datetime.strptime(date_str, '%Y-%m-%d')
            # Validate it's not a past date (unless it's today)
            today = datetime.now().date()
            parsed_date = parsed.date()
            if parsed_date < today:
                print(f"⚠️ Date {date_str} is in the past, using today instead")
                return today.strftime('%Y-%m-%d')
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            # Try other common formats
            try:
                # Try MM/DD/YYYY
                parsed = datetime.strptime(date_str, '%m/%d/%Y')
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # Try DD/MM/YYYY
                    parsed = datetime.strptime(date_str, '%d/%m/%Y')
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    print(f"⚠️ Could not parse date: {date_str}, assuming 'today'")
                    # If we can't parse, assume it's "today" as fallback
                    return datetime.now().strftime('%Y-%m-%d')
    
    async def _send_transcript(self, text: str, speaker: str = "agent"):
        """Send transcript to frontend via data channel"""
        if not self._room:
            return
        try:
            import json
            data = json.dumps({
                "type": "transcript",
                "speaker": speaker,
                "text": text,
                "timestamp": None  # Frontend will add timestamp
            }).encode('utf-8')
            await self._room.local_participant.publish_data(data, reliable=True)
        except Exception as e:
            print(f"⚠️ Error sending transcript: {e}")
    
    async def _generate_reply_with_transcript(self, instructions: str):
        """Generate a reply and send transcript to frontend"""
        session = self.session if hasattr(self, 'session') else self._agent_session
        if session:
            await session.generate_reply(instructions=instructions)
            # Also send as transcript
            await self._send_transcript(instructions, speaker="agent")
    
    async def on_agent_start(self, session):
        """Called when the agent session starts - send initial greeting"""
        self._agent_session = session
        self._greeting_sent = False
        self.booking_context.reset()
        
        # Send initial greeting
        greeting = "Hello! Welcome to our restaurant. I'm here to help you make a reservation. How many guests will be joining us today?"
        print(f"👋 Sending initial greeting...")
        try:
            await self._generate_reply_with_transcript(greeting)
            self._greeting_sent = True
            self.booking_context.state = ConversationState.COLLECTING_GUESTS
            print(f"✅ Greeting sent, state: {self.booking_context.state.value}")
        except Exception as e:
            print(f"❌ Error sending greeting: {e}")
            import traceback
            traceback.print_exc()
    
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
            
            # Send user transcript to frontend
            await self._send_transcript(user_text, speaker="user")
            
            # If this is the first message and greeting wasn't sent, send it
            if not self._greeting_sent:
                await self._send_greeting()
            
            # Update context based on conversation state
            await self._update_context_from_message(user_text)
            
            # Handle state-specific logic
            if self.booking_context.state == ConversationState.FETCHING_WEATHER:
                # Only fetch weather if we have a valid date
                if self.booking_context.booking_date:
                    await self._fetch_weather_and_suggest_seating()
                else:
                    # No valid date, ask for date again
                    self.booking_context.state = ConversationState.COLLECTING_DATE
                    await self._guide_to_next_step()
            elif self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                # User might have provided seating preference, check if we need to move forward
                if self.booking_context.is_complete():
                    self.booking_context.state = ConversationState.CONFIRMING
                    await asyncio.sleep(1)
                    await self._confirm_booking_details()
                else:
                    # Still need more info, guide to next step
                    await self._guide_to_next_step()
            elif self.booking_context.state == ConversationState.CONFIRMING:
                # User confirmed, create booking
                if "yes" in user_text.lower() or "confirm" in user_text.lower() or "okay" in user_text.lower() or "ok" in user_text.lower():
                    await self._create_booking()
                elif "no" in user_text.lower() or "cancel" in user_text.lower():
                    # User wants to cancel or change something
                    await self._ask_for_correction()
            elif self.booking_context.state == ConversationState.CREATING_BOOKING:
                # Booking is being created, wait for completion
                pass
            else:
                # After processing user input, guide to next step
                await self._guide_to_next_step()
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
  "booking_date": "<YYYY-MM-DD format. Convert 'today' to today's date, 'tomorrow' to tomorrow's date. Use actual date, not 'null' string>",
  "booking_time": "<HH:mm in 24-hour format or null>",
  "cuisine_preference": "<string or null>",
  "special_requests": "<string or null>",
  "seating_preference": "<'indoor' or 'outdoor' or null>"
}}

IMPORTANT: 
- If user says "today" or "today would be good", extract today's date in YYYY-MM-DD format (use actual current date)
- If user says "tomorrow", extract tomorrow's date in YYYY-MM-DD format
- For dates, always use the actual date in YYYY-MM-DD format, never the word "today" or "tomorrow"
- Never return the string "null" for dates - use actual date or omit the field
- If user says "no" to special requests, set special_requests to empty string ""
- Only include fields that are mentioned in the message
- Return valid JSON only."""

        try:
            # Get LLM from session if available
            session = self.session if hasattr(self, 'session') else self._agent_session
            if session and hasattr(session, 'llm'):
                print(f"🤖 Processing user message with LLM...")
                # Create a chat context with the extraction prompt
                from livekit.agents import llm
                chat_ctx = llm.ChatContext()
                chat_ctx.add_message(
                    role="user",
                    content=extraction_prompt
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
                    
                    # Update context and state transitions
                    updated_fields = []
                    state_changed = False
                    
                    if extracted.get('number_of_guests'):
                        self.booking_context.number_of_guests = int(extracted['number_of_guests'])
                        updated_fields.append(f"guests: {self.booking_context.number_of_guests}")
                        if self.booking_context.state == ConversationState.COLLECTING_GUESTS:
                            self.booking_context.state = ConversationState.COLLECTING_DATE
                            state_changed = True
                            print(f"✅ Guests collected: {self.booking_context.number_of_guests}, moving to date collection")
                    
                    if extracted.get('booking_date'):
                        date_value = extracted['booking_date']
                        # Normalize date: handle "today", "tomorrow", "null" string, etc.
                        normalized_date = self._normalize_date(date_value)
                        if normalized_date:
                            # Only update if we don't already have a date, or if the new date is different
                            if not self.booking_context.booking_date or self.booking_context.booking_date != normalized_date:
                                self.booking_context.booking_date = normalized_date
                                updated_fields.append(f"date: {self.booking_context.booking_date}")
                                if self.booking_context.state == ConversationState.COLLECTING_DATE:
                                    self.booking_context.state = ConversationState.FETCHING_WEATHER
                                    state_changed = True
                                    print(f"🌤️ Date received: {self.booking_context.booking_date}, will fetch weather")
                        else:
                            print(f"⚠️ Could not normalize date: {date_value}")
                    
                    if extracted.get('booking_time'):
                        self.booking_context.booking_time = extracted['booking_time']
                        updated_fields.append(f"time: {self.booking_context.booking_time}")
                        if self.booking_context.state == ConversationState.COLLECTING_TIME:
                            self.booking_context.state = ConversationState.COLLECTING_CUISINE
                            state_changed = True
                            print(f"✅ Time collected: {self.booking_context.booking_time}, moving to cuisine")
                    
                    if extracted.get('cuisine_preference'):
                        self.booking_context.cuisine_preference = extracted['cuisine_preference']
                        updated_fields.append(f"cuisine: {self.booking_context.cuisine_preference}")
                        if self.booking_context.state == ConversationState.COLLECTING_CUISINE:
                            self.booking_context.state = ConversationState.COLLECTING_REQUESTS
                            state_changed = True
                            print(f"✅ Cuisine collected: {self.booking_context.cuisine_preference}, moving to requests")
                    
                    # Handle special requests - also check for "no" responses
                    user_text_lower = user_text.lower()
                    if extracted.get('special_requests'):
                        # Check if user explicitly said "no" or "none" for special requests
                        if any(phrase in user_text_lower for phrase in ['no special', 'no dietary', 'no requests', 'not allergic', 'nothing', 'no, we', 'no thank']):
                            self.booking_context.special_requests = ""  # Empty string means no special requests
                            updated_fields.append(f"requests: (none)")
                        else:
                            self.booking_context.special_requests = extracted['special_requests']
                            updated_fields.append(f"requests: {self.booking_context.special_requests}")
                        
                        if self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
                            # Check if we have all required info
                            if self.booking_context.is_complete():
                                self.booking_context.state = ConversationState.CONFIRMING
                                state_changed = True
                                print(f"✅ All info collected, ready for confirmation")
                    elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
                        # User responded but didn't provide special requests in JSON - check for "no" responses
                        if any(phrase in user_text_lower for phrase in ['no special', 'no dietary', 'no requests', 'not allergic', 'nothing', 'no, we', 'no thank', 'no we are not', 'no we are', 'no dietary restrictions']):
                            self.booking_context.special_requests = ""
                            updated_fields.append(f"requests: (none)")
                            if self.booking_context.is_complete():
                                self.booking_context.state = ConversationState.CONFIRMING
                                state_changed = True
                                print(f"✅ All info collected (no special requests), ready for confirmation")
                    
                    # Handle seating preference
                    if extracted.get('seating_preference'):
                        seating = extracted['seating_preference'].lower()
                        if seating in ['indoor', 'outdoor']:
                            self.booking_context.seating_preference = seating
                            updated_fields.append(f"seating: {seating}")
                            # If we're suggesting seating and user responds, check if we have all info
                            if self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                                if self.booking_context.is_complete():
                                    self.booking_context.state = ConversationState.CONFIRMING
                                    state_changed = True
                                    print(f"✅ Seating preference collected: {seating}, ready for confirmation")
                                elif not self.booking_context.booking_time:
                                    self.booking_context.state = ConversationState.COLLECTING_TIME
                                    state_changed = True
                                elif not self.booking_context.cuisine_preference:
                                    self.booking_context.state = ConversationState.COLLECTING_CUISINE
                                    state_changed = True
                    
                    if updated_fields:
                        print(f"📋 Updated booking context: {', '.join(updated_fields)}")
                    if state_changed:
                        print(f"🔄 State changed to: {self.booking_context.state.value}")
                        # If state changed to CONFIRMING, trigger confirmation immediately
                        if self.booking_context.state == ConversationState.CONFIRMING:
                            print(f"📋 Triggering confirmation...")
                            # Schedule confirmation to run after current function completes
                            asyncio.create_task(self._confirm_booking_details())
                    
                    # Also check if we're complete after all updates (in case state didn't change but we're now complete)
                    if self.booking_context.is_complete() and self.booking_context.state not in [
                        ConversationState.CONFIRMING, 
                        ConversationState.CREATING_BOOKING, 
                        ConversationState.COMPLETED,
                        ConversationState.ERROR
                    ]:
                        print(f"✅ All required info is now complete, moving to confirmation")
                        self.booking_context.state = ConversationState.CONFIRMING
                        asyncio.create_task(self._confirm_booking_details())
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse JSON from LLM response: {e}")
                    print(f"   Response was: {response_text}")
            else:
                print(f"⚠️ No JSON found in LLM response")
        except Exception as e:
            print(f"❌ Error extracting context: {e}")
            import traceback
            traceback.print_exc()
    
    async def _send_greeting(self):
        """Send initial greeting if not already sent"""
        if self._greeting_sent:
            return
        
        session = self.session if hasattr(self, 'session') else self._agent_session
        if not session:
            return
        
        greeting = "Hello! Welcome to our restaurant. I'm here to help you make a reservation. How many guests will be joining us today?"
        print(f"👋 Sending initial greeting...")
        try:
            await session.generate_reply(instructions=greeting)
            self._greeting_sent = True
            self.booking_context.state = ConversationState.COLLECTING_GUESTS
            print(f"✅ Greeting sent, state: {self.booking_context.state.value}")
        except Exception as e:
            print(f"❌ Error sending greeting: {e}")
    
    async def _guide_to_next_step(self):
        """Guide the user to the next step in the booking flow"""
        session = self.session if hasattr(self, 'session') else self._agent_session
        if not session:
            return
        
        # Don't guide if we're in special states
        if self.booking_context.state in [
            ConversationState.FETCHING_WEATHER,
            ConversationState.CONFIRMING,
            ConversationState.CREATING_BOOKING,
            ConversationState.COMPLETED,
            ConversationState.ERROR
        ]:
            return
        
        # Determine what to ask next based on current state
        next_question = None
        
        if self.booking_context.state == ConversationState.COLLECTING_GUESTS:
            if not self.booking_context.number_of_guests:
                next_question = "How many guests will be joining us today?"
        
        elif self.booking_context.state == ConversationState.COLLECTING_DATE:
            if not self.booking_context.booking_date:
                next_question = "What date would you like to make a reservation for?"
        
        elif self.booking_context.state == ConversationState.COLLECTING_TIME:
            if not self.booking_context.booking_time:
                next_question = "What time would you prefer? We're open from 11 AM to 10 PM."
        
        elif self.booking_context.state == ConversationState.COLLECTING_CUISINE:
            if not self.booking_context.cuisine_preference:
                next_question = "Do you have a cuisine preference? We offer Italian, Chinese, Indian, and more."
        
        elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
            # Special requests are optional
            # If we already have special_requests set (even if empty), and we have all required info, move to confirmation
            if self.booking_context.special_requests is not None and self.booking_context.is_complete():
                # All required info collected, move to confirmation
                self.booking_context.state = ConversationState.CONFIRMING
                await self._confirm_booking_details()
                return
            elif self.booking_context.special_requests is None:
                # Haven't asked yet, ask now
                next_question = "Any special requests or dietary restrictions we should know about?"
        
        elif self.booking_context.state == ConversationState.SUGGESTING_SEATING:
            # After seating suggestion, check if we have all info
            if self.booking_context.is_complete():
                self.booking_context.state = ConversationState.CONFIRMING
                await self._confirm_booking_details()
                return
        
        # Send the next question if we have one
        if next_question:
            print(f"💬 Asking next question: {next_question}")
            try:
                await self._generate_reply_with_transcript(next_question)
            except Exception as e:
                print(f"❌ Error asking next question: {e}")
    
    async def _ask_for_correction(self):
        """Ask user what they'd like to change"""
        await self._generate_reply_with_transcript(
            "What would you like to change? You can modify the date, time, number of guests, or any other details."
        )
    
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
            
            await self._generate_reply_with_transcript(suggestion)
            
            # After suggesting seating, check if we need to collect more info
            if not self.booking_context.booking_time:
                self.booking_context.state = ConversationState.COLLECTING_TIME
                # Wait a bit for user to respond about seating, then ask for time
                await asyncio.sleep(2)
                await self._guide_to_next_step()
            elif not self.booking_context.cuisine_preference:
                self.booking_context.state = ConversationState.COLLECTING_CUISINE
                await asyncio.sleep(2)
                await self._guide_to_next_step()
            elif self.booking_context.is_complete():
                # All required info collected, wait a bit then move to confirmation
                await asyncio.sleep(2)
                if self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                    self.booking_context.state = ConversationState.CONFIRMING
                    await self._confirm_booking_details()
        except Exception as e:
            print(f"Error fetching weather: {e}")
            # If weather fetch fails, move to suggesting seating anyway
            self.booking_context.state = ConversationState.SUGGESTING_SEATING
            await self._generate_reply_with_transcript(
                "I'm having trouble checking the weather, but we can still proceed. Would you prefer indoor or outdoor seating?"
            )
            # After asking about seating, check what info we still need
            if not self.booking_context.booking_time:
                self.booking_context.state = ConversationState.COLLECTING_TIME
            elif not self.booking_context.cuisine_preference:
                self.booking_context.state = ConversationState.COLLECTING_CUISINE
            elif self.booking_context.is_complete():
                # All required info collected, move to confirmation
                self.booking_context.state = ConversationState.CONFIRMING
                await asyncio.sleep(2)
                await self._confirm_booking_details()
    
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

        await self._generate_reply_with_transcript(confirmation_text)
    
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
            
            await self._generate_reply_with_transcript(success_message)
        except Exception as e:
            self.booking_context.state = ConversationState.ERROR
            self.booking_context.error_message = str(e)
            
            error_msg = str(e).lower()
            if "time slot" in error_msg or "already booked" in error_msg:
                await self._generate_reply_with_transcript(
                    "I'm sorry, but that time slot is already booked. Would you like to choose a different date or time?"
                )
            else:
                await self._generate_reply_with_transcript(
                    "I'm sorry, there was an error creating your booking. Please try again or contact us directly."
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
        # Using cost-effective models:
        # - LLM: gpt-4o-mini (cheaper than gpt-3.5-turbo, better performance)
        # - STT: gpt-4o-mini-transcribe (default, cost-effective)
        # - TTS: gpt-4o-mini-tts (default, cost-effective)
        session = AgentSession(
            vad=VAD.load(),
            stt=STT(),  # Uses gpt-4o-mini-transcribe by default
            llm=OpenAILLM(model="gpt-4o-mini"),  # Cheaper and better than gpt-3.5-turbo
            tts=TTS(),  # Uses gpt-4o-mini-tts by default
        )
        
        # Store session and room reference in agent (using private attribute)
        agent._agent_session = session
        agent._room = ctx.room
        
        # Start the session
        await session.start(room=ctx.room, agent=agent)
        print("Restaurant booking agent started")
        
        # Send initial greeting after session starts
        try:
            await agent.on_agent_start(session)
        except Exception as e:
            print(f"⚠️ Could not send initial greeting: {e}")
            # Fallback: greeting will be sent on first user message
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
