import gzip

from odlparser.parser import parse_odl
from odlparser.reader import OdlReadError, load_odl_file


def test_v2_gzip_wrapped(tmp_path, data_dir):
    raw = (data_dir / "minimal_v2.odl").read_bytes()

    gz_path = tmp_path / "v2.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(raw)

    version, buffer = load_odl_file(gz_path)
    records = parse_odl(version, buffer, gz_path.name, decryptor=None)

    assert len(records) == 1


def test_v3_gzip_wrapped(tmp_path, data_dir):
    raw = (data_dir / "minimal_v3.odl").read_bytes()

    gz_path = tmp_path / "v3.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(raw)

    version, buffer = load_odl_file(gz_path)
    records = parse_odl(version, buffer, gz_path.name, decryptor=None)

    assert version == 3
    assert len(records) == 1


def test_load_minimal_v2(data_dir):
    path = data_dir / "minimal_v2.odl"
    version, raw = load_odl_file(path)
    assert version == 2
    assert isinstance(raw, bytes)


def test_load_missing_file():
    try:
        load_odl_file("does_not_exist.odl")
    except OdlReadError:
        assert True
