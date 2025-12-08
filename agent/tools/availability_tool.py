"""
Date availability checking tool wrapper
"""
from .base_tool import BaseTool
from utils.api_client import BackendAPIClient
from typing import Dict, Any


class AvailabilityTool(BaseTool):
    """Tool for checking date/time availability"""
    
    def __init__(self):
        super().__init__(
            name="check-availability",
            description="Check if a date/time slot is available for booking"
        )
        self.api_client = BackendAPIClient()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check availability for a date/time
        Args:
            params: {'date': 'YYYY-MM-DD', 'time': 'HH:mm' (optional)}
        Returns:
            Availability status dict
        """
        print(f"🔧 [AVAILABILITY_TOOL] Executing with params: {params}")
        error = self.validate_params(params, ['date'])
        if error:
            print(f"❌ [AVAILABILITY_TOOL] Validation failed: {error}")
            return {'success': False, 'error': error}
        
        try:
            result = await self.api_client.call_tool('check-availability', params)
            print(f"✅ [AVAILABILITY_TOOL] Availability check completed")
            return result
        except Exception as e:
            print(f"❌ [AVAILABILITY_TOOL] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
