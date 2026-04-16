import sqlite3
import subprocess


def test_cli_runs(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()
    (folder / "minimal_v2.odl").write_bytes((data_dir / "minimal_v2.odl").read_bytes())

    result = subprocess.run(["odlparse", str(folder)], capture_output=True, text=True)

    assert result.returncode == 0
    assert "Processing minimal_v2.odl" in result.stdout


def test_cli_sqlite_output(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()

    src = data_dir / "minimal_v2.odl"
    dst = folder / "minimal_v2.odl"
    dst.write_bytes(src.read_bytes())

    sqlite_path = tmp_path / "out.db"

    result = subprocess.run(
        ["odlparse", str(folder), "--sqlite", str(sqlite_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Processing minimal_v2.odl" in result.stdout
    assert sqlite_path.exists()

    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records'")
    assert cur.fetchone() is not None

    cur.execute("SELECT COUNT(*) FROM records")
    count = cur.fetchone()[0]
    assert count >= 1

    cur.execute("SELECT filename, index_num, code_file, function FROM records LIMIT 1")
    row = cur.fetchone()
    assert row is not None

    filename, index_num, code_file, function = row

    assert filename == "minimal_v2.odl"
    assert isinstance(index_num, int)
    assert isinstance(code_file, str)
    assert isinstance(function, str)

    conn.close()


def test_cli_sqlite_indexes(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()

    (folder / "minimal_v2.odl").write_bytes((data_dir / "minimal_v2.odl").read_bytes())

    sqlite_path = tmp_path / "out.db"

    result = subprocess.run(
        ["odlparse", str(folder), "--sqlite", str(sqlite_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert sqlite_path.exists()

    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records'")
    assert cur.fetchone() is not None

    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    index_names = {row[0] for row in cur.fetchall()}

    assert "idx_timestamp" in index_names
    assert "idx_function" in index_names
    assert "idx_code_file" in index_names

    conn.close()


def test_cli_csv_and_sqlite(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()

    (folder / "minimal_v2.odl").write_bytes((data_dir / "minimal_v2.odl").read_bytes())

    csv_path = tmp_path / "out.csv"
    sqlite_path = tmp_path / "out.db"

    result = subprocess.run(
        ["odlparse", str(folder), "-o", str(csv_path), "--sqlite", str(sqlite_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert csv_path.exists()
    assert sqlite_path.exists()

    lines = csv_path.read_text().splitlines()
    assert len(lines) >= 2
    assert "filename,index,timestamp,code_file,function,params" in lines[0]


def test_cli_sqlite_only_mode(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()

    (folder / "minimal_v2.odl").write_bytes((data_dir / "minimal_v2.odl").read_bytes())

    sqlite_path = tmp_path / "only.db"

    result = subprocess.run(
        ["odlparse", str(folder), "--sqlite", str(sqlite_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert sqlite_path.exists()

    default_csv = folder / "ODL_Report.csv"
    assert default_csv.exists()
