import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from odlparser.decoder.keystore import Keystore
from odlparser.decoder.unobfuscate import OdlDecryptor


def make_keystore(key: bytes, utf="utf-8"):
    return Keystore(key=key, utf_type=utf, version=3)


def test_map_only_unobfuscation():
    decryptor = OdlDecryptor(keystore=None, mapping={"X": "hello"})
    assert decryptor.unobfuscate("X") == "hello"


def test_map_fallback_when_no_keystore():
    decryptor = OdlDecryptor(keystore=None, mapping={"abc": "XYZ"})
    assert decryptor.unobfuscate("abc") == "XYZ"


def test_non_word_tokens_preserved():
    decryptor = OdlDecryptor(keystore=None, mapping={"A": "X"})
    assert decryptor.unobfuscate("A:B") == "X:B"
    assert decryptor.unobfuscate("A@B") == "X@B"
    assert decryptor.unobfuscate("A/B") == "X/B"


def test_unknown_word_falls_back_to_original():
    decryptor = OdlDecryptor(keystore=None, mapping={})
    assert decryptor.unobfuscate("hello") == "hello"


def test_tokenization_mixed_symbols():
    decryptor = OdlDecryptor(keystore=None, mapping={"abc": "X"})
    assert decryptor.unobfuscate("abc:def") == "X:def"
    assert decryptor.unobfuscate("abc.def") == "X.def"
    assert decryptor.unobfuscate("abc/def") == "X/def"


def test_invalid_aes_token_falls_back():
    ks = make_keystore(b"\x00" * 32)
    decryptor = OdlDecryptor(keystore=ks, mapping={})
    assert decryptor.unobfuscate("not_base64") == "not_base64"


def test_short_token_never_decrypted():
    ks = make_keystore(b"\x00" * 32)
    decryptor = OdlDecryptor(keystore=ks, mapping={})
    assert decryptor.unobfuscate("abc") == "abc"  # <22 chars → skip AES


def test_urlsafe_base64_normalization():
    ks = make_keystore(b"\x00" * 32)
    decryptor = OdlDecryptor(keystore=ks, mapping={})

    token = "abcd_efgh-ijkl"  # URL-safe chars
    assert decryptor.unobfuscate(token) == token


def test_aes_decrypt_success():
    key = b"\x11" * 32
    ks = make_keystore(key)
    decryptor = OdlDecryptor(keystore=ks, mapping={})

    cipher = AES.new(key, AES.MODE_CBC, iv=b"\0" * 16)
    encrypted = cipher.encrypt(pad(b"hello", 16))
    token = base64.b64encode(encrypted).decode()

    assert decryptor.unobfuscate(token) == "hello"


def test_aes_then_map_fallback():
    ks = make_keystore(b"\x00" * 32)
    decryptor = OdlDecryptor(keystore=ks, mapping={"abc": "XYZ"})
    assert decryptor.unobfuscate("abc") == "XYZ"


def test_mixed_aes_and_map_tokens():
    key = b"\x11" * 32
    ks = make_keystore(key)
    decryptor = OdlDecryptor(keystore=ks, mapping={"foo": "BAR"})

    cipher = AES.new(key, AES.MODE_CBC, iv=b"\0" * 16)
    encrypted = cipher.encrypt(pad(b"hello", 16))
    aes_token = base64.b64encode(encrypted).decode()

    text = f"{aes_token}:foo"
    assert decryptor.unobfuscate(text) == "hello:BAR"
