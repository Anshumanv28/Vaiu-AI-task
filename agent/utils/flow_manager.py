"""
Conversation flow management utilities
"""
from typing import Optional
from conversation import ConversationState, BookingContext


def get_next_question(context: BookingContext) -> Optional[str]:
    """
    Determine the next question to ask based on current state and context
    Args:
        context: Current booking context
    Returns:
        Next question string or None if no question needed
    """
    if context.state == ConversationState.COLLECTING_GUESTS:
        if context.number_of_guests is None:
            return "How many guests will be joining us today?"
        else:
            return None  # Move to next state
    
    elif context.state == ConversationState.COLLECTING_DATE:
        if context.booking_date is None:
            return "What date would you like to make a reservation for?"
        else:
            return None  # Move to weather fetching
    
    elif context.state == ConversationState.COLLECTING_TIME:
        if context.booking_time is None:
            return "What time would you prefer? We're open from 11 AM to 10 PM."
        else:
            return None  # Move to next state
    
    elif context.state == ConversationState.COLLECTING_CUISINE:
        if context.cuisine_preference is None or context.cuisine_preference == "":
            return "Do you have a cuisine preference? We offer Italian, Chinese, Indian, and more."
        else:
            return None  # Move to next state
    
    elif context.state == ConversationState.COLLECTING_REQUESTS:
        if context.special_requests is None:
            return "Any special requests or dietary restrictions we should know about?"
        else:
            return None  # Check if complete
    
    elif context.state == ConversationState.COLLECTING_EMAIL:
        if context.customer_email is None or context.customer_email == "":
            return "Would you like to receive a confirmation email? If yes, please provide your email address."
        else:
            return None  # Move to confirmation
    
    return None


def should_collect_email(context: BookingContext) -> bool:
    """
    Determine if email collection should be attempted
    Args:
        context: Current booking context
    Returns:
        True if email should be collected, False otherwise
    """
    # Email collection happens after special requests are collected
    # and before confirmation
    return (
        context.state == ConversationState.COLLECTING_EMAIL or
        (context.state == ConversationState.COLLECTING_REQUESTS and 
         context.special_requests is not None)
    )


def get_next_state(context: BookingContext) -> Optional[ConversationState]:
    """
    Determine the next state based on current state and context completeness
    Args:
        context: Current booking context
    Returns:
        Next conversation state or None if should stay in current state
    """
    if context.state == ConversationState.COLLECTING_GUESTS:
        if context.number_of_guests is not None:
            return ConversationState.COLLECTING_DATE
    
    elif context.state == ConversationState.COLLECTING_DATE:
        if context.booking_date is not None:
            return ConversationState.FETCHING_WEATHER
    
    elif context.state == ConversationState.COLLECTING_TIME:
        if context.booking_time is not None:
            return ConversationState.COLLECTING_CUISINE
    
    elif context.state == ConversationState.COLLECTING_CUISINE:
        if context.cuisine_preference:
            return ConversationState.COLLECTING_REQUESTS
    
    elif context.state == ConversationState.COLLECTING_REQUESTS:
        if context.special_requests is not None:
            # After special requests, optionally collect email
            return ConversationState.COLLECTING_EMAIL
    
    elif context.state == ConversationState.COLLECTING_EMAIL:
        # After email (or skipping), move to confirmation if complete
        if context.is_complete():
            return ConversationState.CONFIRMING
    
    elif context.state == ConversationState.SUGGESTING_SEATING:
        if context.is_complete():
            return ConversationState.CONFIRMING
        elif not context.booking_time:
            return ConversationState.COLLECTING_TIME
        elif not context.cuisine_preference:
            return ConversationState.COLLECTING_CUISINE
        elif context.special_requests is None:
            return ConversationState.COLLECTING_REQUESTS
    
    return None

