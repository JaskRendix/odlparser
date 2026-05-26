from odlparser.structures import CDEF_V2, CDEF_V3


def test_cdef_v2_parse_minimal():
    raw = (
        b"\xCC\xDD\xEE\xFF"  # signature
        + b"\x01\x00\x00\x00"  # unknown_flag
        + b"\x11\x22\x33\x44\x55\x66\x77\x88"  # timestamp (8 bytes)
        + b"\x02\x00\x00\x00"  # unk1
        + b"\x03\x00\x00\x00"  # unk2
        + b"\x00" * 20  # unknown[20]
        + b"\x01\x00\x00\x00"  # one = 1
        + b"\x10\x00\x00\x00"  # data_len = 16
        + b"\x00\x00\x00\x00"  # reserved = 0
    )

    obj = CDEF_V2.parse(raw)

    assert obj.signature == b"\xCC\xDD\xEE\xFF"
    assert obj.unknown_flag == 1
    assert obj.timestamp == 0x8877665544332211
    assert obj.unk1 == 2
    assert obj.unk2 == 3
    assert obj.one == 1
    assert obj.data_len == 16
    assert obj.reserved == 0
    assert len(obj.unknown) == 20


def test_cdef_v3_parse_minimal():
    raw = (
        b"\xCC\xDD\xEE\xFF"  # signature
        + b"\x10\x00"  # context_data_len = 16 (Int16ul)
        + b"\x01\x00"  # unknown_flag = 1 (Int16ul)
        + b"\x11\x22\x33\x44\x55\x66\x77\x88"  # timestamp
        + b"\x02\x00\x00\x00"  # unk1
        + b"\x03\x00\x00\x00"  # unk2
        + b"\x10\x00\x00\x00"  # data_len = 16
        + b"\x00\x00\x00\x00"  # reserved = 0
    )

    obj = CDEF_V3.parse(raw)

    assert obj.signature == b"\xCC\xDD\xEE\xFF"
    assert obj.context_data_len == 16
    assert obj.unknown_flag == 1
    assert obj.timestamp == 0x8877665544332211
    assert obj.unk1 == 2
    assert obj.unk2 == 3
    assert obj.data_len == 16
    assert obj.reserved == 0
