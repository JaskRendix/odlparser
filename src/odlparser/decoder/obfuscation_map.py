"""
Obfuscation map loader for OneDrive ODL logs.

Older OneDrive versions store unobfuscation mappings in a tab-delimited
text file named `ObfuscationStringMap.txt`. Each line contains:

    KEY<TAB>VALUE

Some keys appear multiple times (older and newer values). By default,
only the *newest* value is used. If `include_all=True`, all values are
joined with "|" in the order they appear.

This module provides:
- Encoding detection (UTF-8 vs UTF-16LE)
- Robust parsing of the map file
- Optional handling of repeated keys
- A clean, testable API
"""

from __future__ import annotations

from pathlib import Path

from .keystore import guess_encoding


class ObfuscationMapError(Exception):
    """Raised when the obfuscation map cannot be parsed."""


def load_obfuscation_map(path: str | Path, include_all: bool = False) -> dict[str, str]:
    """
    Load and parse an ObfuscationStringMap.txt file.

    Args:
        path: Path to the map file.
        include_all: If True, repeated keys accumulate values separated by "|".
                     If False, only the newest value is kept.

    Returns:
        A dictionary mapping obfuscated tokens → unobfuscated strings.

    Raises:
        ObfuscationMapError: If the file cannot be read or parsed.
    """
    path = Path(path)

    if not path.exists():
        raise ObfuscationMapError(f"Obfuscation map not found: {path}")

    encoding = guess_encoding(path)
    mapping: dict[str, str] = {}
    repeated_found = False

    try:
        with path.open("r", encoding=encoding) as f:
            last_key = None
            last_val = None

            for raw_line in f:
                line = raw_line.rstrip("\n")
                parts = line.split("\t")

                # Case 1: KEY<TAB>VALUE
                if len(parts) == 2:
                    key, value = parts

                    if key in mapping:
                        repeated_found = True

                        if include_all:
                            # Append new value
                            mapping[key] = f"{mapping[key]}|{value}"
                        else:
                            # Skip older values
                            continue

                        last_key = key
                        last_val = mapping[key]
                    else:
                        mapping[key] = value
                        last_key = key
                        last_val = value

                # Case 2: Continuation of previous value (multi-line)
                else:
                    if last_key is None:
                        # Malformed file — ignore silently
                        continue

                    if not include_all and last_key in mapping:
                        # Skip continuation for older entries
                        continue

                    last_val = f"{last_val}\n{line}"
                    mapping[last_key] = last_val

    except Exception as ex:
        raise ObfuscationMapError(f"Failed to parse obfuscation map: {ex}") from ex

    if repeated_found and not include_all:
        print("WARNING: Repeated keys found in obfuscation map (older values ignored).")

    return mapping
