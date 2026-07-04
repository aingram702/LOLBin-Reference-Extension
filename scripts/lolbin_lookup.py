#!/usr/bin/env python3
"""
LOLBin Reference Tool - CLI Lookup
Standalone Python script for terminal-based lookup during engagements.
Uses the same JSON database as the Chrome extension.
"""

import argparse
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "extension" / "data" / "lolbin_db.json"

COLOR_CYAN = "\033[96m"
COLOR_YELLOW = "\033[93m"
COLOR_GREEN = "\033[92m"
COLOR_GRAY = "\033[90m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"


def load_db():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)
    with open(DB_PATH) as f:
        return json.load(f)


def search(db, query=None, os_filter=None, category=None):
    results = db
    if os_filter:
        results = [e for e in results if e["os"].lower() == os_filter.lower()]
    if category:
        results = [e for e in results if category.lower() in e["category"].lower()]
    if query:
        q = query.lower()
        results = [
            e for e in results
            if q in e["name"].lower()
            or q in e["description"].lower()
            or q in e["id"].lower()
        ]
    return results


def print_entry(entry):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}=== {entry['name']} ({entry['os']}) ==={COLOR_RESET}")
    print(f"{COLOR_GRAY}Category:{COLOR_RESET} {entry['category']}")
    print(f"{COLOR_GRAY}Description:{COLOR_RESET} {entry['description']}")
    print(f"{COLOR_YELLOW}Example:{COLOR_RESET} {entry['example_command']}")

    for alt in entry.get("alt_commands", []):
        print(f"{COLOR_YELLOW}Alt:{COLOR_RESET}     {alt}")

    if entry.get("detection_notes"):
        print(f"{COLOR_GREEN}Detection:{COLOR_RESET} {entry['detection_notes']}")

    for ref in entry.get("references", []):
        print(f"{COLOR_GRAY}Ref: {ref}{COLOR_RESET}")


def main():
    parser = argparse.ArgumentParser(description="LOLBin Reference Tool CLI")
    parser.add_argument("--name", "-n", help="Search term (binary name, keyword)")
    parser.add_argument("--os", choices=["windows", "linux", "macos"], help="Filter by OS")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument("--list-all", action="store_true", help="List all entries")

    args = parser.parse_args()

    db = load_db()

    if args.list_all:
        results = db
    else:
        results = search(db, query=args.name, os_filter=args.os, category=args.category)

    if not results:
        print("No matching entries found.")
        sys.exit(0)

    for entry in results:
        print_entry(entry)

    print(f"\n{COLOR_GRAY}{len(results)} result(s) found.{COLOR_RESET}")


if __name__ == "__main__":
    main()
