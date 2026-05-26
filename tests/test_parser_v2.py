from odlparser.parser import parse_odl
from odlparser.reader import load_odl_file


def test_v2_header_parsed(data_dir):
    path = data_dir / "minimal_v2.odl"
    odl_file = load_odl_file(path)
    assert odl_file.version == 2
    assert odl_file.data[:4] == b"\xCC\xDD\xEE\xFF"


def test_v2_single_record(data_dir):
    path = data_dir / "minimal_v2.odl"
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert len(records) == 1
    rec = records[0]
    assert rec.index == 1
    assert rec.filename == path.name
    assert rec.timestamp > 0


def test_v2_payload_fields(data_dir):
    path = data_dir / "minimal_v2.odl"
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    rec = records[0]
    assert rec.code_file == "test"
    assert rec.function == "func"
    assert rec.params == "abcd"


def test_parse_minimal_v2(data_dir):
    path = data_dir / "minimal_v2.odl"
    odl_file = load_odl_file(path)
    assert odl_file.version == 2
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert isinstance(records, list)
    assert len(records) >= 1
    rec = records[0]
    assert rec.filename == path.name
    assert rec.index == 1
    assert rec.timestamp > 0
    assert rec.code_file == "test"
    assert rec.function == "func"
    assert rec.params == "abcd"


def test_v2_multiple_blocks(tmp_path, data_dir):
    minimal = (data_dir / "minimal_v2.odl").read_bytes()
    header = minimal[:0x100]
    block = minimal[0x100:]
    combined = header + block + block
    path = tmp_path / "multi_v2.odl"
    path.write_bytes(combined)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert len(records) == 2
    assert records[0].code_file == "test"
    assert records[1].function == "func"


def test_v2_bad_signature(tmp_path, data_dir):
    minimal = (data_dir / "minimal_v2.odl").read_bytes()
    header = minimal[:0x100]
    block = bytearray(minimal[0x100:])
    block[0:4] = b"BAD!"
    path = tmp_path / "bad_v2.odl"
    path.write_bytes(header + block)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert records == []


def test_v2_truncated_header(tmp_path, data_dir):
    minimal = (data_dir / "minimal_v2.odl").read_bytes()
    truncated = minimal[: 0x100 + 10]
    path = tmp_path / "trunc_v2.odl"
    path.write_bytes(truncated)
    odl_file = load_odl_file(path)
    records = parse_odl(odl_file.version, odl_file.data, path.name, decryptor=None)
    assert records == []


def test_v2_odlfile_fields(data_dir):
    path = data_dir / "minimal_v2.odl"
    odl_file = load_odl_file(path)
    assert isinstance(odl_file.version, int)
    assert isinstance(odl_file.data, bytes)
    assert isinstance(odl_file.signature, bytes)
    assert isinstance(odl_file.is_gzip, bool)


def test_v2_signature_exposed(data_dir):
    path = data_dir / "minimal_v2.odl"
    odl_file = load_odl_file(path)
    assert odl_file.signature.startswith(b"EBFGONED")
    assert len(odl_file.signature) >= 4
