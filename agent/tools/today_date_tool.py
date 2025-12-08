"""
Current date and time checking tool wrapper - returns current date and time for context awareness
"""
from .base_tool import BaseTool
from utils.api_client import BackendAPIClient
from typing import Dict, Any


class TodayDateTool(BaseTool):
    """Tool for getting current date and time for context awareness"""
    
    def __init__(self):
        super().__init__(
            name="check-date",
            description="Get current date and time for context awareness. Use this to detect if users are trying to book in the past and to calculate relative dates like 'today', 'tomorrow', etc."
        )
        self.api_client = BackendAPIClient()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current date and time
        Args:
            params: Empty dict (no params needed)
        Returns:
            Current date (YYYY-MM-DD) and time (HH:mm) in 24-hour format
        """
        print(f"🔧 [DATE_TIME_TOOL] Getting current date and time")
        try:
            result = await self.api_client.call_tool('check-date', {})
            if result.get('success'):
                date_data = result.get('data', {})
                print(f"✅ [DATE_TIME_TOOL] Current date: {date_data.get('today')}, Current time: {date_data.get('currentTime')}")
            else:
                print(f"✅ [DATE_TIME_TOOL] Date and time retrieved")
            return result
        except Exception as e:
            print(f"❌ [DATE_TIME_TOOL] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
