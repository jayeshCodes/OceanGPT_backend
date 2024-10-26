# DO NOT RUN
import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pydantic import Field, BaseModel

from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, FunctionMessage
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
from langchain.agents.output_parsers import ToolsAgentOutputParser
from langchain_community.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langchain.agents.format_scratchpad import format_to_openai_functions
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ChromaDB setup
chroma_client = chromadb.PersistentClient(path="../chroma_db")
collection = chroma_client.get_or_create_collection(name="conversation_history")


# Tool definitions
@tool
async def execute_python(code: str) -> str:
    """Execute Python code and return the output."""
    # Implementation from previous execute_python.py
    # ... (include the execute_python implementation here)
    pass


@tool
async def search_web(query: str) -> str:
    """Search the web for information."""
    # Implement web search functionality
    return f"Web search results for: {query}"


tools = [
    Tool(
        name="python",
        description="Execute Python code and return the output",
        func=execute_python,
        coroutine=execute_python
    ),
    Tool(
        name="search",
        description="Search the web for information",
        func=search_web,
        coroutine=search_web
    ),
]


class ChromaDBMemory(ConversationBufferMemory, BaseModel):
    """Custom memory class that uses ChromaDB for persistence"""

    chroma_collection: Any = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context to ChromaDB"""
        super().save_context(inputs, outputs)

        # Format the conversation entry
        entry = f"User: {inputs['input']}\nAssistant: {outputs['output']}"

        # Store in ChromaDB
        self.chroma_collection.add(
            documents=[entry],
            ids=[str(datetime.now().timestamp())],
            metadatas=[{"timestamp": datetime.now().timestamp()}]
        )

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Load conversation history from ChromaDB"""
        results = self.chroma_collection.query(
            query_texts=[inputs["input"]],
            n_results=7,
            where={"timestamp": {"$gte": (datetime.now() - timedelta(days=7)).timestamp()}}
        )

        if results['documents'] and len(results['documents'][0]) > 0:
            return {"history": "\n".join(results['documents'][0])}
        return {"history": ""}


class TwoStageChat:
    def __init__(self, model_name: str = "llama2"):
        # Initialize LLM with updated import
        self.llm = ChatOllama(model=model_name)

        # Initialize memory with the ChromaDB collection
        self.memory = ChromaDBMemory(
            chroma_collection=collection,
            return_messages=True,
            memory_key="chat_history"
        )

        # First stage - Tool selection prompt
        self.tool_selection_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="You are a helpful AI assistant. Based on the user's input, determine if you need to use any tools."),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Second stage - Final response prompt
        self.final_response_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="You are a helpful AI assistant. Use the tool results to provide a comprehensive response."),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="tool_responses"),
        ])

        # Set up the tool selection chain
        self.tool_selection_chain = (
                RunnablePassthrough.assign(
                    agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
                )
                | self.tool_selection_prompt
                | self.llm
                | ToolsAgentOutputParser()
        )

        # Set up the final response chain
        self.final_response_chain = (
                self.final_response_prompt
                | self.llm
                | StrOutputParser()
        )

    async def process_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Process tool calls and return results"""
        tool_responses = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"]

            try:
                tool = next(t for t in tools if t.name == tool_name)
                result = await tool.coroutine(**tool_args)
                tool_responses.append({
                    "tool_name": tool_name,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tool_responses.append({
                    "tool_name": tool_name,
                    "error": str(e)
                })

        return tool_responses

    async def __call__(self, user_input: str) -> str:
        """Process user input through the two-stage architecture"""
        try:
            # Get chat history
            chat_history = self.memory.load_memory_variables({"input": user_input})

            # First stage: Tool selection
            tool_selection_response = await self.tool_selection_chain.ainvoke({
                "input": user_input,
                "chat_history": chat_history["history"],
                "intermediate_steps": []
            })

            # Process tool calls if any
            tool_responses = []
            if hasattr(tool_selection_response, "tool_calls"):
                tool_responses = await self.process_tool_calls(tool_selection_response.tool_calls)

            # Second stage: Final response
            final_response = await self.final_response_chain.ainvoke({
                "input": user_input,
                "chat_history": chat_history["history"],
                "tool_responses": "\n".join([f"{r['tool_name']}: {r.get('result', r.get('error'))}"
                                             for r in tool_responses])
            })

            # Save conversation to memory
            self.memory.save_context(
                {"input": user_input},
                {"output": final_response}
            )

            return final_response

        except Exception as e:
            logger.error(f"Error in chat process: {e}")
            return f"An error occurred: {str(e)}"


async def main():
    """Main function for CLI usage"""
    chat = TwoStageChat()

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break

            result = await chat(user_input)
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