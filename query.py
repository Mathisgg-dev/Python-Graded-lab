"""Running queries against the flight database."""
from validator import parse_datetime

RECORD_KEYS = ["flight_id", "origin", "destination",
               "departure_datetime", "arrival_datetime", "price"]


def is_number(value) -> bool:
    """int or float, but not bool (True is an int in Python)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_valid_query(query) -> bool:
    """Check keys, value types and the sort_by / order / limit rules."""
    if not isinstance(query, dict):
        return False

    for key, value in query.items():
        if key in ["flight_id", "origin", "destination"]:
            if not isinstance(value, str):
                return False
        elif key in ["departure_datetime", "arrival_datetime"]:
            if not isinstance(value, str) or parse_datetime(value) is None:
                return False
        elif key in ["price", "min_price"]:
            if not is_number(value):
                return False
        elif key == "sort_by":
            if value not in RECORD_KEYS:
                return False
        elif key == "order":
            if value not in ["asc", "desc"] or "sort_by" not in query:
                return False
        elif key == "limit":
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                return False
        else:  # unknown key
            return False
    return True


def flight_matches(flight: dict, query: dict) -> bool:
    """True if the flight passes every condition of the query (AND).

    Datetimes are 'YYYY-MM-DD HH:MM' strings, so comparing the strings
    is the same as comparing the dates.
    """
    for key in ["flight_id", "origin", "destination"]:
        if key in query and flight[key] != query[key]:
            return False
    if "departure_datetime" in query and flight["departure_datetime"] < query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and flight["arrival_datetime"] > query["arrival_datetime"]:
        return False
    if "price" in query and flight["price"] > query["price"]:
        return False
    if "min_price" in query and flight["price"] < query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [flight for flight in db if flight_matches(flight, query)]

    if "sort_by" in query:
        descending = query.get("order", "asc") == "desc"
        # sorted() is stable: equal values keep database order, also with reverse=True
        matches = sorted(matches, key=lambda flight: flight[query["sort_by"]], reverse=descending)

    if "limit" in query:
        matches = matches[:query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if isinstance(queries, dict):
        queries = [queries]
    return [run_query(db, query) for query in queries]