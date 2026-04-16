"""
Command-line interface for the modern ODL parser (argparse version).

This module:
- Accepts a folder containing ODL files
- Loads obfuscation map + keystore (if present)
- Creates an OdlDecryptor
- Loads and parses each ODL file
- Writes CSV output

No parsing logic lives here — only orchestration.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from .decoder.keystore import Keystore, KeystoreError
from .decoder.obfuscation_map import ObfuscationMapError, load_obfuscation_map
from .decoder.unobfuscate import OdlDecryptor
from .models import OdlRecord
from .parser import parse_odl
from .reader import OdlReadError, load_odl_file


def _find_files(folder: Path):
    """Yield all ODL-related files in a folder."""
    patterns = ("*.odl", "*.odlgz", "*.odlsent", "*.aodl")
    for pattern in patterns:
        yield from folder.glob(pattern)


def _write_sqlite(path: Path, records: list[OdlRecord]) -> None:
    """Write parsed ODL records to a SQLite database with indexes and WAL mode."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("PRAGMA journal_mode=WAL;")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            filename TEXT,
            index_num INTEGER,
            timestamp TEXT,
            code_file TEXT,
            function TEXT,
            params TEXT
        )
        """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON records(timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_function ON records(function)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_code_file ON records(code_file)")

    rows = [
        (
            r.filename,
            r.index,
            (
                r.timestamp.isoformat()
                if hasattr(r.timestamp, "isoformat")
                else r.timestamp
            ),
            r.code_file,
            r.function,
            r.params if isinstance(r.params, str) else ",".join(r.params),
        )
        for r in records
    ]

    cur.executemany(
        """
        INSERT INTO records (filename, index_num, timestamp, code_file, function, params)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    conn.commit()
    conn.close()


def _write_csv(path: Path, records: list[OdlRecord]) -> None:
    """Write parsed ODL records to CSV."""
    fieldnames = ["filename", "index", "timestamp", "code_file", "function", "params"]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in records:
            writer.writerow(
                {
                    "filename": r.filename,
                    "index": r.index,
                    "timestamp": r.timestamp,
                    "code_file": r.code_file,
                    "function": r.function,
                    "params": r.params,
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse OneDrive ODL logs and produce a CSV report."
    )

    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing ODL files",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output CSV file path (default: ODL_Report.csv in folder)",
    )

    parser.add_argument(
        "-s",
        "--map",
        dest="map_path",
        type=Path,
        help="Path to ObfuscationStringMap.txt",
    )

    parser.add_argument(
        "-k",
        "--all-keys",
        action="store_true",
        help="Include all repeated map values",
    )

    parser.add_argument(
        "--sqlite",
        type=Path,
        help="Write results to a SQLite database instead of (or in addition to) CSV",
    )

    args = parser.parse_args()

    folder: Path = args.folder
    output: Path | None = args.output
    map_path: Path | None = args.map_path
    include_all_keys: bool = args.all_keys

    if not folder.exists() or not folder.is_dir():
        print(f"ERROR: Folder does not exist or is not a directory: {folder}")
        return

    print(f"Scanning folder: {folder}")

    mapping = {}
    if map_path is None:
        default_map = folder / "ObfuscationStringMap.txt"
        if default_map.exists():
            map_path = default_map

    if map_path:
        try:
            mapping = load_obfuscation_map(map_path, include_all=include_all_keys)
            print(f"Loaded {len(mapping)} obfuscation map entries")
        except ObfuscationMapError as ex:
            print(f"WARNING: Failed to load obfuscation map: {ex}")

    keystore = None
    ks_path = folder / "general.keystore"
    if not ks_path.exists():
        alt = folder / "EncryptionKeyStoreCopy" / "general.keystore"
        if alt.exists():
            ks_path = alt

    if ks_path.exists():
        try:
            keystore = Keystore.load(ks_path)
            print(
                f"Loaded keystore (version={keystore.version}, utf={keystore.utf_type})"
            )
        except KeystoreError as ex:
            print(f"WARNING: Failed to load keystore: {ex}")

    decryptor = OdlDecryptor(keystore=keystore, mapping=mapping)

    all_records: list[OdlRecord] = []

    for file in _find_files(folder):
        print(f"Processing {file.name}")

        try:
            version, raw_data = load_odl_file(file)
        except OdlReadError as ex:
            print(f"ERROR: {ex}")
            continue

        records = parse_odl(
            version=version,
            raw_data=raw_data,
            filename=file.name,
            decryptor=decryptor,
        )

        print(f"  → {len(records)} records")
        all_records.extend(records)

    if output is None:
        output = folder / "ODL_Report.csv"

    _write_csv(output, all_records)
    print(f"Done. Output written to: {output}")

    if args.sqlite:
        _write_sqlite(args.sqlite, all_records)
        print(f"SQLite output written to: {args.sqlite}")
