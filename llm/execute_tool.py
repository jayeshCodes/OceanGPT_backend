"""imports"""
import asyncio
import importlib
import sys
from typing import Dict, Any
import json
import os


# Add the path to the functions package
def add_functions_package_path():
    """successfully import functions package path"""
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    functions_package_path = os.path.join(parent_directory, "functions")


async def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> str:
    """Execute the required tool."""
    print(f"Executing tool: {tool_name}")
    try:
        # Add the external functions package path
        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
        functions_package_path = os.path.join(parent_directory, "functions")

        if functions_package_path not in sys.path:
            sys.path.append(functions_package_path)

        # Import and execute the tool
        module = importlib.import_module(f"functions.{tool_name}")
        tool_function = getattr(module, tool_name)
        result = await tool_function(**parameters) if asyncio.iscoroutinefunction(tool_function) else tool_function(
            **parameters)
        return json.dumps(result)
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"

