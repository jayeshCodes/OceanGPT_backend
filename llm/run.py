"""imports"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta
import logging

import chromadb
import ollama

from constants.llama_config import model, system, tools

try:
    from llm.execute_tool import execute_tool
    from llm.delete_old_entries import delete_old_entries
    from llm.extract_content import extract_content
    from llm.process_tool_calls import process_tool_calls
except ImportError:
    from execute_tool import execute_tool
    from delete_old_entries import delete_old_entries
    from extract_content import extract_content
    from process_tool_calls import process_tool_calls

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables before any imports or client initialization
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# init chromadb with persistent storage to store conversation history
chroma_client = chromadb.PersistentClient(path="../chroma_db")
collection = chroma_client.get_or_create_collection(name="conversation_history")


async def run(model_name=model, user_input=""):
    """run the large language model"""
    try:
        client = ollama.AsyncClient()
        system_prompt = system

        # Retrieve recent conversation history
        results = collection.query(
            query_texts=[user_input],
            n_results=7,
            where={"timestamp": {"$gte": (datetime.now() - timedelta(days=7)).timestamp()}}
        )

        conversation_history = ""
        if results['documents'] and len(results['documents'][0]) > 0:
            conversation_history = "\n".join(results['documents'][0])

        # Include the user input in the initial messages
        message = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "system",
                "content": f"Recent conversation history:\n{conversation_history}"
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        # First call to check for tool usage
        try:
            response = await client.chat(
                model=model_name,
                messages=message,
                format="json",
                tools=tools,
                stream=False
            )
            logger.debug(f"Initial response: {response}")
        except Exception as e:
            logger.error(f"Error in initial model call: {e}")
            raise

        print(response)
        tool_responses = await process_tool_calls(response)

        # Construct final message including tool responses
        final_message = message.copy()

        if tool_responses:
            for tool_response in tool_responses:
                final_message.append({
                    "role": "function",
                    "name": tool_response["tool_name"],
                    "content": tool_response.get("result", str(tool_response.get("error")))
                })

        # Get final response
        try:
            final_response = await client.chat(
                model=model_name,
                messages=final_message,
                stream=False
            )
        except Exception as e:
            logger.error(f"Error in final model call: {e}")
            raise

        # Store conversation in collection
        try:
            collection.add(
                documents=[f"User: {user_input}\nAssistant: {final_response}"],
                ids=[str(uuid.uuid4())],
                metadatas=[{"timestamp": datetime.now().timestamp()}]
            )
            delete_old_entries(collection)
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            # Don't raise here as we still want to return the response

        return extract_content(final_response)

    except Exception as e:
        logger.error(f"Error in run function: {e}")
        return f"An error occurred: {str(e)}"


async def main():
    """Main function for CLI usage"""
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break
            result = await run(model_name=model, user_input=user_input)
            print("Assistant:", result)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    # Set up event loop policy for Windows if needed
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())