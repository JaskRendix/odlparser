import gzip

from odlparser.parser import parse_odl
from odlparser.reader import OdlReadError, load_odl_file


def test_v2_gzip_wrapped(tmp_path, data_dir):
    raw = (data_dir / "minimal_v2.odl").read_bytes()

    gz_path = tmp_path / "v2.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(raw)

    odl_file = load_odl_file(gz_path)
    records = parse_odl(odl_file.version, odl_file.data, gz_path.name, decryptor=None)

    assert len(records) == 1


def test_v3_gzip_wrapped(tmp_path, data_dir):
    raw = (data_dir / "minimal_v3.odl").read_bytes()

    gz_path = tmp_path / "v3.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(raw)

    odl_file = load_odl_file(gz_path)
    records = parse_odl(odl_file.version, odl_file.data, gz_path.name, decryptor=None)

    assert odl_file.version == 3
    assert len(records) == 1


def test_load_minimal_v2(data_dir):
    path = data_dir / "minimal_v2.odl"
    odl_file = load_odl_file(path)
    assert odl_file.version == 2
    assert isinstance(odl_file.data, bytes)


def test_load_missing_file():
    try:
        load_odl_file("does_not_exist.odl")
    except OdlReadError:
        assert True
