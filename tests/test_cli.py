import sqlite3
import subprocess


def run_cli(args):
    """Helper to run the CLI and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["odlparse"] + args,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_runs(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()
    (folder / "minimal_v2.odl").write_bytes((data_dir / "minimal_v2.odl").read_bytes())

    code, out, _ = run_cli([str(folder)])

    assert code == 0
    assert "Processing minimal_v2.odl" in out
    assert "Done. Output written to:" in out


def test_cli_missing_folder(tmp_path):
    code, out, _ = run_cli([str(tmp_path / "does_not_exist")])
    assert code == 0
    assert "ERROR: Folder does not exist" in out


def test_cli_sqlite_output(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()

    src = data_dir / "minimal_v2.odl"
    dst = folder / "minimal_v2.odl"
    dst.write_bytes(src.read_bytes())

    sqlite_path = tmp_path / "out.db"

    code, out, _ = run_cli([str(folder), "--sqlite", str(sqlite_path)])

    assert code == 0
    assert sqlite_path.exists()
    assert "SQLite output written to:" in out

    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM records")
    count = cur.fetchone()[0]
    assert count >= 1

    cur.execute("SELECT filename, index_num, code_file, function FROM records LIMIT 1")
    row = cur.fetchone()
    assert row is not None

    conn.close()


def test_cli_sqlite_indexes(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()
    (folder / "minimal_v2.odl").write_bytes((data_dir / "minimal_v2.odl").read_bytes())

    sqlite_path = tmp_path / "out.db"

    code, _, _ = run_cli([str(folder), "--sqlite", str(sqlite_path)])
    assert code == 0

    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

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

    code, _, _ = run_cli(
        [str(folder), "-o", str(csv_path), "--sqlite", str(sqlite_path)]
    )

    assert code == 0
    assert csv_path.exists()
    assert sqlite_path.exists()

    lines = csv_path.read_text().splitlines()
    assert len(lines) >= 2
    assert "filename,index,timestamp,code_file,function,params" in lines[0]


def test_cli_sqlite_only_mode_creates_default_csv(tmp_path, data_dir):
    folder = tmp_path / "odl"
    folder.mkdir()
    (folder / "minimal_v2.odl").write_bytes((data_dir / "minimal_v2.odl").read_bytes())

    sqlite_path = tmp_path / "only.db"

    code, _, _ = run_cli([str(folder), "--sqlite", str(sqlite_path)])
    assert code == 0
    assert sqlite_path.exists()

    default_csv = folder / "ODL_Report.csv"
    assert default_csv.exists()


def test_cli_invalid_odl_file(tmp_path):
    folder = tmp_path / "odl"
    folder.mkdir()

    # Write garbage
    (folder / "broken.odl").write_text("not a real odl file")

    code, out, _ = run_cli([str(folder)])
    assert code == 0
    assert "ERROR:" in out
