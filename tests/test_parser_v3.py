from odlparser.parser import parse_odl
from odlparser.reader import load_odl_file


def test_v3_header_parsed(data_dir):
    path = data_dir / "minimal_v3.odl"
    odl_file = load_odl_file(path)
    assert odl_file.version == 3
    assert odl_file.data[:4] == b"\xCC\xDD\xEE\xFF"


def test_v3_single_record(data_dir):
    path = data_dir / "minimal_v3.odl"
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert len(records) == 1
    rec = records[0]
    assert rec.index == 1
    assert rec.filename == path.name
    assert rec.timestamp > 0


def test_v3_payload_fields(data_dir):
    path = data_dir / "minimal_v3.odl"
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    rec = records[0]
    assert rec.code_file == "test"
    assert rec.function == "func"
    assert rec.params == "abcd"


def test_parse_minimal_v3(data_dir):
    path = data_dir / "minimal_v3.odl"
    odl_file = load_odl_file(path)
    assert odl_file.version == 3
    records = parse_odl(
        odl_file.version, odl_file.data, "minimal_v3.odl", decryptor=None
    )
    assert len(records) >= 1


def test_v3_multiple_blocks(tmp_path, data_dir):
    minimal = (data_dir / "minimal_v3.odl").read_bytes()
    header = minimal[:0x100]
    block = minimal[0x100:]
    combined = header + block + block
    path = tmp_path / "multi_v3.odl"
    path.write_bytes(combined)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert len(records) == 2
    assert records[0].params == "abcd"


def test_v3_bad_signature(tmp_path, data_dir):
    minimal = (data_dir / "minimal_v3.odl").read_bytes()
    header = minimal[:0x100]
    block = bytearray(minimal[0x100:])
    block[0:4] = b"BAD!"
    path = tmp_path / "bad_v3.odl"
    path.write_bytes(header + block)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert records == []


def test_v3_truncated_context(tmp_path, data_dir):
    minimal = (data_dir / "minimal_v3.odl").read_bytes()
    truncated = minimal[: 0x100 + 20]
    path = tmp_path / "trunc_v3.odl"
    path.write_bytes(truncated)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert records == []


def test_v3_odlfile_fields(data_dir):
    path = data_dir / "minimal_v3.odl"
    odl_file = load_odl_file(path)
    assert isinstance(odl_file.version, int)
    assert isinstance(odl_file.data, bytes)
    assert isinstance(odl_file.signature, bytes)
    assert isinstance(odl_file.is_gzip, bool)


def test_v3_signature_exposed(data_dir):
    path = data_dir / "minimal_v3.odl"
    odl_file = load_odl_file(path)
    assert odl_file.signature.startswith(b"EBFGONED")
    assert len(odl_file.signature) >= 4
