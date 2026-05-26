import base64
import json

import pytest

from odlparser.decoder.keystore import Keystore, KeystoreError, guess_encoding


def make_keystore_json(key_bytes: bytes, version=1, utf32=False):
    """Helper to build a valid keystore JSON structure."""
    key_b64 = base64.b64encode(key_bytes).decode()

    # utf32 detection is based on the *string* ending
    if utf32:
        key_b64 += "\\u0000\\u0000"

    return json.dumps([{"Key": key_b64, "Version": version}])


def test_load_tiny_keystore(data_dir):
    ks = Keystore.load(data_dir / "tiny_keystore.json")
    assert ks.key
    assert ks.utf_type in ("utf16", "utf32")


def test_load_utf8_keystore(tmp_path):
    key = b"\x11" * 32
    path = tmp_path / "ks.json"
    path.write_text(make_keystore_json(key), encoding="utf-8")

    ks = Keystore.load(path)
    assert ks.key == key
    assert ks.utf_type == "utf16"  # default unless utf32 marker present


def test_load_utf16le_keystore(tmp_path):
    key = b"\x22" * 32
    path = tmp_path / "ks.json"
    content = make_keystore_json(key).encode("utf-16le")
    path.write_bytes(content)

    ks = Keystore.load(path)
    assert ks.key == key


def test_utf32_detection(tmp_path):
    key = b"\x33" * 32
    path = tmp_path / "ks.json"
    path.write_text(make_keystore_json(key, utf32=True), encoding="utf-8")

    ks = Keystore.load(path)
    assert ks.utf_type == "utf32"


def test_missing_file_raises():
    with pytest.raises(KeystoreError):
        Keystore.load("does_not_exist.json")


def test_invalid_json_raises(tmp_path):
    path = tmp_path / "ks.json"
    path.write_text("{not valid json}", encoding="utf-8")

    with pytest.raises(KeystoreError):
        Keystore.load(path)


def test_invalid_structure_raises(tmp_path):
    path = tmp_path / "ks.json"
    path.write_text(json.dumps({"Key": "abc"}), encoding="utf-8")  # not a list

    with pytest.raises(KeystoreError):
        Keystore.load(path)


def test_invalid_base64_key_raises(tmp_path):
    path = tmp_path / "ks.json"
    bad_json = json.dumps([{"Key": "!!!notbase64!!!", "Version": 1}])
    path.write_text(bad_json, encoding="utf-8")

    with pytest.raises(KeystoreError):
        Keystore.load(path)


def test_version_warning(tmp_path, capsys):
    key = b"\x44" * 32
    path = tmp_path / "ks.json"
    path.write_text(make_keystore_json(key, version=99), encoding="utf-8")

    ks = Keystore.load(path)
    captured = capsys.readouterr().out
    assert "WARNING" in captured
    assert ks.version == 99


def test_guess_encoding_utf8(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("hello", encoding="utf-8")
    assert guess_encoding(path) == "utf-8"


def test_guess_encoding_utf16le(tmp_path):
    path = tmp_path / "file.txt"
    path.write_bytes("ABCD".encode("utf-16le"))
    assert guess_encoding(path) == "utf-16le"
