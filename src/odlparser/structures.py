"""
Binary structure definitions for OneDrive ODL logs.

These are pure Construct definitions for:
- ODL file header
- CDEF (v2) blocks
- CDEF (v3) blocks

This module contains no parsing logic — only binary layouts.
"""

from construct import Byte, Bytes, Const, Struct
from construct.core import Int16ul, Int32ul, Int64ul

OdlHeader = Struct(
    "signature" / Bytes(8),  # Expected: b'EBFGONED'
    "odl_version" / Int32ul,  # 2 or 3
    "unknown_2" / Int32ul,
    "unknown_3" / Int64ul,
    "unknown_4" / Int32ul,
    "one_drive_version" / Byte[0x40],
    "windows_version" / Byte[0x40],
    "reserved" / Byte[0x64],
)


CDEF_V2 = Struct(
    "signature" / Const(b"\xCC\xDD\xEE\xFF"),
    "unknown_flag" / Int32ul,
    "timestamp" / Int64ul,
    "unk1" / Int32ul,
    "unk2" / Int32ul,
    "unknown" / Byte[20],
    "one" / Int32ul,  # Always 1
    "data_len" / Int32ul,  # Length of following data
    "reserved" / Int32ul,  # Always 0
)


CDEF_V3 = Struct(
    "signature" / Const(b"\xCC\xDD\xEE\xFF"),
    "context_data_len" / Int16ul,
    "unknown_flag" / Int16ul,
    "timestamp" / Int64ul,
    "unk1" / Int32ul,
    "unk2" / Int32ul,
    "data_len" / Int32ul,
    "reserved" / Int32ul,  # Always 0
)
