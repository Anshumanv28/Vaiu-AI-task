"""
Conversation state machine and flow logic for the booking agent
"""
from typing import Dict, Optional, Any
from enum import Enum


class ConversationState(Enum):
    """States in the booking conversation flow"""
    GREETING = "greeting"
    COLLECTING_GUESTS = "collecting_guests"
    COLLECTING_DATE = "collecting_date"
    COLLECTING_TIME = "collecting_time"
    COLLECTING_CUISINE = "collecting_cuisine"
    COLLECTING_REQUESTS = "collecting_requests"
    FETCHING_WEATHER = "fetching_weather"
    SUGGESTING_SEATING = "suggesting_seating"
    CONFIRMING = "confirming"
    CREATING_BOOKING = "creating_booking"
    COMPLETED = "completed"
    ERROR = "error"


class BookingContext:
    """Stores the current booking context during conversation"""
    
    def __init__(self):
        self.state = ConversationState.GREETING
        self.number_of_guests: Optional[int] = None
        self.booking_date: Optional[str] = None  # YYYY-MM-DD format
        self.booking_time: Optional[str] = None  # HH:mm format (24-hour)
        self.cuisine_preference: str = ""
        self.special_requests: str = ""
        self.weather_info: Optional[Dict[str, Any]] = None
        self.seating_preference: str = "indoor"
        self.booking_id: Optional[str] = None
        self.error_message: Optional[str] = None
    
    def to_booking_data(self) -> Dict[str, Any]:
        """Convert context to booking data format for API"""
        return {
            "numberOfGuests": self.number_of_guests,
            "bookingDate": self.booking_date,
            "bookingTime": self.booking_time,
            "cuisinePreference": self.cuisine_preference,
            "specialRequests": self.special_requests,
            "weatherInfo": self.weather_info,
            "seatingPreference": self.seating_preference
        }
    
    def is_complete(self) -> bool:
        """Check if all required booking information is collected"""
        return (
            self.number_of_guests is not None and
            self.booking_date is not None and
            self.booking_time is not None
        )
    
    def reset(self):
        """Reset context for a new booking"""
        self.__init__()

