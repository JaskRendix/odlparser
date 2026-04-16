"""
String extraction utilities for OneDrive ODL logs.

ODL parameters often contain embedded strings preceded by a 4-byte
little-endian length field. This module extracts those strings and
optionally unobfuscates them using the OdlDecryptor.

This module provides:
- ASCII-only extraction (matching original behavior)
- Length-prefix validation
- Optional unobfuscation via decryptor.unobfuscate()
"""

from __future__ import annotations

import re
import struct

from .unobfuscate import OdlDecryptor

# Printable ASCII except control chars — **bytes regex**
PRINTABLE = (
    rb"[A-Za-z0-9"
    rb"\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29"
    rb"\x2A\x2B\x2C\x2D\x2E\x2F"
    rb"\x30-\x39"
    rb"\x3A\x3B\x3C\x3D\x3E\x3F"
    rb"\x40-\x5A"
    rb"\x5B\x5C\x5D\x5E\x5F\x60"
    rb"\x61-\x7A"
    rb"\x7B\x7C\x7D\x7E"
    rb"]"
)

# Match sequences of printable ASCII of length ≥ 4
ASCII_RE = re.compile(PRINTABLE + rb"{4,}")


def _read_length_prefix(data: bytes, pos: int) -> int | None:
    """Read a 4-byte little-endian length prefix preceding a string."""
    if pos < 4:
        return None

    try:
        return struct.unpack("<I", data[pos - 4 : pos])[0]
    except Exception:
        return None


def extract_strings(
    data: bytes, decryptor: OdlDecryptor | None = None, unobfuscate: bool = True
) -> str | list[str]:
    """
    Extract ASCII strings from a parameter blob.
    """
    results: list[str] = []

    for match in ASCII_RE.finditer(data):
        start = match.start()
        end = match.end()
        raw: bytes = match.group()

        stored_len = _read_length_prefix(data, start)
        if stored_len is None:
            continue

        actual_len = end - start

        # Validate length prefix (allow small mismatch like original)
        if actual_len - stored_len > 5:
            continue

        try:
            text = raw[:stored_len].decode("utf8", "ignore")
        except Exception:
            continue

        text = text.rstrip("\r\n").replace("\r", "").replace("\n", " ")

        if unobfuscate and decryptor:
            text = decryptor.unobfuscate(text)

        results.append(text)

    if not results:
        return ""
    if len(results) == 1:
        return results[0]
    return results
