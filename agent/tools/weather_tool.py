"""
Weather checking tool wrapper
"""
import re
from .base_tool import BaseTool
from utils.api_client import BackendAPIClient
from typing import Dict, Any


class WeatherTool(BaseTool):
    """Tool for checking weather forecast"""
    
    def __init__(self):
        super().__init__(
            name="weather",
            description="Check weather forecast for a specific date"
        )
        self.api_client = BackendAPIClient()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check weather for a date and optionally time
        Args:
            params: {'date': 'YYYY-MM-DD', 'time': 'HH:mm' (optional)}
        Returns:
            Weather data dict
        """
        print(f"🔧 [WEATHER_TOOL] Executing with params: {params}")
        error = self.validate_params(params, ['date'])
        if error:
            print(f"❌ [WEATHER_TOOL] Validation failed: {error}")
            return {'success': False, 'error': error}
        
        # Validate time format if provided
        if 'time' in params and params['time']:
            if not re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', params['time']):
                error = "Invalid time format. Use 24-hour format (HH:mm)"
                print(f"❌ [WEATHER_TOOL] {error}")
                return {'success': False, 'error': error}
        
        try:
            result = await self.api_client.call_tool('weather', params)
            print(f"✅ [WEATHER_TOOL] Weather data retrieved")
            return result
        except Exception as e:
            print(f"❌ [WEATHER_TOOL] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
