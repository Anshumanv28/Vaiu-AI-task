"""
Email sending tool wrapper
"""
from .base_tool import BaseTool
from utils.api_client import BackendAPIClient
from typing import Dict, Any


class EmailTool(BaseTool):
    """Tool for sending booking confirmation emails"""
    
    def __init__(self):
        super().__init__(
            name="send-email",
            description="Send booking confirmation email"
        )
        self.api_client = BackendAPIClient()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email confirmation
        Args:
            params: {'bookingId': 'booking_id'}
        Returns:
            Email sending status
        """
        error = self.validate_params(params, ['bookingId'])
        if error:
            return {'success': False, 'error': error}
        
        try:
            result = await self.api_client.send_email(params['bookingId'])
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
