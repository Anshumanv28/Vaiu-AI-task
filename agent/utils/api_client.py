"""
HTTP client for making requests to the backend API
"""
import aiohttp
import os
from typing import Dict, Optional, Any


class BackendAPIClient:
    """Client for communicating with the backend REST API"""
    
    def __init__(self):
        self.base_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
    
    async def get_weather(self, date: str) -> Dict[str, Any]:
        """
        Fetch weather data for a specific date
        Args:
            date: Date in YYYY-MM-DD format
        Returns:
            Weather data dict with condition, temperature, description
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/weather/{date}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    error_data = await response.json()
                    raise Exception(f"Weather API error: {error_data.get('error', 'Unknown error')}")
    
    async def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new booking
        Args:
            booking_data: Dictionary with booking details
        Returns:
            Created booking data
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/bookings"
            async with session.post(url, json=booking_data) as response:
                if response.status == 201:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    error_data = await response.json()
                    raise Exception(f"Booking API error: {error_data.get('error', 'Unknown error')}")

