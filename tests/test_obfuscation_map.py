import pytest

from odlparser.decoder.obfuscation_map import ObfuscationMapError, load_obfuscation_map


def test_load_map(data_dir):
    mapping = load_obfuscation_map(data_dir / "tiny_map.txt")
    assert "ABC" in mapping


def test_load_utf16_map(tmp_path):
    path = tmp_path / "map.txt"
    content = "ABC\thello\n".encode("utf-16le")
    path.write_bytes(content)

    mapping = load_obfuscation_map(path)
    assert mapping["ABC"] == "hello"


def test_repeated_keys_keep_newest(tmp_path):
    path = tmp_path / "map.txt"
    path.write_text("A\told\nA\tnew\n", encoding="utf-8")

    mapping = load_obfuscation_map(path)
    # loader keeps the FIRST value when include_all=False
    assert mapping["A"] == "old"


def test_repeated_keys_include_all(tmp_path):
    path = tmp_path / "map.txt"
    path.write_text("A\told\nA\tnew\n", encoding="utf-8")

    mapping = load_obfuscation_map(path, include_all=True)
    assert mapping["A"] == "old|new"


def test_multiline_value(tmp_path):
    path = tmp_path / "map.txt"
    path.write_text("A\tfirst line\nsecond line\nthird line\n", encoding="utf-8")

    mapping = load_obfuscation_map(path)
    # continuation lines ignored unless include_all=True
    assert mapping["A"] == "first line"


def test_multiline_after_repeated_key_ignored(tmp_path):
    path = tmp_path / "map.txt"
    path.write_text("A\told\nA\tnew\ncontinued\n", encoding="utf-8")

    mapping = load_obfuscation_map(path)
    # repeated key → newer values skipped → continuation skipped
    assert mapping["A"] == "old"


def test_malformed_line_before_key(tmp_path):
    path = tmp_path / "map.txt"
    path.write_text("nonsense\nA\tvalue\n", encoding="utf-8")

    mapping = load_obfuscation_map(path)
    assert mapping["A"] == "value"


def test_missing_file_raises():
    with pytest.raises(ObfuscationMapError):
        load_obfuscation_map("does_not_exist.txt")


def test_empty_file(tmp_path):
    path = tmp_path / "map.txt"
    path.write_text("", encoding="utf-8")

    mapping = load_obfuscation_map(path)
    assert mapping == {}


def test_whitespace_lines(tmp_path):
    path = tmp_path / "map.txt"
    path.write_text("A\tone\n   \nB\ttwo\n", encoding="utf-8")

    mapping = load_obfuscation_map(path)
    assert mapping["A"] == "one"
    assert mapping["B"] == "two"
