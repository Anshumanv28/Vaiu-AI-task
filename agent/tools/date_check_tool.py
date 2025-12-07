"""
Date availability checking tool wrapper
"""
from .base_tool import BaseTool
from utils.api_client import BackendAPIClient
from typing import Dict, Any


class DateCheckTool(BaseTool):
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
        error = self.validate_params(params, ['date'])
        if error:
            return {'success': False, 'error': error}
        
        try:
            result = await self.api_client.check_availability(
                date=params['date'],
                time=params.get('time')
            )
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
