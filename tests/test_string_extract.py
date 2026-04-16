from odlparser.decoder.string_extract import extract_strings


def test_length_prefix_mismatch_allowed():
    data = b"\x04\x00\x00\x00hello!"
    assert extract_strings(data) == "hell"


def test_extract_simple_ascii():
    data = b"\x04\x00\x00\x00test"
    result = extract_strings(data, decryptor=None)
    assert result == "test"
