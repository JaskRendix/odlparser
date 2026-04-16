# **odlparser — Modern, Modular OneDrive ODL Log Parser**

A clean, typed, fully modular parser for **Microsoft OneDrive ODL sync‑engine logs**.

This project is a modern re‑architecture of the original forensic parser by **Yogesh Khatri (@swiftforensics)**.  
It preserves the decoding logic (obfuscation map, AES keystore, CDEF parsing) while providing a maintainable, testable, production‑ready codebase.

---

## **Features**

- Parses **ODL v2** and **ODL v3** log formats  
- Supports all OneDrive log extensions:  
  `.odl`, `.odlgz`, `.odlsent`, `.aodl`
- Automatic detection of:
  - Legacy **ObfuscationStringMap.txt**
  - Modern **general.keystore** (AES‑CBC)
  - Gzip‑wrapped logs
- Clean separation of concerns:
  - **reader** → file I/O + decompression  
  - **parser** → CDEF block parsing  
  - **decoder** → unobfuscation + AES decryption  
  - **models** → typed immutable records  
  - **cli** → orchestration + CSV and SQLite output
- Fully typed (`mypy`‑friendly)
- 100% pytest coverage for all components
- Suitable for DFIR pipelines, automation, and large‑scale log ingestion

---

## **Installation**

```bash
pip install odlparser
```

Or from source:

```bash
git clone https://github.com/<your-repo>/odlparser
cd odlparser
pip install -e .
```

---

## **Command‑Line Usage**

```bash
odlparse <folder> [-o OUTPUT] [-s MAP] [-k] [--sqlite DB]
```

### **Arguments**

| Option | Description |
|--------|-------------|
| `folder` | Folder containing `.odl`, `.odlgz`, `.odlsent`, `.aodl` files |
| `-o, --output` | Output CSV path (default: `ODL_Report.csv` in folder) |
| `-s, --map` | Path to `ObfuscationStringMap.txt` |
| `-k, --all-keys` | Include all repeated map values |
| `--sqlite DB` | Write results to a SQLite database (in addition to CSV) |

### **Examples**

CSV only:

```bash
odlparse ~/OneDriveLogs -o ~/Desktop/odl.csv
```

SQLite only (CSV still produced by default):

```bash
odlparse ~/OneDriveLogs --sqlite ~/Desktop/odl.db
```

CSV + SQLite:

```bash
odlparse ~/OneDriveLogs -o report.csv --sqlite report.db
```

---

## **Programmatic Usage**

```python
from pathlib import Path
from odlparser.reader import load_odl_file
from odlparser.parser import parse_odl
from odlparser.decoder.unobfuscate import OdlDecryptor

version, raw = load_odl_file(Path("SyncEngine-2024-01-01.1234.odlgz"))
decryptor = OdlDecryptor(keystore=None, mapping={})

records = parse_odl(version, raw, filename="log.odl", decryptor=decryptor)

for r in records:
    print(r.timestamp, r.code_file, r.function, r.params)
```

---

## **How OneDrive ODL Logs Work**

OneDrive sync‑engine logs are stored as binary files with extensions:

> `.odl`, `.odlgz`, `.odlsent`, `.aold`

They contain sequences of **CDEF blocks**, each representing a function call inside the OneDrive sync engine.

### **String decoding**

Two mechanisms exist:

#### **1. Legacy (pre‑2022)**  
Strings are obfuscated using a key/value map stored in:

> `ObfuscationStringMap.txt`

#### **2. Modern (post‑2022)**  
Strings are AES‑CBC encrypted using a key stored in:

> `general.keystore`

The parser automatically detects and uses whichever mechanism is present.

---

## **Project Structure**

```
src/odlparser/
    cli.py               # CLI entrypoint
    reader.py            # File I/O + decompression
    parser.py            # CDEF v2/v3 parsing
    models.py            # Typed immutable OdlRecord
    structures.py        # Construct definitions
    decoder/
        keystore.py
        obfuscation_map.py
        string_extract.py
        unobfuscate.py
tests/
    test_*.py            # Full pytest suite
```

---

## **Output Format**

The CLI produces:

### **CSV**
- `filename`
- `index`
- `timestamp`
- `code_file`
- `function`
- `params`

### **SQLite**
A single table named `records` with columns:

- `filename`
- `index_num`
- `timestamp`
- `code_file`
- `function`
- `params`

Example CSV row:

```
SyncEngine-2024-01-01.1234.odlgz,42,2024-01-01T12:34:56,SyncEngine.cpp,UploadItem,"/Documents/report.docx"
```

---

## **Attribution**

This project is a modular rewrite inspired by the original OneDrive ODL parser by:

**Yogesh Khatri (@swiftforensics)**  
[https://github.com/ydkhatri/OneDrive](https://github.com/ydkhatri/OneDrive)

All decoding logic (CDEF structures, unobfuscation, AES handling) is based on analysis of the original implementation.
