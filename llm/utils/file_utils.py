import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict

def calculate_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)
    return sha256.hexdigest()

def get_file_metadata(file_path: Path) -> Dict:
    file_stat = file_path.stat()
    return {
        "file_name": file_path.name,
        "file_path": str(file_path.absolute()),
        "file_size": file_stat.st_size,
        "creation_time": file_stat.st_ctime,
        "modification_time": file_stat.st_mtime,
        "access_time": file_stat.st_atime,
        "file_hash": calculate_file_hash(file_path),
        "last_scanned": datetime.now().timestamp()
    }