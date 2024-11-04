"""main entry point for llm or console based application"""

"""imports"""
import asyncio
import os
from typing import List, Optional
from constants.llama_config import model, system, tools
from llm.chat_manager import ChatManager
from llm.db_manager import DatabaseManager
from llm.file_tracker import FileTracker
from llm.models.message import Message
from llm.config import Config
from llm.utils.logging_config import setup_logging
from process_tool_calls import process_tool_calls
from extract_content import extract_content

logger = setup_logging()


class LLMRunner:
    def __init__(self):
        os.environ["TOKENIZERS_PARALLELISM"] = Config.TOKENIZERS_PARALLELISM
        self.db_manager = DatabaseManager()
        self.chat_manager = ChatManager(model, system)
        self.file_tracker = FileTracker(self.db_manager)

    async def run(self, user_input: str) -> str:
       try:
           # Scan CSV files
           self.file_tracker.scan_csv_files()

           # Get conversation history
           conversation_history = self.db_manager.get_recent_conversations(user_input)

           # Prepare initial messages
           messages = [
               Message(role="system", content=system),
               Message(role="system", content=f"Recent conversation history:\n{conversation_history}"),
               Message(role="user", content=user_input)
           ]

           # Get initial response and process tool calls
           initial_response = await self.chat_manager.get_initial_response(messages, tools)
           print(f"init: {initial_response}\n")
           tool_responses = await process_tool_calls(initial_response)
           print(f"tool responses: {tool_responses}\n")

           # Add successful tool responses to messages
           for tool_response in tool_responses:
               if "error" not in tool_response and "SKIP" not in tool_response:
                   messages.append(Message(
                       role="function",
                       name=tool_response["tool_name"],
                       content=tool_response["result"]
                   ))
               else:
                   logger.warning(f"Skipping tool response due to error: {tool_response["error"]}")

           # Get and process final response
           final_response = await self.chat_manager.get_final_response(messages)
           print(f"final response: {final_response}\n")
           self.db_manager.store_conversation(user_input, final_response)

           return extract_content(final_response)

       except Exception as e:
           logger.error(f"Error in the run function: {e}")
           return f"Error in the run function: {str(e)}"

async def main():
    runner = LLMRunner()
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break
            result = await runner.run(user_input)
            print("Assistant:", result)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
