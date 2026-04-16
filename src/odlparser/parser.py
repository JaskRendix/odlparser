"""
High-level ODL parser.

This module:
- Accepts raw ODL bytes from reader.load_odl_file()
- Iterates through CDEF blocks (v2 or v3)
- Extracts timestamp, code file, function, parameters
- Uses OdlDecryptor + extract_strings() for unobfuscation
- Returns a list of OdlRecord objects

No filtering, no CSV, no CLI — pure parsing.
"""

from __future__ import annotations

import io
import struct

from .decoder.string_extract import extract_strings
from .decoder.unobfuscate import OdlDecryptor
from .models import OdlRecord
from .structures import CDEF_V2, CDEF_V3


class OdlParseError(Exception):
    """Raised when an ODL file cannot be parsed."""


def _read_string(data: bytes, pos: int) -> tuple[int, str]:
    """
    Read a length-prefixed UTF-8 string from data[pos:].

    Returns:
        (bytes_consumed, decoded_string)
    """
    if len(data) < pos + 4:
        return 0, ""

    try:
        strlen = struct.unpack("<I", data[pos : pos + 4])[0]
    except Exception:
        return 0, ""

    start = pos + 4
    end = start + strlen

    if end > len(data):
        return 4, ""

    try:
        return 4 + strlen, data[start:end].decode("utf8", "ignore")
    except Exception:
        return 4 + strlen, ""


def _parse_v2_block(
    buffer: io.BytesIO, decryptor: OdlDecryptor | None, filename: str, index: int
) -> OdlRecord | None:
    """
    Parse a single CDEF v2 block.
    Returns an OdlRecord or None if block is empty.
    """
    header_bytes = buffer.read(56)
    if len(header_bytes) < 56:
        return None

    try:
        header = CDEF_V2.parse(header_bytes)
    except Exception:
        return None

    # v2: unknown_flag is always 0 or 1
    if getattr(header, "unknown_flag", None) not in (0, 1):
        return None
    # v2: "one" field is always exactly 1
    if getattr(header, "one", None) != 1:
        return None
    # v2: data_len is small and sane; v3 data_len is much larger
    if header.data_len > 10_000_000:
        return None

    if header.data_len <= 4:
        return None

    data = buffer.read(header.data_len)
    pos = 0

    consumed, code_file = _read_string(data, pos)
    pos += consumed

    pos += 4  # flags

    consumed, function = _read_string(data, pos)
    pos += consumed

    params_raw = data[pos:] if pos < len(data) else b""
    params = extract_strings(params_raw, decryptor=decryptor, unobfuscate=True)

    return OdlRecord(
        filename=filename,
        index=index,
        timestamp=header.timestamp,
        code_file=code_file,
        function=function,
        params=params,
    )


def _parse_v3_block(
    buffer: io.BytesIO, decryptor: OdlDecryptor | None, filename: str, index: int
) -> OdlRecord | None:
    """
    Parse a single CDEF v3 block.
    Returns an OdlRecord or None if block is empty.
    """
    header_bytes = buffer.read(32)
    if len(header_bytes) < 32:
        return None

    try:
        header = CDEF_V3.parse(header_bytes)
    except Exception:
        return None

    if header.data_len <= 4:
        return None

    if header.context_data_len > 0:
        buffer.seek(header.context_data_len, io.SEEK_CUR)
        data_len = header.data_len - header.context_data_len
    else:
        buffer.seek(24, io.SEEK_CUR)
        data_len = header.data_len - 24

    data = buffer.read(data_len)
    pos = 0

    consumed, code_file = _read_string(data, pos)
    pos += consumed

    pos += 4  # flags

    consumed, function = _read_string(data, pos)
    pos += consumed

    params_raw = data[pos:] if pos < len(data) else b""
    params = extract_strings(params_raw, decryptor=decryptor, unobfuscate=True)

    return OdlRecord(
        filename=filename,
        index=index,
        timestamp=header.timestamp,
        code_file=code_file,
        function=function,
        params=params,
    )


def parse_odl(
    version: int, raw_data: bytes, filename: str, decryptor: OdlDecryptor | None = None
) -> list[OdlRecord]:
    """
    Parse an ODL file into a list of OdlRecord objects.

    Args:
        version: ODL version (2 or 3)
        raw_data: full decompressed ODL data (after header)
        filename: original filename (for reporting)
        decryptor: optional OdlDecryptor for unobfuscation

    Returns:
        List[OdlRecord]
    """
    buffer = io.BytesIO(raw_data)
    records: list[OdlRecord] = []
    index = 1

    while True:
        if version == 2:
            record = _parse_v2_block(buffer, decryptor, filename, index)
        else:
            record = _parse_v3_block(buffer, decryptor, filename, index)

        if record is None:
            break

        records.append(record)
        index += 1

    return records
