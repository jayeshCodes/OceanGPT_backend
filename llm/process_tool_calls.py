import json

try:
    from llm.execute_tool import execute_tool
except ImportError:
    from execute_tool import execute_tool

tool_responses = []
async def process_tool_calls(response):
    """process tool calls coming from the llm response"""
    # Process tool calls
    try:
        if isinstance(response, dict):
            # Check for tool_calls format
            if 'message' in response and 'tool_calls' in response['message']:
                for tool_call in response['message']['tool_calls']:
                    try:
                        tool_name = tool_call['function']['name']
                        tool_args = json.loads(tool_call['function']['arguments'])
                        tool_response = await execute_tool(tool_name, tool_args)
                        tool_responses.append({
                            "tool_name": tool_name,
                            "result": tool_response
                        })
                    except Exception as e:
                        print(f"Error executing tool {tool_name}: {str(e)}")
                        tool_responses.append({
                            "tool_name": tool_name,
                            "error": str(e)
                        })

            # Check for direct function call in message content
            elif 'message' in response and 'content' in response['message']:
                try:
                    # Try to parse the content as JSON
                    content = json.loads(response['message']['content'])
                    if isinstance(content, dict) and 'name' in content and 'arguments' in content:
                        tool_name = content['name']
                        # Handle both string and dict arguments
                        if isinstance(content['arguments'], str):
                            tool_args = json.loads(content['arguments'].replace("'", '"'))
                        else:
                            tool_args = content['arguments']

                        tool_response = await execute_tool(tool_name, tool_args)
                        tool_responses.append({
                            "tool_name": tool_name,
                            "result": tool_response
                        })
                except json.JSONDecodeError:
                    # Content is not JSON, treat as regular response
                    pass
                except Exception as e:
                    print(f"Error processing tool call: {str(e)}")

    except Exception as e:
        print(f"Error processing response: {str(e)}")

    return tool_responses
