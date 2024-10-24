import json
from json import JSONDecodeError

def extract_content(final_response):
    """Extract final message content, handling different possible formats."""
    # Try to access the 'message' -> 'content' and handle it as JSON or plain text
    try:
        content = final_response['message']['content']
        try:
            # Try to load the content as JSON
            content = json.loads(content)
            return content.get('text', content.get('content'))  # Handle both 'text' and 'content'
        except JSONDecodeError:
            return content  # Return the plain 'content' if it's not JSON
    except KeyError:
        pass

    # Fallback to the original response if no 'message' or 'content' is found
    return final_response