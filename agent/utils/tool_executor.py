"""
Tool executor - executes tool calls and handles responses
"""
from typing import Dict, Any, Optional
from tools import WeatherTool, BookingTool, EmailTool, AvailabilityTool, TodayDateTool


class ToolExecutor:
    """Executes tool calls and manages tool instances"""
    
    def __init__(self):
        self.tools = {
            'weather': WeatherTool(),
            'create-booking': BookingTool(),
            'send-email': EmailTool(),
            'check-availability': AvailabilityTool(),
            'check-date': TodayDateTool(),
        }
    
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name
        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters
        Returns:
            Tool execution result
        """
        print(f"🔧 [TOOL_EXECUTOR] Executing tool: {tool_name} with params: {params}")
        
        tool = self.tools.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
            print(f"❌ [TOOL_EXECUTOR] {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        try:
            result = await tool.execute(params)
            if result.get('success'):
                print(f"✅ [TOOL_EXECUTOR] Tool '{tool_name}' executed successfully")
            else:
                print(f"❌ [TOOL_EXECUTOR] Tool '{tool_name}' failed: {result.get('error')}")
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [TOOL_EXECUTOR] Exception executing tool '{tool_name}': {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a tool instance by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> list:
        """List all available tools"""
        return [
            {
                'name': tool.name,
                'description': tool.description
            }
            for tool in self.tools.values()
        ]
