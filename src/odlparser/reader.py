"""
Low-level file reader for OneDrive ODL logs.

Responsibilities:
- Validate file existence
- Detect empty files
- Read ODL header
- Detect gzip compression
- Decompress if needed
- Return a clean byte buffer for the parser

This module contains *no* parsing logic — only file I/O and decompression.
"""

from __future__ import annotations

import io
import zlib
from pathlib import Path

from .structures import OdlHeader


class OdlReadError(Exception):
    """Raised when an ODL file cannot be read or decoded."""


def is_file_empty(path: str | Path) -> bool:
    """
    Check if a file exists and has size 0.
    """
    path = Path(path)
    return path.exists() and path.stat().st_size == 0


def read_odl_header(raw: bytes) -> tuple[int, bytes]:
    """
    Parse the ODL header and return:
        (version, signature_bytes)

    Raises:
        OdlReadError if the header is invalid.
    """
    try:
        header = OdlHeader.parse(raw)
    except Exception as ex:
        raise OdlReadError(f"Failed to parse ODL header: {ex}") from ex

    version = header.odl_version
    signature = header.signature

    if version not in (2, 3):
        raise OdlReadError(f"Unsupported ODL version: {version}")

    return version, signature


GZIP_MAGIC = b"\x1F\x8B\x08\x00"


def _maybe_decompress_gzip(f: io.BufferedReader, start_pos: int) -> io.BytesIO:
    """
    Detect gzip header and decompress if needed.

    Args:
        f: open file object positioned at the start of the CDEF header.
        start_pos: file offset where CDEF or gzip header begins.

    Returns:
        BytesIO containing decompressed or raw data.
    """
    # Peek 8 bytes
    header = f.read(8)
    f.seek(start_pos)

    if header.startswith(GZIP_MAGIC):
        try:
            f.seek(start_pos - 8)
            all_data = f.read()
            z = zlib.decompressobj(31)  # gzip wrapper
            decompressed = z.decompress(all_data)
            return io.BytesIO(decompressed)
        except Exception as ex:
            raise OdlReadError(f"Gzip decompression failed: {ex}") from ex

    # Not gzip → return raw file object wrapped in BytesIO
    f.seek(start_pos)
    return io.BytesIO(f.read())


def load_odl_file(path: str | Path) -> tuple[int, bytes]:
    """
    Load an ODL file and return:
        (version, full_data_bytes)

    Steps:
    - Read first 0x100 bytes (ODL header)
    - Parse version
    - Seek to first CDEF or gzip header
    - Decompress if needed
    - Return clean byte buffer

    Raises:
        OdlReadError for any I/O or format issue.
    """
    path = Path(path)

    if not path.exists():
        raise OdlReadError(f"File not found: {path}")

    if is_file_empty(path):
        raise OdlReadError(f"File is empty: {path}")

    try:
        with path.open("rb") as f:
            # Read ODL header (always 0x100 bytes)
            raw_header = f.read(0x100)

            # Entire file is gzip-wrapped; decompress from start
            if raw_header.startswith(b"\x1f\x8b"):
                f.seek(0)
                all_data = f.read()
                try:
                    z = zlib.decompressobj(31)  # gzip wrapper
                    decompressed = z.decompress(all_data)
                except Exception as ex:
                    raise OdlReadError(f"Gzip decompression failed: {ex}") from ex

                if len(decompressed) < 0x100:
                    raise OdlReadError("Decompressed ODL data too short")

                # Now treat decompressed bytes as a normal ODL file
                header_bytes = decompressed[:0x100]
                version, signature = read_odl_header(header_bytes)

                if signature.startswith(b"EBFGONED"):
                    data = decompressed[0x100:]
                else:
                    data = decompressed[8:]

                return version, data

            version, signature = read_odl_header(raw_header)

            # If signature matches, skip header
            if signature.startswith(b"EBFGONED"):
                f.seek(0x100)
                start_pos = 0x100
            else:
                # Rare case: no ODL header, start at offset 8
                f.seek(8)
                start_pos = 8

            # Detect gzip or raw CDEF
            buffer = _maybe_decompress_gzip(f, start_pos)

            # Return version + full data
            return version, buffer.read()

    except Exception as ex:
        raise OdlReadError(f"Failed to load ODL file {path}: {ex}") from ex
