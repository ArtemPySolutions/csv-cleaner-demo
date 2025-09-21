# CSV Cleaner Demo

A small, self-contained demo project that reads a CSV file, cleans it with a few configurable rules, and writes a cleaned CSV plus a human-readable report.

Features
- Trim leading/trailing spaces from all string cells
- Handle empty cells with a policy: mark them with `__EMPTY__` or delete rows that contain empties
- Deduplicate rows on all columns or a subset of columns
- Robust on empty files and “header-only” files
- Text report with row counts, duplicates removed, empty statistics, runtime, and parameters used

Requirements
- Python 3.10+
- Install dependencies:
  - Windows PowerShell:
    ```powershell
    py -m pip install -r requirements.txt
    ```
  - macOS/Linux:
    ```bash
    python3 -m pip install -r requirements.txt
    ```

Usage
Run from the project root:

- Basic (dedupe full rows, mark empties):
  ```powershell
  python main.py --input data\messy.csv --output data\clean.csv --dedupe-on all --empty-policy mark --report reports\run_001.txt
  ```

- Deduplicate on specific columns and use a custom separator:
  ```powershell
  python main.py --input data\messy.csv --output data\clean.csv --dedupe-on id,email --empty-policy delete-row --sep ";" --report reports\run_002.txt
  ```

Arguments
- --input          Path to input CSV (e.g., data\messy.csv)
- --output         Path to cleaned CSV to write
- --dedupe-on      Either `all` or a comma-separated list of columns (e.g., `id,email`)
- --empty-policy   `delete-row` or `mark` (mark uses `__EMPTY__`)
- --sep            Separator, default is `,`
- --report         Path to report file (e.g., reports\run_YYYYMMDD_HHMM.txt)

Sample data
- data/messy.csv is a sample input
- data/clean_expected.csv is the expected result for this command:
  ```powershell
  python main.py --input data\messy.csv --output data\clean.csv --dedupe-on id,email --empty-policy mark --sep "," --report reports\run_sample.txt
  ```
  After running it, data/clean.csv should match data/clean_expected.csv.

Report content
The report includes:
- total input rows
- total output rows
- number of duplicates removed
- number of empty cells found and rows dropped due to empties
- runtime
- parameters used
- notes (e.g., if requested dedupe columns were missing)

Project structure
```
csv-cleaner-demo/
├── data/
│   ├── messy.csv
│   └── clean_expected.csv
├── reports/
├── screenshots/
├── main.py
├── requirements.txt
├── README.md
└── SPEC.md
```

License
This demo project is provided for educational purposes and can be used freely.