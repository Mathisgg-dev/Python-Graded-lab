"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports


STUDENT_ID = "260ADB198"
FIRST_NAME = "Mathis"
LAST_NAME = "GuillinGoutte"


def get_arguments(argv):
    """Read the command line. argparse exits with code 2 on a usage error."""
    parser = argparse.ArgumentParser(
        description="Validate flight CSV files, store the valid flights as JSON and run queries.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file of a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="output JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with the queries to run")
    parser.add_argument("-r", metavar="FOLDER", default=".",
                        help="folder for the response file (default: current folder)")
    args = parser.parse_args(argv)

    if args.j is None and args.a is None:
        parser.error("-a is required with -i and -d")
    if args.j is not None and args.o is not None:
        parser.error("-o cannot be used with -j")
    return args


def read_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def load_database(path):
    """Load a JSON database: it must be an array of objects."""
    database = read_json(path)
    if not isinstance(database, list) or not all(isinstance(item, dict) for item in database):
        raise ValueError(f"{path}: the database must be a JSON array of objects")
    return database


def load_queries(path):
    """Load a query file: one object, or an array of objects."""
    queries = read_json(path)
    if isinstance(queries, dict):
        return queries
    if isinstance(queries, list) and all(isinstance(item, dict) for item in queries):
        return queries
    raise ValueError(f"{path}: the queries must be one JSON object or an array of objects")


def find_csv_files(folder):
    """Paths of the .csv files directly in the folder, in sorted name order."""
    names = sorted(os.listdir(folder))
    paths = [os.path.join(folder, name) for name in names
             if name.endswith(".csv") and os.path.isfile(os.path.join(folder, name))]
    if not paths:
        raise ValueError(f"no .csv files found in {folder}")
    return paths


def start_log(logger, log_path):
    """Attach a file handler writing to log_path; return it so it can be removed."""
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    return handler


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    try:
        args = get_arguments(argv)
    except SystemExit as error:  # argparse: usage error (2) or -h (0)
        return error.code

    logger = logging.getLogger("flight_parser")
    handler = None
    try:
        if args.j is not None:
            database = load_database(args.j)
        else:
            airports = load_airports(args.a)
            if args.i is not None:
                paths = [args.i]
            else:
                paths = find_csv_files(args.d)

            db_path = args.o if args.o is not None else "db.json"
            log_path = os.path.join(os.path.dirname(db_path), "errors.log")
            handler = start_log(logger, log_path)

            database, errors = parse_files(paths, airports)
            for message in errors:
                logger.warning(message)
            logger.info(f"{len(database)} valid rows, {len(errors)} invalid rows")
            write_json(db_path, database)
            print(f"{len(database)} valid flights, {len(errors)} invalid rows")

        if args.q is not None:
            queries = load_queries(args.q)
            response = run_queries(database, queries)
            stamp = datetime.now().strftime("%Y%m%d_%H%M")
            file_name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
            write_json(os.path.join(args.r, file_name), response)

        return 0
    except (OSError, ValueError) as error:  # missing file, bad JSON, bad shape...
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())