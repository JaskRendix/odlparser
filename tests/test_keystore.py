from odlparser.decoder.keystore import Keystore, KeystoreError


def test_load_tiny_keystore(data_dir):
    ks = Keystore.load(data_dir / "tiny_keystore.json")
    assert ks.key
    assert ks.utf_type in ("utf16", "utf32")
