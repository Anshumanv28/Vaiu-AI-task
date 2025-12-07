"""
Weather checking tool wrapper
"""
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
        Check weather for a date
        Args:
            params: {'date': 'YYYY-MM-DD'}
        Returns:
            Weather data dict
        """
        print(f"🔧 [WEATHER_TOOL] Executing with params: {params}")
        error = self.validate_params(params, ['date'])
        if error:
            print(f"❌ [WEATHER_TOOL] Validation failed: {error}")
            return {'success': False, 'error': error}
        
        try:
            weather_data = await self.api_client.get_weather(params['date'])
            print(f"✅ [WEATHER_TOOL] Weather data retrieved: {weather_data}")
            return {
                'success': True,
                'data': weather_data
            }
        except Exception as e:
            print(f"❌ [WEATHER_TOOL] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
