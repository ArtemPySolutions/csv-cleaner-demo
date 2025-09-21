"""
CSV Cleaner Demo - Command-line CSV cleaning tool.

Features:
- Read a CSV file using pandas
- Trim leading/trailing spaces in all string cells
- Handle empty cells by either marking them with "__EMPTY__" or deleting rows with any empties
- Deduplicate rows based on all columns or a subset
- Write cleaned CSV and a processing report

Usage examples (PowerShell):
  python main.py --input data\messy.csv --output data\clean.csv --dedupe-on all --empty-policy mark --report reports\run.txt
  python main.py --input data\messy.csv --output data\clean.csv --dedupe-on id,email --empty-policy delete-row --sep ";" --report reports\run.txt
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd


MARKER_EMPTY = "__EMPTY__"


@dataclass
class RunStats:
    total_input_rows: int = 0
    total_output_rows: int = 0
    duplicates_removed: int = 0
    empty_cells_found: int = 0
    rows_dropped_due_to_empty: int = 0
    runtime_seconds: float = 0.0


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="csv-cleaner-demo",
        description="Read a CSV, clean it, write cleaned CSV and a report.",
    )
    parser.add_argument("--input", required=True, help="Path to input CSV (e.g., data/messy.csv)")
    parser.add_argument("--output", required=True, help="Path to cleaned CSV to write")
    parser.add_argument(
        "--dedupe-on",
        required=True,
        help='Either "all" to deduplicate full rows or a comma-separated list of columns (e.g., id,email)',
    )
    parser.add_argument(
        "--empty-policy",
        required=True,
        choices=["delete-row", "mark"],
        help='How to handle empty cells: "delete-row" removes any row that has an empty cell; "mark" replaces empties with "__EMPTY__"',
    )
    parser.add_argument("--sep", default=",", help='CSV separator (default ",")')
    parser.add_argument(
        "--report",
        required=True,
        help="Path to report file to write (e.g., reports/run_YYYYMMDD_HHMM.txt)",
    )

    return parser.parse_args(argv)


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_csv(path: Path, sep: str) -> Tuple[pd.DataFrame, int]:
    """Load CSV as all strings; handle empty files gracefully.

    Returns DataFrame and total input rows (excluding header).
    """
    try:
        df = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=True)
        return df, len(df)
    except FileNotFoundError:
        raise
    except pd.errors.EmptyDataError:
        # Completely empty file (no header, no rows)
        return pd.DataFrame(), 0


def _trim_strings(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.applymap(lambda x: x.strip() if isinstance(x, str) else x)


def _handle_empty_cells(df: pd.DataFrame, policy: str) -> Tuple[pd.DataFrame, int, int]:
    """Normalize empty strings to NA, count empties, then apply policy.

    Returns (df_after, empty_cells_found, rows_dropped_due_to_empty)
    """
    if df.empty:
        return df, 0, 0

    # Normalize purely empty strings to NA to count empties reliably
    df = df.replace("", pd.NA)

    empty_cells_found = int(df.isna().sum().sum())

    rows_dropped = 0
    if policy == "delete-row":
        if len(df.columns) == 0:
            # No columns -> dropping rows doesn't make sense; nothing to drop
            return df, empty_cells_found, 0
        rows_with_empty = df.isna().any(axis=1)
        rows_dropped = int(rows_with_empty.sum())
        df = df.loc[~rows_with_empty].copy()
    elif policy == "mark":
        df = df.fillna(MARKER_EMPTY)
    else:
        raise ValueError(f"Unknown empty policy: {policy}")

    return df, empty_cells_found, rows_dropped


def _deduplicate(df: pd.DataFrame, dedupe_on: str) -> Tuple[pd.DataFrame, int, List[str]]:
    """Deduplicate DataFrame rows according to parameter.

    Returns (df_after, duplicates_removed, used_columns)
    """
    if df.empty:
        return df, 0, []

    before = len(df)
    used_cols: List[str] = []

    if dedupe_on.strip().lower() == "all":
        df2 = df.drop_duplicates(keep="first")
        return df2, before - len(df2), []

    # Parse subset list
    requested_cols = [c.strip() for c in dedupe_on.split(",") if c.strip()]
    existing_cols = [c for c in requested_cols if c in df.columns]

    if not existing_cols:
        # Nothing to dedupe on; return unchanged
        return df, 0, []

    df2 = df.drop_duplicates(subset=existing_cols, keep="first")
    return df2, before - len(df2), existing_cols


def _write_csv(df: pd.DataFrame, path: Path, sep: str) -> None:
    _ensure_parent_dir(path)
    # Ensure consistent writing of empty DataFrames
    df.to_csv(path, sep=sep, index=False)


def _write_report(path: Path, stats: RunStats, params: dict, notes: List[str]) -> None:
    _ensure_parent_dir(path)
    lines = []
    lines.append("CSV Cleaner Report")
    lines.append("=" * 72)
    lines.append("")
    lines.append("Parameters:")
    for k, v in params.items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("Results:")
    lines.append(f"  Total input rows: {stats.total_input_rows}")
    lines.append(f"  Total output rows: {stats.total_output_rows}")
    lines.append(f"  Duplicates removed: {stats.duplicates_removed}")
    lines.append(f"  Empty cells found: {stats.empty_cells_found}")
    lines.append(f"  Rows dropped due to empty: {stats.rows_dropped_due_to_empty}")
    lines.append(f"  Runtime (s): {stats.runtime_seconds:.3f}")
    if notes:
        lines.append("")
        lines.append("Notes:")
        for n in notes:
            lines.append(f"  - {n}")
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    try:
        args = _parse_args(argv)
    except SystemExit:
        # argparse already printed the error/help
        return 2

    input_path = Path(args.input)
    output_path = Path(args.output)
    report_path = Path(args.report)

    notes: List[str] = []

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    start = time.perf_counter()
    stats = RunStats()

    try:
        df, stats.total_input_rows = _load_csv(input_path, args.sep)

        # Trim whitespace
        df = _trim_strings(df)

        # Handle empties
        df, stats.empty_cells_found, stats.rows_dropped_due_to_empty = _handle_empty_cells(df, args["empty_policy"] if isinstance(args, dict) else args.empty_policy)

        # Deduplicate
        df, stats.duplicates_removed, used_cols = _deduplicate(df, args["dedupe_on"] if isinstance(args, dict) else args.dedupe_on)
        if used_cols:
            notes.append(f"Deduplication used columns: {', '.join(used_cols)}")
        elif (args["dedupe_on"] if isinstance(args, dict) else args.dedupe_on).strip().lower() != "all":
            requested = [c.strip() for c in (args["dedupe_on"] if isinstance(args, dict) else args.dedupe_on).split(",") if c.strip()]
            missing = [c for c in requested if df.columns.tolist() and c not in df.columns]
            if missing:
                notes.append(f"Requested dedupe columns not found and were ignored: {', '.join(missing)}")

        stats.total_output_rows = len(df)

        # Write outputs
        _write_csv(df, output_path, args.sep)

        params = {
            "input": str(input_path),
            "output": str(output_path),
            "dedupe_on": args.dedupe_on,
            "empty_policy": args.empty_policy,
            "sep": args.sep,
            "report": str(report_path),
        }

        stats.runtime_seconds = time.perf_counter() - start
        _write_report(report_path, stats, params, notes)

        return 0
    except Exception as e:
        # Catch-all to prevent crashes; still non-zero exit
        try:
            params = {
                "input": str(input_path),
                "output": str(output_path),
                "dedupe_on": args.dedupe_on,
                "empty_policy": args.empty_policy,
                "sep": args.sep,
                "report": str(report_path),
            }
            stats.runtime_seconds = time.perf_counter() - start
            _write_report(report_path, stats, params, notes + [f"Error: {e}"])
        except Exception:
            pass
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
