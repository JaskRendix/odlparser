"""
Typed data models for the modern ODL parser.

These dataclasses represent the structured output of the parser.
They are intentionally minimal and immutable, making them ideal
for downstream processing, CSV export, or integration into DFIR
pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OdlRecord:
    """
    Represents a single parsed ODL log entry.

    Attributes:
        filename: Name of the ODL file the record came from.
        index: Sequential index of the record within the file.
        timestamp: Unix millisecond timestamp converted to datetime.
        code_file: Source file name inside the OneDrive sync engine.
        function: Function name inside the OneDrive sync engine.
        params: Decoded parameters (string or list of strings).
    """

    filename: str
    index: int
    timestamp: datetime
    code_file: str
    function: str
    params: str | list[str]
