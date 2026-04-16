from odlparser.decoder.obfuscation_map import load_obfuscation_map


def test_load_map(data_dir):
    mapping = load_obfuscation_map(data_dir / "tiny_map.txt")
    assert "ABC" in mapping
