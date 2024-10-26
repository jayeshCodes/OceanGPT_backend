"""database operations live here"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import chromadb
from llm.config import Config
from llm.utils.logging_config import setup_logging

logger = setup_logging()


class DatabaseManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
        self.conversation_collection = self.client.get_or_create_collection(
            name=Config.CONVERSATION_COLLECTION
        )
        self.csv_metadata_collection = self.client.get_or_create_collection(
            name=Config.CSV_METADATA_COLLECTION
        )

    def get_recent_conversations(self, query_text: str) -> str:
        results = self.conversation_collection.query(
            query_texts=[query_text],
            n_results=Config.CONVERSATION_HISTORY_LIMIT,
            where={
                "timestamp": {"$gte": (datetime.now() - timedelta(days=Config.CONVERSATION_HISTORY_DAYS)).timestamp()}}
        )
        return "\n".join(results['documents'][0] if results['documents'] and results['documents'][0] else "")

    def store_conversation(self, user_input: str, assistant_response: str) -> None:
        try:
            self.conversation_collection.add(
                documents=[f"User: {user_input}, Assistant: {assistant_response}"],
                ids=[str(uuid.uuid4())],
                metadatas=[{"timestamp": datetime.now().timestamp()}]
            )
            self.delete_old_entries()
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")

    def update_csv_metadata(self, metadata: Dict[str, Any]) -> None:
        try:
            existing_entries = self.csv_metadata_collection.query(
                query_texts=[metadata["file_name"]],
                where={"file_path": metadata["file_path"]},
                n_results=1
            )

            if not existing_entries['ids']:
                self.csv_metadata_collection.add(
                    documents=[f"CSV File: {metadata['file_name']}"],
                    ids=[str(uuid.uuid4())],
                    metadatas=[metadata]
                )
                logger.info(f"Added new CSV file metadata: {metadata['file_name']}")
            else:
                existing_id = existing_entries['ids'][0][0]
                existing_metadata = existing_entries['metadatas'][0][0]

                if existing_metadata.get('file_hash') != metadata['file_hash']:
                    self.csv_metadata_collection.update(
                        ids=[existing_id],
                        documents=[f"CSV File: {metadata['file_name']}"],
                        metadatas=[metadata]
                    )
                    logger.info(f"Updated CSV file metadata: {metadata['file_name']}")
        except Exception as e:
            logger.error(f"Error updating CSV metadata: {e}")

    def delete_old_entries(self):
        """delete old entries from conversation"""
        seven_days_ago = (datetime.now() - timedelta(days=7)).timestamp()
        self.conversation_collection.delete(
            where={"timestamp": {"$lt": seven_days_ago}}
        )
