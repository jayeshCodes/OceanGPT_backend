from typing import List, Dict, Any
import ollama

from llm.models.message import Message, ToolResponse
from llm.utils.logging_config import setup_logging

logger = setup_logging()

class ChatManager:
    def __init__(self, model_name: str, system_prompt:str):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.client = ollama.AsyncClient()

    async def get_initial_response(self, messages: List[Message], tools: List[Dict]) -> Any:
        try:
            return await self.client.chat(
                model=self.model_name,
                messages=[m.__dict__ for m in messages],
                format="json",
                tools=tools,
                stream=False
            )
        except Exception as e:
            logger.error(f"Failed to get initial response: {e}")
            raise

    async def get_final_response(self, messages: List[Message]) -> str:
        try:
            return await self.client.chat(
                model=self.model_name,
                messages=[m.__dict__ for m in messages],
                format="json",
                stream=False
            )
        except Exception as e:
            logger.error(f"Failed to get final response: {e}")
            raise
