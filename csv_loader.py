"""Reading CSV files into flight records and error messages."""
import csv
import os

from validator import to_record, validate_row


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """
    records = []
    errors = []
    seen = set()  # (flight_id, departure_datetime) of the valid rows already kept

    for path in paths:
        file_name = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                text = line.strip()
                # line 1 is the header; blank and comment lines are skipped silently
                if line_number == 1 or text == "" or text.startswith("#"):
                    continue

                fields = next(csv.reader([line]))
                error_code = validate_row(fields, airports)

                if error_code is None:
                    record = to_record(fields)
                    key = (record["flight_id"], record["departure_datetime"])
                    if key in seen:
                        error_code = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(key)
                        records.append(record)

                if error_code is not None:
                    errors.append(f"{file_name}:{line_number}: {error_code} | {text}")

    return records, errors
