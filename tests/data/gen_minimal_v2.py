#!/usr/bin/env python3
import struct
from pathlib import Path

out = Path(__file__).parent / "minimal_v2.odl"

# 0x100-byte ODL header matching OdlHeader
header = bytearray(0x100)
header[0:8] = b"EBFGONED"  # signature
header[8:12] = struct.pack("<I", 2)  # odl_version = 2
# rest stays zero

timestamp = 1710000000000
code_file = b"\x04\x00\x00\x00test"
function = b"\x04\x00\x00\x00func"
params = b"\x04\x00\x00\x00abcd"

payload = code_file + b"\x00\x00\x00\x00" + function + params
data_len = len(payload)

cdef_header = bytearray()
cdef_header += b"\xCC\xDD\xEE\xFF"  # signature
cdef_header += struct.pack("<I", 1)  # unknown_flag
cdef_header += struct.pack("<Q", timestamp)  # timestamp
cdef_header += struct.pack("<I", 0)  # unk1
cdef_header += struct.pack("<I", 0)  # unk2
cdef_header += b"\x00" * 20  # unknown[20]
cdef_header += struct.pack("<I", 1)  # one
cdef_header += struct.pack("<I", data_len)  # data_len
cdef_header += struct.pack("<I", 0)  # reserved

with out.open("wb") as f:
    f.write(header)
    f.write(cdef_header)
    f.write(payload)

print("Generated:", out)
