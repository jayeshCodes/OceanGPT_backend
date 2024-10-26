import glob
from pathlib import Path
from typing import List

from llm.config import Config
from llm.utils.file_utils import get_file_metadata
from llm.utils.logging_config import setup_logging

logger = setup_logging()

class FileTracker:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def scan_csv_files(self) -> None:
        try:
            csv_files = glob.glob(str(Config.DATA_DIR / "**/*.csv"), recursive=True)

            for file_path in csv_files:
                metadata = get_file_metadata(Path(file_path))
                self.db_manager.update_csv_metadata(metadata)

        except Exception as e:
            logger.error(f"Error while scanning CSV files: {e}")
