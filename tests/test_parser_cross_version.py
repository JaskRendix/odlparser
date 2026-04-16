from odlparser.parser import parse_odl
from odlparser.reader import load_odl_file


def test_mixed_v2_header_v3_block(tmp_path, data_dir):
    v2 = (data_dir / "minimal_v2.odl").read_bytes()
    v3 = (data_dir / "minimal_v3.odl").read_bytes()

    header_v2 = v2[:0x100]
    block_v3 = v3[0x100:]

    path = tmp_path / "mixed_v2_v3.odl"
    path.write_bytes(header_v2 + block_v3)

    version, buffer = load_odl_file(path)
    records = parse_odl(version, buffer, path.name, decryptor=None)

    assert records == []


def test_mixed_v3_header_v2_block(tmp_path, data_dir):
    v2 = (data_dir / "minimal_v2.odl").read_bytes()
    v3 = (data_dir / "minimal_v3.odl").read_bytes()

    header_v3 = v3[:0x100]
    block_v2 = v2[0x100:]

    path = tmp_path / "mixed_v3_v2.odl"
    path.write_bytes(header_v3 + block_v2)

    version, buffer = load_odl_file(path)
    records = parse_odl(version, buffer, path.name, decryptor=None)

    assert records == []
