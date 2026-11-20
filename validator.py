"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d %H:%M"


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    airports = set()
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            code = line.strip()
            if code != "" and not code.startswith("#"):
                airports.add(code)
    return airports


def parse_datetime(text: str):
    """Return a datetime if text is exactly 'YYYY-MM-DD HH:MM', else None.

    The regex enforces the strict format (zero-padded, ASCII digits);
    strptime then checks that the date and time really exist.
    """
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}", text):
        return None
    try:
        return datetime.strptime(text, DATE_FORMAT)
    except ValueError:
        return None


def is_airport_code(code: str, airports: set[str]) -> bool:
    """3 uppercase ASCII letters AND present in the airport list."""
    return re.fullmatch(r"[A-Z]{3}", code) is not None and code in airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    # 1. exactly 6 fields
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, departure, arrival, price = [f.strip() for f in fields]

    # 2. no empty field
    if "" in [flight_id, origin, destination, departure, arrival, price]:
        return "MISSING_FIELD"

    # 3. flight id: 2-8 ASCII letters or digits
    if not re.fullmatch(r"[A-Za-z0-9]{2,8}", flight_id):
        return "INVALID_FLIGHT_ID"

    # 4-6. airports
    if not is_airport_code(origin, airports):
        return "INVALID_ORIGIN"
    if not is_airport_code(destination, airports):
        return "INVALID_DESTINATION"
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # 7-9. dates
    departure_time = parse_datetime(departure)
    if departure_time is None:
        return "INVALID_DEPARTURE"
    arrival_time = parse_datetime(arrival)
    if arrival_time is None:
        return "INVALID_ARRIVAL"
    if arrival_time <= departure_time:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # 10-11. price
    try:
        price_value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(price_value):
        return "INVALID_PRICE"
    if price_value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    flight_id, origin, destination, departure, arrival, price = [f.strip() for f in fields]
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }