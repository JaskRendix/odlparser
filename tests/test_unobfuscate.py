from odlparser.decoder.unobfuscate import OdlDecryptor


def test_map_only_unobfuscation():
    decryptor = OdlDecryptor(keystore=None, mapping={"X": "hello"})
    assert decryptor.unobfuscate("X") == "hello"
