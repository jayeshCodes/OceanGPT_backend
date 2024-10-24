"""imports"""
import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta

import chromadb
import ollama

from constants.llama_config import model, system, tools

try:
    from llm.execute_tool import execute_tool
    from llm.delete_old_entries import delete_old_entries
    from llm.extract_content import extract_content
except ImportError:
    from execute_tool import execute_tool
    from delete_old_entries import delete_old_entries
    from extract_content import extract_content

# suppress warnings
os.environ["TOKENS_PARALLELISM"] = "false"

# init chromadb with persistent storage to store conversation history
chroma_client = chromadb.PersistentClient(path="../chroma_db")
collection = chroma_client.get_or_create_collection(name="conversation_history")


async def run(model_name=model, user_input=""):
    """run the large language model"""
    client = ollama.AsyncClient()
    system_prompt = system

    # Retrieve recent conversation history
    results = collection.query(
        query_texts=[user_input],
        n_results=7,
        where={"timestamp": {"$gte": (datetime.now() - timedelta(days=7)).timestamp()}}
    )

    conversation_history = ""
    if results['documents']:
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
    response = await client.chat(
        model=model_name,
        messages=message,
        format="json",
        tools=tools,
        stream=False
    )

    print(response)

    tool_responses = []

    # Process tool calls if they exist
    if isinstance(response, dict) and 'tool_calls' in response['message']:
        for tool_call in response['tool_calls']:
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
    final_response = await client.chat(
        model=model_name,
        messages=final_message,
        stream=False
    )

    # Store conversation in collection
    collection.add(
        documents=[f"User: {user_input}\nAssistant: {final_response}"],
        ids=[str(uuid.uuid4())],
        metadatas=[{"timestamp": datetime.now().timestamp()}]
    )

    # Delete old entries
    delete_old_entries(collection)

    return extract_content(final_response)

async def main():
    while True:
        user_input = input("> ")
        if user_input.lower() == "exit":
            break
        result = await run(model_name=model, user_input=user_input)
        print("Assistant:", result)

if __name__ == "__main__":
    asyncio.run(main())