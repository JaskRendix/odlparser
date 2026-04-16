"""
Keystore loader for OneDrive ODL logs.

Newer OneDrive versions (April 2022+) encrypt obfuscated strings using AES.
The AES key and metadata are stored in a JSON file named `general.keystore`.

This module:
- Detects file encoding (UTF-8 or UTF-16LE)
- Loads the keystore JSON
- Extracts the AES key
- Determines the UTF type (utf16 or utf32)
- Provides a clean, object-oriented interface for the decryptor
"""

from __future__ import annotations

import json
from pathlib import Path


class KeystoreError(Exception):
    """Raised when the keystore cannot be parsed."""


def guess_encoding(path: Path) -> str:
    """
    Guess whether the keystore or obfuscation map is UTF-8 or UTF-16LE.

    The original script used a heuristic based on null bytes.
    """
    with path.open("rb") as f:
        data = f.read(4)

    if len(data) < 4:
        return "utf-8"

    # UTF-16LE typically has 0x00 in odd positions
    if data[1] == 0 and data[3] == 0 and data[0] != 0 and data[2] != 0:
        return "utf-16le"

    return "utf-8"


class Keystore:
    """
    Represents a loaded OneDrive keystore.

    Attributes:
        key (bytes): AES key used for unobfuscation.
        utf_type (str): 'utf16' or 'utf32' depending on key metadata.
        version (int): Keystore version (usually 1).
    """

    def __init__(self, key: bytes, utf_type: str, version: int):
        self.key = key
        self.utf_type = utf_type
        self.version = version

    @classmethod
    def load(cls, path: str | Path) -> "Keystore":
        """
        Load and parse a OneDrive keystore JSON file.

        Raises:
            KeystoreError: if the file cannot be parsed or is invalid.
        """
        path = Path(path)

        if not path.exists():
            raise KeystoreError(f"Keystore not found: {path}")

        encoding = guess_encoding(path)

        try:
            with path.open("r", encoding=encoding) as f:
                data = json.load(f)
        except Exception as ex:
            raise KeystoreError(f"Failed to parse keystore JSON: {ex}") from ex

        try:
            entry = data[0]
            key_b64 = entry["Key"]
            version = entry["Version"]
        except Exception as ex:
            raise KeystoreError(f"Invalid keystore structure: {ex}") from ex

        # Determine UTF type
        utf_type = "utf32" if key_b64.endswith("\\u0000\\u0000") else "utf16"

        # Decode base64 key
        try:
            import base64

            key = base64.b64decode(key_b64)
        except Exception as ex:
            raise KeystoreError(f"Failed to decode AES key: {ex}") from ex

        if version != 1:
            # Not fatal, but worth warning
            print(f"WARNING: Keystore version {version} may not be supported.")

        return cls(key=key, utf_type=utf_type, version=version)

    def __repr__(self) -> str:
        return f"<Keystore version={self.version} utf={self.utf_type} key_len={len(self.key)}>"
