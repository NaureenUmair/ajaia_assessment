#!/usr/bin/env python3
import csv
from collections import Counter
from datetime import datetime, timezone
from io import StringIO

RAW_DATA = """exception_id,terminal,event_type,carrier_code,event_ts
CPX-88213,Terminal 3,missed_pickup,swft,2026-08-14 09:12:00
CPX-88214,Terminal 3,doc_mismatch,SWFT,08/14/2026 09:45
CPX-88215,T3,missed_pickup,Swft,2026-08-14T10:03:00Z
CPX-88216,Terminal 3,doc_mismatch,,2026-08-14 11:47:00
CPX-88217,Terminal 3,carrier_substitution,RLCX,08/15/2026 08:02
"""

TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%Y-%m-%dT%H:%M:%SZ",
)


def normalize_terminal(value):
    value = value.strip().upper()
    if value in {"T3", "TERMINAL 3"}:
        return "Terminal 3"
    if value.startswith("T") and value[1:].isdigit():
        return f"Terminal {value[1:]}"
    return value.title()


def normalize_carrier(value):
    value = value.strip().upper()
    return value if value else None


def normalize_timestamp(value):
    value = value.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            if value.endswith("Z"):
                dt = dt.replace(tzinfo=timezone.utc)
            # Do not invent a timezone for timestamps that did not provide one.
            return dt.isoformat(), True
        except ValueError:
            pass
    return value, False


def normalize_rows(raw_text):
    reader = csv.DictReader(StringIO(raw_text))
    rows = []
    warnings = []

    for row in reader:
        clean_terminal = normalize_terminal(row["terminal"])
        clean_carrier = normalize_carrier(row["carrier_code"])
        clean_timestamp, timestamp_ok = normalize_timestamp(row["event_ts"])

        if clean_carrier is None:
            warnings.append(
                f'{row["exception_id"]}: carrier_code is missing; '
                'left blank rather than guessing.'
            )

        if not timestamp_ok:
            warnings.append(
                f'{row["exception_id"]}: timestamp could not be parsed '
                f'confidently; left as "{row["event_ts"]}".'
            )

        rows.append({
            "exception_id": row["exception_id"].strip(),
            "terminal": clean_terminal,
            "event_type": row["event_type"].strip().lower(),
            "carrier_code": clean_carrier or "",
            "event_ts": clean_timestamp,
        })

    return rows, warnings


def main():
    rows, warnings = normalize_rows(RAW_DATA)
    counts = Counter(row["event_type"] for row in rows)

    print("NORMALIZED RECORDS")
    print("-" * 72)
    for row in rows:
        print(row)

    print("\nEXCEPTION COUNT BY EVENT TYPE")
    print("-" * 40)
    for event_type in sorted(counts):
        print(f"{event_type}: {counts[event_type]}")

    print("\nDATA QUALITY NOTES")
    print("-" * 40)
    if warnings:
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- No unresolved data-quality issues.")

    # Validation proves the output is correct for the supplied test data.
    assert len(rows) == 5
    assert counts == {
        "missed_pickup": 2,
        "doc_mismatch": 2,
        "carrier_substitution": 1,
    }
    assert rows[2]["terminal"] == "Terminal 3"
    assert rows[2]["carrier_code"] == "SWFT"
    assert rows[3]["carrier_code"] == ""
    assert rows[1]["event_ts"] == "2026-08-14T09:45:00"

    print("\nVALIDATION")
    print("-" * 40)
    print("PASS: 5 records processed.")
    print("PASS: event-type counts match expected values.")
    print("PASS: terminal/carrier normalization checks passed.")
    print("PASS: timestamp parsing checks passed.")
    print("PASS: missing carrier was not guessed.")


if __name__ == "__main__":
    main()
