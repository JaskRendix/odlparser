"""
High-level ODL parser (refactored + test-compatible).

This version:
- Uses strategy classes (v2/v3)
- Avoids duplication
- Injects decoder
- Returns int timestamps (tests expect this)
- Silently skips invalid headers (tests expect this)
"""

from __future__ import annotations

import io
import struct
from typing import BinaryIO

from .decoder.string_extract import extract_strings
from .decoder.unobfuscate import OdlDecryptor
from .models import OdlRecord
from .structures import CDEF_V2, CDEF_V3


def _read_string(data: bytes, pos: int) -> tuple[int, str]:
    """Read a length-prefixed UTF-8 string from data[pos:]."""
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


class BaseCdefParser:
    """Abstract base class for CDEF block parsers."""

    HEADER_SIZE: int = 0

    def parse_header(self, header_bytes: bytes):
        raise NotImplementedError

    def compute_data_length(self, header) -> int:
        raise NotImplementedError

    def skip_context(self, buffer: BinaryIO, header) -> None:
        """Skip context data if present (v3 only)."""
        return

    def parse_block(
        self,
        buffer: BinaryIO,
        filename: str,
        index: int,
        decoder: OdlDecryptor | None,
    ) -> OdlRecord | None:
        """Unified block parsing logic."""
        header_bytes = buffer.read(self.HEADER_SIZE)
        if len(header_bytes) < self.HEADER_SIZE:
            return None

        # IMPORTANT: tests expect invalid headers to be silently skipped
        try:
            header = self.parse_header(header_bytes)
        except Exception:
            return None

        self.skip_context(buffer, header)
        data_len = self.compute_data_length(header)

        if data_len <= 4:
            return None

        data = buffer.read(data_len)
        if len(data) < data_len:
            return None

        pos = 0

        consumed, code_file = _read_string(data, pos)
        pos += consumed

        pos += 4  # flags

        consumed, function = _read_string(data, pos)
        pos += consumed

        params_raw = data[pos:] if pos < len(data) else b""
        params = extract_strings(params_raw, decryptor=decoder, unobfuscate=True)

        # IMPORTANT: tests expect raw integer timestamps, not datetime
        return OdlRecord(
            filename=filename,
            index=index,
            timestamp=header.timestamp,
            code_file=code_file,
            function=function,
            params=params,
        )


class CdefParserV2(BaseCdefParser):
    HEADER_SIZE = 56

    def parse_header(self, header_bytes: bytes):
        header = CDEF_V2.parse(header_bytes)

        # These validations must NOT raise — tests expect silent skip
        if header.unknown_flag not in (0, 1):
            raise ValueError("invalid v2 unknown_flag")

        if header.one != 1:
            raise ValueError("invalid v2 'one' field")

        if header.data_len > 10_000_000:
            raise ValueError("v2 data_len too large")

        return header

    def compute_data_length(self, header) -> int:
        return header.data_len


class CdefParserV3(BaseCdefParser):
    HEADER_SIZE = 32

    def parse_header(self, header_bytes: bytes):
        return CDEF_V3.parse(header_bytes)

    def skip_context(self, buffer: BinaryIO, header) -> None:
        if header.context_data_len > 0:
            buffer.seek(header.context_data_len, io.SEEK_CUR)
        else:
            buffer.seek(24, io.SEEK_CUR)

    def compute_data_length(self, header) -> int:
        if header.context_data_len > 0:
            return header.data_len - header.context_data_len
        return header.data_len - 24


def _get_parser(version: int) -> BaseCdefParser:
    if version == 2:
        return CdefParserV2()
    elif version == 3:
        return CdefParserV3()
    raise ValueError(f"Unsupported ODL version: {version}")


def parse_odl(
    version: int,
    raw_data: bytes,
    filename: str,
    decryptor: OdlDecryptor | None = None,
) -> list[OdlRecord]:
    """
    Parse an ODL file into a list of OdlRecord objects.
    """
    parser = _get_parser(version)
    buffer = io.BytesIO(raw_data)

    records: list[OdlRecord] = []
    index = 1

    while True:
        record = parser.parse_block(buffer, filename, index, decryptor)
        if record is None:
            break
        records.append(record)
        index += 1

    return records
