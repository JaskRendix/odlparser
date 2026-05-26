import struct

from odlparser.decoder.string_extract import extract_strings
from odlparser.decoder.unobfuscate import OdlDecryptor


def make_blob(text: str) -> bytes:
    """Build a valid blob: [len][ASCII] where ASCII starts at offset 4."""
    raw = text.encode("ascii")
    return struct.pack("<I", len(raw)) + raw


def test_extract_simple_ascii():
    data = make_blob("test")
    assert extract_strings(data) == "test"


def test_length_prefix_mismatch_allowed():
    data = b"\x04\x00\x00\x00hello!"
    assert extract_strings(data) == "hell"


def test_length_prefix_mismatch_too_large():
    data = b"\x04\x00\x00\x00" + b"A" * 20
    assert extract_strings(data) == ""


def test_multiple_strings():
    data = make_blob("test") + make_blob("abcd")
    assert extract_strings(data) == ["test", "abcd"]


def test_non_ascii_ignored():
    data = b"\x04\x00\x00\x00" + "tëst".encode("utf-8")
    assert extract_strings(data) == ""


def test_newlines_split_into_two_strings():
    data = make_blob("hello\nworld")
    assert extract_strings(data) == ["hello", "world"]


def test_carriage_returns_split_into_two_strings():
    data = make_blob("hello\rworld")
    assert extract_strings(data) == ["hello", "world"]


def test_no_length_prefix_returns_empty():
    data = b"abcdEFGH"
    assert extract_strings(data) == ""


def test_unobfuscation_applied():
    decryptor = OdlDecryptor(keystore=None, mapping={"test": "BAR"})
    data = make_blob("test")
    assert extract_strings(data, decryptor=decryptor) == "BAR"


def test_unobfuscation_disabled():
    decryptor = OdlDecryptor(keystore=None, mapping={"test": "BAR"})
    data = make_blob("test")
    assert extract_strings(data, decryptor=decryptor, unobfuscate=False) == "test"


def test_prefix_before_start_ignored():
    data = b"hello"
    assert extract_strings(data) == ""


def test_partial_decode_ignores_invalid_utf8():
    raw = b"he\xffllo"
    data = struct.pack("<I", 5) + raw
    # No ASCII run ≥4 chars → extractor returns ""
    assert extract_strings(data) == ""
