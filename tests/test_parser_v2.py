from odlparser.parser import parse_odl
from odlparser.reader import load_odl_file


def test_v2_header_parsed(data_dir):
    path = data_dir / "minimal_v2.odl"
    version, buffer = load_odl_file(path)
    assert version == 2
    assert buffer[:4] == b"\xCC\xDD\xEE\xFF"  # first CDEF signature


def test_v2_single_record(data_dir):
    path = data_dir / "minimal_v2.odl"
    version, buffer = load_odl_file(path)
    records = parse_odl(version, buffer, path.name, decryptor=None)

    assert len(records) == 1
    rec = records[0]

    assert rec.index == 1
    assert rec.filename == path.name
    assert rec.timestamp > 0


def test_v2_payload_fields(data_dir):
    path = data_dir / "minimal_v2.odl"
    version, buffer = load_odl_file(path)
    records = parse_odl(version, buffer, path.name, decryptor=None)
    rec = records[0]

    # These come from the synthetic payload
    assert rec.code_file == "test"
    assert rec.function == "func"
    assert rec.params == "abcd"


def test_parse_minimal_v2(data_dir):
    path = data_dir / "minimal_v2.odl"

    # Step 1: load header + skip to first CDEF block
    version, buffer = load_odl_file(path)
    assert version == 2

    # Step 2: parse the CDEF blocks
    records = parse_odl(version, buffer, path.name, decryptor=None)
    assert isinstance(records, list)
    assert len(records) >= 1

    rec = records[0]

    # Step 3: validate record fields
    assert rec.filename == path.name
    assert rec.index == 1
    assert rec.timestamp > 0

    # Step 4: validate extracted strings
    # Our synthetic v2 payload contains:
    #   code_file = "test"
    #   function  = "func"
    #   params    = "abcd"
    assert rec.code_file == "test"
    assert rec.function == "func"
    assert rec.params == "abcd"


def test_v2_multiple_blocks(tmp_path, data_dir):
    """Ensure parser handles multiple consecutive CDEF_V2 blocks."""

    # Load the existing minimal block
    minimal = (data_dir / "minimal_v2.odl").read_bytes()

    # Duplicate the CDEF block portion (skip the 0x100 header)
    header = minimal[:0x100]
    block = minimal[0x100:]

    combined = header + block + block  # two blocks

    path = tmp_path / "multi_v2.odl"
    path.write_bytes(combined)

    version, buffer = load_odl_file(path)
    records = parse_odl(version, buffer, path.name, decryptor=None)

    assert len(records) == 2
    assert records[0].code_file == "test"
    assert records[1].function == "func"


def test_v2_bad_signature(tmp_path, data_dir):
    """Parser should skip or error on invalid CDEF signature."""

    minimal = (data_dir / "minimal_v2.odl").read_bytes()
    header = minimal[:0x100]
    block = bytearray(minimal[0x100:])

    block[0:4] = b"BAD!"  # corrupt signature

    path = tmp_path / "bad_v2.odl"
    path.write_bytes(header + block)

    version, buffer = load_odl_file(path)
    records = parse_odl(version, buffer, path.name, decryptor=None)

    assert records == []  # no valid blocks


def test_v2_truncated_header(tmp_path, data_dir):
    minimal = (data_dir / "minimal_v2.odl").read_bytes()
    truncated = minimal[: 0x100 + 10]  # cut inside CDEF header

    path = tmp_path / "trunc_v2.odl"
    path.write_bytes(truncated)

    version, buffer = load_odl_file(path)
    records = parse_odl(version, buffer, path.name, decryptor=None)

    assert records == []
