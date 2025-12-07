"""
Base class for all tools
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseTool(ABC):
    """Base class for all agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given parameters
        Args:
            params: Tool parameters
        Returns:
            Result dictionary with 'success' and 'data' or 'error' keys
        """
        pass
    
    def validate_params(self, params: Dict[str, Any], required: list) -> Optional[str]:
        """
        Validate that required parameters are present
        Args:
            params: Parameters to validate
            required: List of required parameter names
        Returns:
            Error message if validation fails, None otherwise
        """
        missing = [p for p in required if p not in params or params[p] is None]
        if missing:
            return f"Missing required parameters: {', '.join(missing)}"
        return None
