from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Message:
    role: str
    content: str
    name: Optional[str] = None


@dataclass
class ToolResponse:
    tool_name: str
    result: Optional[str] = None
    error: Optional[str] = None
