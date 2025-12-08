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
        print(f"🔧 [EMAIL_TOOL] Executing with params: {params}")
        error = self.validate_params(params, ['bookingId'])
        if error:
            print(f"❌ [EMAIL_TOOL] Validation failed: {error}")
            return {'success': False, 'error': error}
        
        try:
            result = await self.api_client.call_tool('send-email', params)
            print(f"✅ [EMAIL_TOOL] Email sent successfully")
            return result
        except Exception as e:
            print(f"❌ [EMAIL_TOOL] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
