#!/usr/bin/env python3
import os
import struct
from pathlib import Path

out = Path(__file__).parent / "minimal_v3.odl"

# 0x100-byte ODL header matching OdlHeader
header = bytearray(0x100)
header[0:8] = b"EBFGONED"
header[8:12] = struct.pack("<I", 3)  # odl_version = 3

timestamp = 1710000000000
code_file = b"\x04\x00\x00\x00test"
function = b"\x04\x00\x00\x00func"
params = b"\x04\x00\x00\x00abcd"

context = os.urandom(24)
payload = code_file + b"\x00\x00\x00\x00" + function + params
data_len = len(context) + len(payload)

cdef_header = bytearray()
cdef_header += b"\xCC\xDD\xEE\xFF"  # signature
cdef_header += struct.pack("<H", len(context))  # context_data_len (Int16)
cdef_header += struct.pack("<H", 1)  # unknown_flag
cdef_header += struct.pack("<Q", timestamp)  # timestamp
cdef_header += struct.pack("<I", 0)  # unk1
cdef_header += struct.pack("<I", 0)  # unk2
cdef_header += struct.pack("<I", data_len)  # data_len
cdef_header += struct.pack("<I", 0)  # reserved

with out.open("wb") as f:
    f.write(header)
    f.write(cdef_header)
    f.write(context)
    f.write(payload)

print("Generated:", out)
