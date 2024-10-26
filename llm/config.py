class Config:
    CHROMA_DB_PATH = "../chroma_db"
    DATA_DIR = "../data"
    TOKENIZERS_PARALLELISM = "false"
    CONVERSATION_COLLECTION = "conversation_history"
    CSV_METADATA_COLLECTION = "csv_metadata"
    CONVERSATION_HISTORY_DAYS = 7
    CONVERSATION_HISTORY_LIMIT = 7