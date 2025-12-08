"""
Booking creation tool wrapper
"""
from .base_tool import BaseTool
from utils.api_client import BackendAPIClient
from typing import Dict, Any


class BookingTool(BaseTool):
    """Tool for creating restaurant bookings"""
    
    def __init__(self):
        super().__init__(
            name="create-booking",
            description="Create a new restaurant booking"
        )
        self.api_client = BackendAPIClient()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a booking
        Args:
            params: Booking details (numberOfGuests, bookingDate, bookingTime, etc.)
        Returns:
            Created booking data
        """
        print(f"🔧 [BOOKING_TOOL] Executing with params: {params}")
        required = ['numberOfGuests', 'bookingDate', 'bookingTime']
        error = self.validate_params(params, required)
        if error:
            print(f"❌ [BOOKING_TOOL] Validation failed: {error}")
            return {'success': False, 'error': error}
        
        try:
            result = await self.api_client.call_tool('create-booking', params)
            booking = result.get('data', {}).get('booking', {})
            booking_id = booking.get('_id') or booking.get('bookingId') or result.get('data', {}).get('bookingId')
            print(f"✅ [BOOKING_TOOL] Booking created: {booking_id}")
            return result
        except Exception as e:
            print(f"❌ [BOOKING_TOOL] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
