"""
LiveKit voice agent for restaurant booking
"""
import asyncio
import os
import json
import re
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
from utils.email_extractor import extract_email, is_valid_email
from utils.flow_manager import get_next_question, should_collect_email, get_next_state

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
        self._is_speaking = False  # Track if agent is currently speaking
        self._waiting_for_response = False  # Track if we're waiting for user response
        self._last_extracted_data = None  # Store last extracted data for confirmation
        self._last_question_asked = None  # Track last question asked to prevent duplicates
        self._last_confirmation_sent = None  # Track last confirmation to prevent duplicates
    
    
    def _extract_number_from_text(self, text: str) -> int:
        """Extract number from text using regex fallback for number words"""
        if not text:
            return None
        
        text_lower = text.lower().strip()
        
        # First try to find digits
        digit_match = re.search(r'\d+', text)
        if digit_match:
            return int(digit_match.group())
        
        # Map common number words to digits
        number_words = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
            'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
        }
        
        # Check for number words
        for word, num in number_words.items():
            if word in text_lower:
                return num
        
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to YYYY-MM-DD format"""
        if not date_str or date_str.lower() in ['null', 'none', '']:
            return None
        
        date_str_original = date_str.strip()
        date_str = date_str_original.lower()
        
        # Handle relative dates - check if "today" appears anywhere in the string
        if 'today' in date_str:
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"📅 Normalized '{date_str_original}' to today: {today}")
            return today
        elif 'tomorrow' in date_str:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"📅 Normalized '{date_str_original}' to tomorrow: {tomorrow}")
            return tomorrow
        
        # Normalize month names (handle Norwegian and other variations)
        month_replacements = {
            'desember': 'december', 'januar': 'january', 'februar': 'february',
            'mars': 'march', 'april': 'april', 'mai': 'may', 'juni': 'june',
            'juli': 'july', 'august': 'august', 'september': 'september',
            'oktober': 'october', 'november': 'november'
        }
        for norwegian, english in month_replacements.items():
            date_str = date_str.replace(norwegian, english)
        
        # Try to parse as YYYY-MM-DD first
        try:
            parsed = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now().date()
            parsed_date = parsed.date()
            # Don't fallback to today - return the date as extracted (LLM should handle year correctly)
            # If it's in the past, that's an extraction error that should be handled by LLM, not by fallback
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try formats with month names (e.g., "27. december", "27th December", "December 27", "Oktober")
        month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                       'july', 'august', 'september', 'october', 'november', 'december']
        
        # Check if input is just a month name (e.g., "Oktober", "October")
        # In this case, assume current month and current year, or if current month has passed, next occurrence
        if date_str in month_names or date_str.rstrip('.') in month_names:
            month_name = date_str.rstrip('.').lower()
            month_num = month_names.index(month_name) + 1
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            
            # If the requested month is in the past this year, use next year
            # Otherwise use current year
            if month_num < current_month:
                target_year = current_year + 1
            else:
                target_year = current_year
            
            # Use the 1st of the month as default
            result = f"{target_year}-{month_num:02d}-01"
            print(f"📅 [DATE] Month-only input '{date_str_original}' → '{result}' (using 1st of month)")
            return result
        
        for month_name in month_names:
            if month_name in date_str:
                # Try various formats with month names
                formats_to_try = [
                    '%d. %B %Y',      # "27. December 2025"
                    '%d %B %Y',       # "27 December 2025"
                    '%B %d, %Y',      # "December 27, 2025"
                    '%d %B',          # "27 December" (assume current year)
                    '%d. %B',         # "27. December" (assume current year)
                    '%dth %B %Y',     # "27th December 2025"
                    '%dth %B',        # "27th December" (assume current year)
                    '%B',             # "October" or "Oktober" (just month name)
                ]
                
                for fmt in formats_to_try:
                    try:
                        parsed = datetime.strptime(date_str, fmt)
                        # If year not in format, use current year
                        if '%Y' not in fmt:
                            current_year = datetime.now().year
                            current_month = datetime.now().month
                            parsed_month = parsed.month
                            # If the month is in the past, use next year
                            if parsed_month < current_month:
                                parsed = parsed.replace(year=current_year + 1)
                            else:
                                parsed = parsed.replace(year=current_year)
                        
                        # Don't check if date is in past - return as extracted
                        # If year is missing, use current year (already handled above)
                        result = parsed.strftime('%Y-%m-%d')
                        print(f"📅 [DATE] Normalized '{date_str_original}' to: {result}")
                        return result
                    except ValueError:
                        continue
        
        # Try numeric formats
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
                try:
                    # Try DD.MM.YYYY
                    parsed = datetime.strptime(date_str, '%d.%m.%Y')
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    pass
        
        # If all parsing fails, don't default to today - return None so LLM can try again
        print(f"⚠️ Could not parse date: {date_str_original}, returning None")
        return None
    
    def _format_user_message_for_ui(self, extracted: dict, updated_fields: list) -> str:
        """Format the user's message as understood by the LLM for UI display"""
        # Build a clean message showing what the agent understood
        parts = []
        
        if extracted.get('number_of_guests'):
            parts.append(f"{extracted['number_of_guests']} guest{'s' if extracted['number_of_guests'] > 1 else ''}")
        
        if extracted.get('booking_date'):
            # Format date nicely for display
            try:
                from datetime import datetime
                date_obj = datetime.strptime(extracted['booking_date'], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%B %d, %Y')
                parts.append(f"{formatted_date}")
            except:
                parts.append(extracted['booking_date'])
        
        if extracted.get('booking_time'):
            # Format time nicely for display
            time_str = extracted['booking_time']
            try:
                from datetime import datetime
                time_obj = datetime.strptime(time_str, '%H:%M')
                formatted_time = time_obj.strftime('%I:%M %p').lstrip('0')
                parts.append(f"{formatted_time}")
            except:
                parts.append(time_str)
        
        if extracted.get('seating_preference'):
            parts.append(f"{extracted['seating_preference']} seating")
        
        if extracted.get('cuisine_preference'):
            parts.append(f"{extracted['cuisine_preference']} cuisine")
        
        if extracted.get('special_requests'):
            parts.append(f"{extracted['special_requests']}")
        
        if extracted.get('customer_email'):
            parts.append(f"email: {extracted['customer_email']}")
        
        if parts:
            return ", ".join(parts)
        
        # Fallback: if nothing was extracted, return None (don't show anything)
        return None
    
    async def _send_transcript(self, text: str, speaker: str = "agent"):
        """Send transcript to frontend via data channel"""
        # ========== LOGGING: UI OUTPUT ==========
        print(f"")
        print(f"=" * 80)
        print(f"📤 [UI OUTPUT] Sending to frontend - Speaker: {speaker}")
        print(f"   Text: '{text}'")
        print(f"=" * 80)
        try:
            import json
            data = json.dumps({
                "type": "transcript",
                "speaker": speaker,
                "text": text,
                "timestamp": None  # Frontend will add timestamp
            }).encode('utf-8')
            
            # Try multiple methods to send data - ensure it's sent reliably
            sent = False
            if self._room and hasattr(self._room, 'local_participant'):
                try:
                    await self._room.local_participant.publish_data(data, reliable=True)
                    print(f"✅ Transcript sent via room.local_participant: {text[:50]}...")
                    sent = True
                except Exception as e:
                    print(f"⚠️ Failed to send via room.local_participant: {e}")
            
            if not sent and self._agent_session and hasattr(self._agent_session, 'participant'):
                try:
                    await self._agent_session.participant.publish_data(data, reliable=True)
                    print(f"✅ Transcript sent via session.participant: {text[:50]}...")
                    sent = True
                except Exception as e:
                    print(f"⚠️ Failed to send via session.participant: {e}")
            
            if not sent and self._agent_session and hasattr(self._agent_session, 'room'):
                try:
                    room = self._agent_session.room
                    if room and hasattr(room, 'local_participant'):
                        await room.local_participant.publish_data(data, reliable=True)
                        print(f"✅ Transcript sent via session.room.local_participant: {text[:50]}...")
                        sent = True
                except Exception as e:
                    print(f"⚠️ Failed to send via session.room.local_participant: {e}")
            
            if not sent:
                print(f"⚠️ Cannot find method to publish data")
                print(f"   Room: {self._room}")
                print(f"   Session: {self._agent_session}")
                if self._agent_session:
                    print(f"   Session.room: {getattr(self._agent_session, 'room', None)}")
        except Exception as e:
            print(f"⚠️ Error sending transcript: {e}")
            import traceback
            traceback.print_exc()
    
    async def _generate_reply_with_transcript(self, instructions: str, allow_interruptions: bool = False):
        """Generate a reply and send transcript to frontend"""
        session = self.session if hasattr(self, 'session') else self._agent_session
        if not session:
            print("⚠️ No session available for generating reply")
            return
            
        self._is_speaking = True  # Mark agent as speaking
        try:
            # Send transcript first so it appears immediately in the UI
            print(f"📤 Sending transcript: {instructions[:50]}...")
            await self._send_transcript(instructions, speaker="agent")
            
            # Use say() for direct TTS - this will speak the text immediately via TTS
            # generate_reply() uses LLM which might not trigger TTS for simple messages
            print(f"🔊 Speaking via TTS...")
            if hasattr(session, 'say'):
                try:
                    await session.say(instructions, allow_interruptions=allow_interruptions)
                    print(f"✅ TTS completed via say()")
                except Exception as say_error:
                    print(f"⚠️ say() failed: {say_error}, falling back to generate_reply")
                    await session.generate_reply(instructions=instructions)
            else:
                # Fallback to generate_reply if say() is not available
                print(f"⚠️ say() not available, using generate_reply")
                await session.generate_reply(instructions=instructions)
        except Exception as e:
            print(f"❌ Error in _generate_reply_with_transcript: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Wait a moment after speaking to ensure TTS completes
            await asyncio.sleep(0.5)
            self._is_speaking = False  # Mark agent as done speaking
    
    async def on_agent_start(self, session):
        """Called when the agent session starts - send initial greeting"""
        self._agent_session = session
        # Get room from session or context
        if hasattr(session, 'room'):
            self._room = session.room
        elif hasattr(session, '_room'):
            self._room = session._room
        self._greeting_sent = False
        self.booking_context.reset()
        self._last_question_asked = None  # Reset question tracking
        self._last_confirmation_sent = None  # Reset confirmation tracking
        
        # Send initial greeting immediately with allow_interruptions=False
        # This ensures the greeting completes fully before user can interrupt
        greeting = "Hello! Welcome to our restaurant. I'm here to help you make a reservation. How many guests will be joining us today?"
        print(f"👋 Sending initial greeting...")
        print(f"🔍 Room reference: {self._room}")
        print(f"🔍 Session: {session}")
        try:
            # Use allow_interruptions=False to ensure greeting completes
            await self._generate_reply_with_transcript(greeting, allow_interruptions=False)
            self._greeting_sent = True
            self.booking_context.state = ConversationState.COLLECTING_GUESTS
            self._last_question_asked = "collecting_guests_guests"  # Mark greeting question as asked
            print(f"✅ Greeting sent, state: {self.booking_context.state.value}")
        except Exception as e:
            print(f"❌ Error sending greeting: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Handle user turn completion events"""
        # Don't process user input while agent is speaking
        if self._is_speaking:
            print("⏸️ Agent is speaking, ignoring user input for now")
            return
        
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
            
            # ========== LOGGING: STT INPUT ==========
            print(f"")
            print(f"=" * 80)
            print(f"📥 [STT INPUT] Raw transcription received: '{user_text}'")
            print(f"📊 [STATE] Current booking state: {self.booking_context.state.value}")
            print(f"💬 [PROCESSING] Starting user input processing...")
            print(f"=" * 80)
            
            # DON'T send raw user transcript to frontend immediately
            # Only send the finalized/processed response after LLM extraction
            # This ensures the UI shows only what the agent understood, not raw STT output
            print(f"ℹ️ [UI] Raw STT transcription received, waiting for LLM processing before sending to UI")
            
            # Handle CONFIRMING state FIRST - before any extraction
            # In CONFIRMING state, we only care about yes/no/confirm/cancel
            if self.booking_context.state == ConversationState.CONFIRMING:
                user_text_lower = user_text.lower().strip()
                # Check for confirmation
                if "yes" in user_text_lower or "confirm" in user_text_lower or "okay" in user_text_lower or "ok" in user_text_lower:
                    await self._create_booking()
                elif "no" in user_text_lower or "cancel" in user_text_lower:
                    # User wants to cancel or change something
                    await self._ask_for_correction()
                else:
                    # User said something else - might want to change a specific field
                    # Allow extraction but it will be handled as a correction
                    self._waiting_for_response = True
                    await self._update_context_from_message(user_text)
                    # After extraction, guide to next step or re-confirm
                    await self._guide_to_next_step()
                return
            
            # Filter out confirmatory responses that are just acknowledgments
            # These shouldn't be treated as answers to questions
            user_text_lower = user_text.lower().strip()
            # Normalize for comparison (remove punctuation)
            user_text_normalized = user_text_lower.rstrip('.,!?')
            confirmatory_phrases = ['ok', 'okay', 'sure', 'great', 'good', 'fine', 'alright', 'yes', 'yeah', 'yep', 'yup', 'cool', 'nice', 'perfect', 'awesome', 'excellent']
            
            # Check if the user's response is ONLY a confirmatory phrase (not a real answer)
            is_only_confirmatory = user_text_normalized in confirmatory_phrases or any(
                user_text_normalized == phrase for phrase in confirmatory_phrases
            )
            
            # If it's just a confirmatory response, don't process it as an answer - just acknowledge and continue
            if is_only_confirmatory:
                print(f"ℹ️ User gave confirmatory response, not processing as answer")
                # Don't update context, just continue to next step
                await self._guide_to_next_step()
                return
            
            # Set waiting flag to prevent mixing questions
            self._waiting_for_response = True
            
            # Don't send greeting again if already sent - on_agent_start should handle it
            # This prevents duplicate greetings
            
            # Update context based on conversation state
            await self._update_context_from_message(user_text)
            
            # Handle state-specific logic
            if self.booking_context.state == ConversationState.FETCHING_WEATHER:
                # Only fetch weather if we have a valid date and time
                if self.booking_context.booking_date and self.booking_context.booking_time:
                    await self._fetch_weather_and_suggest_seating()
                elif not self.booking_context.booking_date:
                    # No valid date, ask for date again
                    self.booking_context.state = ConversationState.COLLECTING_DATE
                    await self._guide_to_next_step()
                elif not self.booking_context.booking_time:
                    # No valid time, ask for time
                    self.booking_context.state = ConversationState.COLLECTING_TIME
                    await self._guide_to_next_step()
            elif self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                # User responded to seating question
                # After seating is confirmed, ALWAYS move to collecting cuisine
                # Don't check is_complete() here - we need to ask cuisine, requests, email first
                if self.booking_context.seating_preference:
                    # Seating preference is set, move to cuisine collection
                    self.booking_context.state = ConversationState.COLLECTING_CUISINE
                    await self._guide_to_next_step()
                else:
                    # Seating not set yet, wait for it or ask again
                    await self._guide_to_next_step()
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
            # Clear waiting flag on error
            self._waiting_for_response = False
    
    async def _update_context_from_message(self, user_text: str):
        """Extract booking information from user message using LLM"""
        # ========== LOGGING: LLM EXTRACTION START ==========
        print(f"")
        print(f"=" * 80)
        print(f"🤖 [LLM EXTRACTION] Starting extraction for: '{user_text}'")
        print(f"📊 [CONTEXT] Current state: {self.booking_context.state.value}")
        print(f"   - Guests: {self.booking_context.number_of_guests or 'Not set'}")
        print(f"   - Date: {self.booking_context.booking_date or 'Not set'}")
        print(f"   - Time: {self.booking_context.booking_time or 'Not set'}")
        print(f"   - Cuisine: {self.booking_context.cuisine_preference or 'Not set'}")
        print(f"   - Requests: {self.booking_context.special_requests or 'Not set'}")
        print(f"   - Email: {self.booking_context.customer_email or 'Not set'}")
        print(f"=" * 80)
        
        # Use LLM to extract structured data from user message
        extraction_prompt = f"""Extract booking information from this user message: "{user_text}"

Current context:
- Number of guests: {self.booking_context.number_of_guests or 'Not set'}
- Date: {self.booking_context.booking_date or 'Not set'}
- Time: {self.booking_context.booking_time or 'Not set'}
- Cuisine: {self.booking_context.cuisine_preference or 'Not set'}
- Special requests: {self.booking_context.special_requests or 'Not set'}
- Email: {self.booking_context.customer_email or 'Not set'}

Current state: {self.booking_context.state.value}

Extract and return ONLY a JSON object with any new information provided:
{{
  "number_of_guests": <number or null>,
  "booking_date": "<YYYY-MM-DD format. Convert 'today' to today's date, 'tomorrow' to tomorrow's date. Use actual date, not 'null' string>",
  "booking_time": "<HH:mm in 24-hour format or null>",
  "cuisine_preference": "<string or null>",
  "special_requests": "<string or null>",
  "customer_email": "<valid email address or null>",
  "seating_preference": "<'indoor' or 'outdoor' or null>"
}}

IMPORTANT: Even if the transcription is in a different script (e.g., Urdu, Hindi), try to understand the user's intent.
For example, if you see "سیونتھ آف ڈسمبر" or "ساتویں دسمبر" or similar, the user likely said "seventh of December" or "7th of December" in English.
Extract the booking information based on the MEANING and INTENT, not just the literal transcription.
Common patterns:
- "سیونتھ" or "ساتویں" = "seventh" or "7th"
- "دسمبر" or "ڈسمبر" = "December"
- "آف" = "of"
- Numbers in Urdu/Hindi script often correspond to English numbers
Extract dates, times, and numbers based on what the user MEANT to say in English, not the script they appear in.

IMPORTANT EXTRACTION RULES:
1. NUMBER OF GUESTS:
   - Convert number words to digits: "two" → 2, "three" → 3, "five" → 5
   - Extract from phrases: "two guests" → 2, "for 4 people" → 4
   - Examples: "two" → 2, "two guests" → 2, "for 3" → 3, "five people" → 5

2. DATES:
   - If user says "today" or "today would be good", extract today's date in YYYY-MM-DD format (use actual current date)
   - If user says "tomorrow", extract tomorrow's date in YYYY-MM-DD format
   - For dates, always use the actual date in YYYY-MM-DD format, never the word "today" or "tomorrow"
   - Never return the string "null" for dates - use actual date or omit the field
   - Examples: "today" → "2025-12-05" (actual date), "7th December" → "2025-12-07"

3. TIMES:
   - Convert to 24-hour format: "5 PM" → "17:00", "12 PM" → "12:00", "11:30 AM" → "11:30"
   - Examples: "5pm" → "17:00", "12 PM" → "12:00", "11:30 AM" → "11:30"

4. SPECIAL REQUESTS:
   - If user says "no" to special requests, set special_requests to empty string ""
   - Extract dietary restrictions, celebrations, etc.

5. GENERAL:
   - Only include fields that are mentioned in the message
   - Return valid JSON only
   - Be robust to multilingual input and variations"""

        try:
            # Get LLM from session if available
            session = self.session if hasattr(self, 'session') else self._agent_session
            if session and hasattr(session, 'llm'):
                print(f"🤖 [LLM] Sending extraction prompt to LLM...")
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
                print(f"⚠️ [LLM] No response from LLM")
                return
            
            print(f"📝 [LLM RESPONSE] Raw LLM output: {response_text[:200]}...")
            
            # Try to extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                try:
                    extracted = json.loads(json_str)
                    print(f"")
                    print(f"=" * 80)
                    print(f"✅ [LLM EXTRACTION RESULT] Parsed JSON: {json.dumps(extracted, indent=2)}")
                    print(f"=" * 80)
                    
                    # Validate extraction - apply regex fallback for number_of_guests if LLM failed
                    if extracted.get('number_of_guests') is None and self.booking_context.state == ConversationState.COLLECTING_GUESTS:
                        # Try regex fallback for number extraction
                        number_from_text = self._extract_number_from_text(user_text)
                        if number_from_text:
                            extracted['number_of_guests'] = number_from_text
                            print(f"🔧 Used regex fallback to extract number: {number_from_text}")
                    
                    # Store extracted data for confirmation
                    self._last_extracted_data = extracted.copy()
                    
                    # Update context and state transitions
                    updated_fields = []
                    extraction_successful = False
                    
                    if extracted.get('number_of_guests'):
                        try:
                            num_guests = int(extracted['number_of_guests'])
                            if num_guests > 0:
                                # POST-PROCESSING: Only add to updated_fields if it's actually new or changed
                                if not self.booking_context.number_of_guests or self.booking_context.number_of_guests != num_guests:
                                    self.booking_context.number_of_guests = num_guests
                                    updated_fields.append(f"guests: {self.booking_context.number_of_guests}")
                                    extraction_successful = True
                                    if self.booking_context.state == ConversationState.COLLECTING_GUESTS:
                                        # Don't change state yet - wait for confirmation
                                        print(f"✅ Guests extracted: {self.booking_context.number_of_guests}, will confirm before moving to date")
                                else:
                                    print(f"ℹ️ [POST-PROCESSING] Guests already set to {num_guests}, skipping duplicate extraction")
                        except (ValueError, TypeError):
                            print(f"⚠️ Invalid number_of_guests value: {extracted['number_of_guests']}")
                    
                    if extracted.get('booking_date'):
                        date_value = extracted['booking_date']
                        print(f"📅 [DATE EXTRACTION] LLM extracted date: '{date_value}'")
                        # Normalize date: handle "today", "tomorrow", "null" string, etc.
                        normalized_date = self._normalize_date(date_value)
                        if normalized_date:
                            print(f"📅 [DATE NORMALIZATION] '{date_value}' → '{normalized_date}'")
                            # Only update if we don't already have a date, or if the new date is different
                            if not self.booking_context.booking_date or self.booking_context.booking_date != normalized_date:
                                self.booking_context.booking_date = normalized_date
                                updated_fields.append(f"date: {self.booking_context.booking_date}")
                                extraction_successful = True
                                if self.booking_context.state == ConversationState.COLLECTING_DATE:
                                    # Don't change state yet - wait for confirmation
                                    print(f"✅ [DATE] Date extracted successfully: {self.booking_context.booking_date}, will confirm before moving to time")
                        else:
                            print(f"⚠️ [DATE] Could not normalize date: '{date_value}' - extraction failed")
                            # Don't mark as successful if date normalization failed
                            extraction_successful = False
                    
                    if extracted.get('booking_time'):
                        time_value = extracted['booking_time']
                        # POST-PROCESSING: Only add to updated_fields if it's actually new or changed
                        if not self.booking_context.booking_time or self.booking_context.booking_time != time_value:
                            self.booking_context.booking_time = time_value
                            updated_fields.append(f"time: {self.booking_context.booking_time}")
                            extraction_successful = True
                            if self.booking_context.state == ConversationState.COLLECTING_TIME:
                                # Don't change state yet - wait for confirmation
                                print(f"⏰ Time extracted: {self.booking_context.booking_time}, will confirm before fetching weather")
                        else:
                            print(f"ℹ️ [POST-PROCESSING] Time already set to {time_value}, skipping duplicate extraction")
                    
                    if extracted.get('cuisine_preference'):
                        cuisine_value = extracted['cuisine_preference']
                        # POST-PROCESSING: Only add to updated_fields if it's actually new or changed
                        if not self.booking_context.cuisine_preference or self.booking_context.cuisine_preference != cuisine_value:
                            self.booking_context.cuisine_preference = cuisine_value
                            updated_fields.append(f"cuisine: {self.booking_context.cuisine_preference}")
                            extraction_successful = True
                            if self.booking_context.state == ConversationState.COLLECTING_CUISINE:
                                # Don't change state yet - wait for confirmation
                                print(f"✅ Cuisine extracted: {self.booking_context.cuisine_preference}, will confirm before moving to requests")
                        else:
                            print(f"ℹ️ [POST-PROCESSING] Cuisine already set to {cuisine_value}, skipping duplicate extraction")
                    elif self.booking_context.state == ConversationState.COLLECTING_CUISINE:
                        # User responded but didn't provide cuisine - check if they said "no" or "skip"
                        user_text_lower = user_text.lower()
                        if any(phrase in user_text_lower for phrase in ['no preference', 'no', 'skip', 'any', "doesn't matter", "don't care", 'whatever']):
                            # User doesn't have a preference, set empty
                            self.booking_context.cuisine_preference = ""
                            updated_fields.append(f"cuisine: (no preference)")
                            extraction_successful = True
                            print(f"✅ No cuisine preference extracted, will confirm before moving to requests")
                    
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
                        
                        extraction_successful = True
                        if self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
                            # Don't change state yet - wait for confirmation
                            print(f"✅ Special requests extracted, will confirm before moving to email")
                    elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
                        # User responded but didn't provide special requests in JSON - check for "no" responses
                        if any(phrase in user_text_lower for phrase in ['no special', 'no dietary', 'no requests', 'not allergic', 'nothing', 'no, we', 'no thank', 'no we are not', 'no we are', 'no dietary restrictions', 'no', 'none']):
                            self.booking_context.special_requests = ""
                            updated_fields.append(f"requests: (none)")
                            extraction_successful = True
                            print(f"✅ No special requests extracted, will confirm before moving to email")
                    
                    # Handle email collection
                    if self.booking_context.state == ConversationState.COLLECTING_EMAIL:
                        # Check if user wants to skip email
                        skip_phrases = ['no', 'skip', 'not needed', "don't need", "don't want", 'no thanks', 'no thank you', 'not necessary', "don't have", "no email"]
                        if any(phrase in user_text_lower for phrase in skip_phrases):
                            # User doesn't want email
                            self.booking_context.customer_email = None
                            updated_fields.append(f"email: (skipped)")
                            extraction_successful = True
                            print(f"✅ Email skipped, will confirm before moving to final confirmation")
                        else:
                            # Try to extract email from user text
                            email_from_text = extract_email(user_text)
                            if email_from_text:
                                self.booking_context.customer_email = email_from_text
                                updated_fields.append(f"email: {email_from_text}")
                                extraction_successful = True
                                print(f"✅ Email extracted: {email_from_text}, will confirm before moving to final confirmation")
                            elif extracted.get('customer_email'):
                                # Email might be in LLM extraction
                                email_value = extracted['customer_email']
                                if is_valid_email(email_value):
                                    self.booking_context.customer_email = email_value.lower().strip()
                                    updated_fields.append(f"email: {self.booking_context.customer_email}")
                                    extraction_successful = True
                                    print(f"✅ Email extracted: {self.booking_context.customer_email}, will confirm before moving to final confirmation")
                    
                    # Handle seating preference
                    if extracted.get('seating_preference'):
                        seating = extracted['seating_preference'].lower()
                        if seating in ['indoor', 'outdoor']:
                            # POST-PROCESSING: Only add to updated_fields if it's actually new or changed
                            # BUT: If user is confirming seating (in SUGGESTING_SEATING state), acknowledge it even if already set
                            if not self.booking_context.seating_preference or self.booking_context.seating_preference != seating:
                                self.booking_context.seating_preference = seating
                                updated_fields.append(f"seating: {seating}")
                                extraction_successful = True
                                # If we're suggesting seating and user responds
                                if self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                                    # Don't change state yet - wait for confirmation
                                    print(f"✅ Seating preference extracted: {seating}, will confirm before moving to cuisine")
                            else:
                                # Seating already set, but if user is responding to seating question, still acknowledge it
                                if self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                                    # User is confirming the seating that was already suggested
                                    updated_fields.append(f"seating: {seating}")  # Add to updated_fields for confirmation
                                    extraction_successful = True
                                    print(f"✅ [POST-PROCESSING] Seating confirmed: {seating} (already set, but user confirmed it)")
                                elif self.booking_context.state in [ConversationState.COLLECTING_CUISINE, ConversationState.COLLECTING_REQUESTS]:
                                    # User provided seating while we were asking for something else - still acknowledge it
                                    updated_fields.append(f"seating: {seating}")  # Add to updated_fields for confirmation
                                    extraction_successful = True
                                    print(f"✅ [POST-PROCESSING] Seating provided: {seating} (already set, but user mentioned it)")
                                else:
                                    print(f"ℹ️ [POST-PROCESSING] Seating already set to {seating}, skipping duplicate extraction")
                    
                    # POST-PROCESSING: Check if we extracted something relevant even if no fields were updated
                    # This handles cases where user confirms something that's already set (e.g., seating)
                    if not extraction_successful and not updated_fields:
                        # Check if user provided seating when we're asking about seating
                        if extracted.get('seating_preference') and self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                            seating = extracted['seating_preference'].lower()
                            if seating in ['indoor', 'outdoor'] and self.booking_context.seating_preference == seating:
                                # User confirmed the seating that was already set
                                updated_fields.append(f"seating: {seating}")
                                extraction_successful = True
                                print(f"✅ [POST-PROCESSING] Seating confirmed by user: {seating}")
                    
                    if updated_fields:
                        print(f"")
                        print(f"=" * 80)
                        print(f"📋 [CONTEXT UPDATE] Updated fields: {', '.join(updated_fields)}")
                        print(f"✅ [EXTRACTION] Extraction successful: {extraction_successful}")
                        print(f"=" * 80)
                    elif not extraction_successful:
                        print(f"")
                        print(f"=" * 80)
                        print(f"ℹ️ [POST-PROCESSING] No fields were updated - all extracted values were already set or invalid")
                        print(f"✅ [EXTRACTION] Extraction successful: {extraction_successful}")
                        print(f"=" * 80)
                    
                    # If extraction was successful, send confirmation and then move to next step
                    if extraction_successful:
                        print(f"✅ [FLOW] Extraction successful, proceeding to confirmation...")
                        # Send the user's input as understood by the LLM (normalized/extracted version)
                        # This is what we'll show in the UI instead of raw STT
                        user_message_to_show = self._format_user_message_for_ui(extracted, updated_fields)
                        if user_message_to_show:
                            await self._send_transcript(user_message_to_show, speaker="user")
                        # Send confirmation message and then transition state
                        await self._send_confirmation_and_advance(updated_fields)
                    else:
                        print(f"⚠️ [FLOW] Extraction failed, asking for clarification...")
                        # Extraction failed or incomplete - ask for clarification
                        await self._ask_for_clarification()
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse JSON from LLM response: {e}")
                    print(f"   Response was: {response_text}")
                    # Clear waiting flag on error
                    self._waiting_for_response = False
                    await self._ask_for_clarification()
            else:
                print(f"⚠️ No JSON found in LLM response")
                # Clear waiting flag on error
                self._waiting_for_response = False
                await self._ask_for_clarification()
        except Exception as e:
            print(f"❌ Error extracting context: {e}")
            import traceback
            traceback.print_exc()
            # Clear waiting flag on error
            self._waiting_for_response = False
    
    async def _send_confirmation_and_advance(self, updated_fields):
        """Send brief confirmation message and advance to next question"""
        session = self.session if hasattr(self, 'session') else self._agent_session
        if not session:
            return
        
        # Generate confirmation message based on what was ACTUALLY extracted (updated_fields)
        # This ensures we confirm the right thing, not just what the state expects
        confirmation_msg = None
        next_state = None
        
        # Check what was actually updated from the updated_fields list
        has_guests = any('guests' in field for field in updated_fields)
        has_date = any('date' in field for field in updated_fields)
        has_time = any('time' in field for field in updated_fields)
        has_seating = any('seating' in field for field in updated_fields)
        has_cuisine = any('cuisine' in field for field in updated_fields)
        has_requests = any('requests' in field for field in updated_fields)
        has_email = any('email' in field for field in updated_fields)
        
        # Priority: What was actually extracted > Current state
        # This ensures we confirm what the user provided, not what the state expects
        if has_time:
            # Time was extracted - confirm it regardless of current state
            confirmation_msg = f"Got it, {self.booking_context.booking_time}."
            next_state = ConversationState.FETCHING_WEATHER
        
        elif has_date:
            # Date was extracted - confirm it regardless of current state
            confirmation_msg = f"Perfect, {self.booking_context.booking_date}."
            next_state = ConversationState.COLLECTING_TIME
        
        elif has_guests:
            # Guests was extracted - confirm it regardless of current state
            confirmation_msg = f"Got it, {self.booking_context.number_of_guests} guest{'s' if self.booking_context.number_of_guests > 1 else ''}."
            next_state = ConversationState.COLLECTING_DATE
        
        elif has_seating:
            # Seating can be extracted in SUGGESTING_SEATING state or even in other states (user providing info out of order)
            seating_text = "outdoor" if self.booking_context.seating_preference == "outdoor" else "indoor"
            confirmation_msg = f"Perfect, {seating_text} seating it is."
            # If we're in SUGGESTING_SEATING, move to cuisine. Otherwise, stay in current state or move appropriately
            if self.booking_context.state == ConversationState.SUGGESTING_SEATING:
                next_state = ConversationState.COLLECTING_CUISINE
            elif self.booking_context.state == ConversationState.COLLECTING_CUISINE:
                # User provided seating while we were asking for cuisine - confirm seating, stay in cuisine state
                next_state = None  # Don't change state, just confirm seating
            elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
                # User provided seating while we were asking for requests - confirm seating, stay in requests state
                next_state = None  # Don't change state, just confirm seating
            else:
                # Default: move to cuisine after seating
                next_state = ConversationState.COLLECTING_CUISINE
        
        elif self.booking_context.state == ConversationState.COLLECTING_CUISINE and has_cuisine:
            if self.booking_context.cuisine_preference:
                confirmation_msg = f"Got it, {self.booking_context.cuisine_preference} cuisine."
            else:
                confirmation_msg = "Got it, no specific cuisine preference."
            next_state = ConversationState.COLLECTING_REQUESTS
        
        elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS and has_requests:
            if self.booking_context.special_requests:
                confirmation_msg = f"Got it, {self.booking_context.special_requests}."
            else:
                confirmation_msg = "Got it, no special requests."
            next_state = ConversationState.COLLECTING_EMAIL
        
        elif self.booking_context.state == ConversationState.COLLECTING_EMAIL and has_email:
            if self.booking_context.customer_email:
                confirmation_msg = f"Got it, I have your email."
            else:
                confirmation_msg = "Got it, no email needed."
            # Only move to CONFIRMING if we have all required info
            if self.booking_context.is_complete():
                next_state = ConversationState.CONFIRMING
        
        # Fallback: if no fields were updated but we're in a state, use state-based confirmation
        # (This handles edge cases)
        if not confirmation_msg:
            if self.booking_context.state == ConversationState.COLLECTING_GUESTS and self.booking_context.number_of_guests:
                confirmation_msg = f"Got it, {self.booking_context.number_of_guests} guest{'s' if self.booking_context.number_of_guests > 1 else ''}."
                next_state = ConversationState.COLLECTING_DATE
            elif self.booking_context.state == ConversationState.COLLECTING_DATE and self.booking_context.booking_date:
                confirmation_msg = f"Perfect, {self.booking_context.booking_date}."
                next_state = ConversationState.COLLECTING_TIME
            elif self.booking_context.state == ConversationState.COLLECTING_TIME and self.booking_context.booking_time:
                confirmation_msg = f"Got it, {self.booking_context.booking_time}."
                next_state = ConversationState.FETCHING_WEATHER
            elif self.booking_context.state == ConversationState.SUGGESTING_SEATING and self.booking_context.seating_preference:
                seating_text = "outdoor" if self.booking_context.seating_preference == "outdoor" else "indoor"
                confirmation_msg = f"Perfect, {seating_text} seating it is."
                next_state = ConversationState.COLLECTING_CUISINE
            elif self.booking_context.state == ConversationState.COLLECTING_CUISINE:
                if self.booking_context.cuisine_preference:
                    confirmation_msg = f"Got it, {self.booking_context.cuisine_preference} cuisine."
                else:
                    confirmation_msg = "Got it, no specific cuisine preference."
                next_state = ConversationState.COLLECTING_REQUESTS
            elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
                if self.booking_context.special_requests:
                    confirmation_msg = f"Got it, {self.booking_context.special_requests}."
                else:
                    confirmation_msg = "Got it, no special requests."
                next_state = ConversationState.COLLECTING_EMAIL
            elif self.booking_context.state == ConversationState.COLLECTING_EMAIL:
                if self.booking_context.customer_email:
                    confirmation_msg = f"Got it, I have your email."
                else:
                    confirmation_msg = "Got it, no email needed."
                if self.booking_context.is_complete():
                    next_state = ConversationState.CONFIRMING
        
        # Send confirmation and move to next question
        if confirmation_msg:
            # Check if we've already sent this exact confirmation for this state
            confirmation_key = f"{self.booking_context.state.value}_{confirmation_msg}"
            if self._last_confirmation_sent == confirmation_key:
                print(f"⏸️ Already sent this confirmation, skipping to avoid duplicate")
                # Still update state and proceed, just don't send duplicate confirmation
                if next_state:
                    self.booking_context.state = next_state
                    self._last_question_asked = None
                    self._last_confirmation_sent = None  # Clear when state changes
                    if next_state == ConversationState.FETCHING_WEATHER:
                        await asyncio.sleep(0.5)
                        await self._fetch_weather_and_suggest_seating()
                    elif next_state == ConversationState.CONFIRMING:
                        await asyncio.sleep(0.5)
                        await self._confirm_booking_details()
                    else:
                        await asyncio.sleep(0.5)
                        await self._guide_to_next_step()
                self._waiting_for_response = False
                return
            
            print(f"💬 Sending confirmation: {confirmation_msg}")
            # Mark this confirmation as sent
            self._last_confirmation_sent = confirmation_key
            await self._generate_reply_with_transcript(confirmation_msg, allow_interruptions=False)
            
            # Clear waiting flag after confirmation is sent
            self._waiting_for_response = False
            
            # Update state after confirmation
            if next_state:
                self.booking_context.state = next_state
                print(f"🔄 State changed to: {self.booking_context.state.value}")
                # Clear last question asked and confirmation when state changes
                self._last_question_asked = None
                self._last_confirmation_sent = None
                
                # If moving to FETCHING_WEATHER, trigger weather fetch
                if next_state == ConversationState.FETCHING_WEATHER:
                    await asyncio.sleep(0.5)  # Small delay after confirmation
                    await self._fetch_weather_and_suggest_seating()
                # If moving to CONFIRMING, trigger confirmation
                elif next_state == ConversationState.CONFIRMING:
                    await asyncio.sleep(0.5)  # Small delay after confirmation
                    await self._confirm_booking_details()
                # Otherwise, ask the next question (if next_state is not None)
                elif next_state is not None:
                    await asyncio.sleep(0.5)  # Small delay after confirmation
                    await self._guide_to_next_step()
                # If next_state is None, we confirmed something but don't want to change state
                # (e.g., confirmed seating while in cuisine state - stay in cuisine state)
        else:
            # No confirmation message - clear waiting flag anyway
            self._waiting_for_response = False
    
    async def _ask_for_clarification(self):
        """Ask for clarification when extraction fails"""
        session = self.session if hasattr(self, 'session') else self._agent_session
        if not session:
            return
        
        clarification_msg = None
        
        if self.booking_context.state == ConversationState.COLLECTING_GUESTS:
            clarification_msg = "I didn't catch that. How many guests will be joining us today?"
        elif self.booking_context.state == ConversationState.COLLECTING_DATE:
            clarification_msg = "I didn't catch the date. What date would you like to make a reservation for?"
        elif self.booking_context.state == ConversationState.COLLECTING_TIME:
            clarification_msg = "I didn't catch the time. What time would you prefer? We're open from 11 AM to 10 PM."
        elif self.booking_context.state == ConversationState.COLLECTING_CUISINE:
            clarification_msg = "I didn't catch that. Do you have a cuisine preference? We offer Italian, Chinese, Indian, and more."
        elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
            clarification_msg = "I didn't catch that. Any special requests or dietary restrictions we should know about?"
        elif self.booking_context.state == ConversationState.COLLECTING_EMAIL:
            clarification_msg = "I didn't catch that. Would you like to receive a confirmation email? If yes, please provide your email address."
        
        if clarification_msg:
            print(f"❓ Asking for clarification: {clarification_msg}")
            await self._generate_reply_with_transcript(clarification_msg, allow_interruptions=False)
            # Clear waiting flag after asking for clarification
            self._waiting_for_response = False
    
    
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
        question_key = None  # Unique key to track if we've asked this question
        
        if self.booking_context.state == ConversationState.COLLECTING_GUESTS:
            if not self.booking_context.number_of_guests:
                next_question = "How many guests will be joining us today?"
                question_key = "guests"
        
        elif self.booking_context.state == ConversationState.COLLECTING_DATE:
            if not self.booking_context.booking_date:
                next_question = "What date would you like to make a reservation for?"
                question_key = "date"
        
        elif self.booking_context.state == ConversationState.COLLECTING_TIME:
            if not self.booking_context.booking_time:
                next_question = "What time would you prefer? We're open from 11 AM to 10 PM."
                question_key = "time"
        
        elif self.booking_context.state == ConversationState.COLLECTING_CUISINE:
            if not self.booking_context.cuisine_preference and self.booking_context.cuisine_preference != "":
                next_question = "Do you have a cuisine preference? We offer Italian, Chinese, Indian, and more."
                question_key = "cuisine"
        
        elif self.booking_context.state == ConversationState.COLLECTING_REQUESTS:
            # Special requests are optional
            if self.booking_context.special_requests is None:
                # Haven't asked yet, ask now
                next_question = "Any special requests or dietary restrictions we should know about? If not, just say 'no' or 'none'."
                question_key = "requests"
        
        elif self.booking_context.state == ConversationState.COLLECTING_EMAIL:
            # Email collection is optional
            if self.booking_context.customer_email is None:
                # Haven't asked yet, ask now
                next_question = "Would you like to receive a confirmation email? If yes, please provide your email address. Otherwise, just say 'no' or 'skip'."
                question_key = "email"
        
        elif self.booking_context.state == ConversationState.SUGGESTING_SEATING:
            # After seating suggestion, wait for user response
            # Don't check is_complete() here - we need to ask cuisine, requests, email first
            # The state will be updated when user responds with seating preference
            pass
        
        # Send the next question if we have one and haven't asked it recently
        if next_question and question_key:
            # Check if we've already asked this exact question in this state
            current_question_key = f"{self.booking_context.state.value}_{question_key}"
            if self._last_question_asked == current_question_key:
                print(f"⏸️ Already asked this question ({current_question_key}), skipping to avoid duplicate")
                return
            
            print(f"💬 Asking next question: {next_question}")
            try:
                # Mark that we've asked this question
                self._last_question_asked = current_question_key
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
            
            # After suggesting seating, wait for user response
            # The state will be handled in on_user_turn_completed when user responds
            # Don't automatically move to next step - let user respond to seating question first
        except Exception as e:
            print(f"Error fetching weather: {e}")
            # If weather fetch fails, move to suggesting seating anyway
            self.booking_context.state = ConversationState.SUGGESTING_SEATING
            await self._generate_reply_with_transcript(
                "I'm having trouble checking the weather, but we can still proceed. Would you prefer indoor or outdoor seating?"
            )
            # After asking about seating, wait for user response
            # State will be handled when user responds
    
    async def _confirm_booking_details(self):
        """Confirm all booking details with the user"""
        self.booking_context.state = ConversationState.CONFIRMING
        
        email_info = self.booking_context.customer_email if self.booking_context.customer_email else "Not provided"
        
        confirmation_text = f"""Let me confirm your booking details:

- Number of guests: {self.booking_context.number_of_guests}
- Date: {self.booking_context.booking_date}
- Time: {self.booking_context.booking_time}
- Cuisine preference: {self.booking_context.cuisine_preference or 'Not specified'}
- Special requests: {self.booking_context.special_requests or 'None'}
- Seating: {self.booking_context.seating_preference}
- Email: {email_info}

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
        # Configure VAD - Silero VAD has configurable parameters
        # Load VAD with longer silence duration to avoid cutting off user speech
        vad = VAD.load()
        # Note: VAD configuration might need to be done through the model itself
        # The default VAD should work, but we'll handle interruptions in the agent code
        
        # Configure STT - keep it simple, use default settings
        stt = STT()  # Uses gpt-4o-mini-transcribe by default
        
        session = AgentSession(
            vad=vad,
            stt=stt,
            llm=OpenAILLM(model="gpt-4o-mini"),  # Cheaper and better than gpt-3.5-turbo
            tts=TTS(),  # Uses gpt-4o-mini-tts by default
        )
        
        # Store session and room reference in agent (using private attribute)
        agent._agent_session = session
        agent._room = ctx.room
        
        # Set up data channel listener for text messages from frontend
        # LiveKit room has a data_received event we can listen to
        def on_data_received(data: bytes, participant, kind, topic):
            """Handle text messages sent from frontend"""
            try:
                import json
                text = data.decode('utf-8')
                message_data = json.loads(text)
                
                if message_data.get('type') == 'user_message':
                    user_text = message_data.get('text', '')
                    if user_text:
                        print(f"📨 Received text message from frontend: {user_text}")
                        # Process as if it were a voice message
                        # Create a mock message object
                        class MockMessage:
                            def __init__(self, text):
                                self.content = text
                                self.text = text
                        
                        # Process the text message asynchronously
                        asyncio.create_task(agent.on_user_turn_completed(None, MockMessage(user_text)))
            except Exception as e:
                print(f"⚠️ Error processing data channel message: {e}")
                import traceback
                traceback.print_exc()
        
        # Register data channel listener - check if room has on method
        if hasattr(ctx.room, 'on'):
            ctx.room.on("data_received", on_data_received)
        elif hasattr(ctx.room, 'add_listener'):
            ctx.room.add_listener("data_received", on_data_received)
        else:
            print("⚠️ Could not set up data channel listener - room doesn't have on() or add_listener() method")
        
        # Start the session
        await session.start(room=ctx.room, agent=agent)
        print("Restaurant booking agent started")
        
        # Send initial greeting immediately after session starts
        # Small delay to ensure session is fully ready
        await asyncio.sleep(0.3)
        try:
            await agent.on_agent_start(session)
            print("✅ Initial greeting sent successfully")
        except Exception as e:
            print(f"⚠️ Could not send initial greeting: {e}")
            import traceback
            traceback.print_exc()
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
