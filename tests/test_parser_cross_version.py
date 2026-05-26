from odlparser.parser import parse_odl
from odlparser.reader import load_odl_file


def test_mixed_v2_header_v3_block(tmp_path, data_dir):
    v2 = (data_dir / "minimal_v2.odl").read_bytes()
    v3 = (data_dir / "minimal_v3.odl").read_bytes()
    header_v2 = v2[:0x100]
    block_v3 = v3[0x100:]
    path = tmp_path / "mixed_v2_v3.odl"
    path.write_bytes(header_v2 + block_v3)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert records == []


def test_mixed_v3_header_v2_block(tmp_path, data_dir):
    v2 = (data_dir / "minimal_v2.odl").read_bytes()
    v3 = (data_dir / "minimal_v3.odl").read_bytes()
    header_v3 = v3[:0x100]
    block_v2 = v2[0x100:]
    path = tmp_path / "mixed_v3_v2.odl"
    path.write_bytes(header_v3 + block_v2)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert records == []


def test_cross_version_odlfile_fields(tmp_path, data_dir):
    v2 = (data_dir / "minimal_v2.odl").read_bytes()
    v3 = (data_dir / "minimal_v3.odl").read_bytes()
    path = tmp_path / "cross_meta.odl"
    path.write_bytes(v2[:0x100] + v3[0x100:])
    odl_file = load_odl_file(path)
    assert isinstance(odl_file.version, int)
    assert isinstance(odl_file.data, bytes)
    assert isinstance(odl_file.signature, bytes)
    assert isinstance(odl_file.is_gzip, bool)


def test_cross_version_signature_exposed(tmp_path, data_dir):
    v2 = (data_dir / "minimal_v2.odl").read_bytes()
    v3 = (data_dir / "minimal_v3.odl").read_bytes()
    path = tmp_path / "cross_sig.odl"
    path.write_bytes(v3[:0x100] + v2[0x100:])
    odl_file = load_odl_file(path)
    assert odl_file.signature.startswith(b"EBFGONED")
    assert len(odl_file.signature) >= 4
