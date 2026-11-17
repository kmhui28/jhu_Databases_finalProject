"""
Convert the F1 CSVs into one-row-per-statement INSERTs (f1_inserts.sql), e.g.

    insert into drivers values ( 1, 'hamilton', 44, 'HAM', 'Lewis', 'Hamilton', '1985-01-07', 'British', 'http://...' );

Usage:
    1. Put this script next to a "data" folder containing the CSVs.
    2. python csv_to_inserts.py
    3. In MySQL: USE f1;  then run f1_inserts.sql

IMPORTANT: these statements have no column list, so the values must be in the
same order as the columns in your CREATE TABLE. The CSV column order matches
f1_schema.sql, as long as extra CSV columns are listed in SKIP_COLUMNS below.
"""
import csv
import os
import re

DATA_DIR = "data"
OUT_FILE = "f1_insertStatements.sql"

# Parents first, children after (so foreign keys never fail)
ORDER = [
    "seasons", "circuits", "constructors", "drivers", "status",
    "races",
    "results", "sprint_results", "qualifying", "lap_times", "pit_stops",
    "driver_standings", "constructor_standings", "constructor_results",
]

# lap_times is ~500k rows (one statement each = slow). Cap it; None = keep all.
MAX_ROWS = {"lap_times": 5000}

# CSV columns that are NOT in your CREATE TABLE. They are dropped so the
# remaining values line up with the table's columns.
SKIP_COLUMNS = {
    "races": {"fp1_date", "fp1_time", "fp2_date", "fp2_time", "fp3_date",
              "fp3_time", "quali_date", "quali_time", "sprint_date", "sprint_time"},
}

# Plain numbers (no leading zeros) are written unquoted, everything else quoted
NUMBER = re.compile(r"^-?(0|[1-9]\d*)(\.\d+)?$")


def sql_value(v):
    if v == "\\N" or v == "":
        return "NULL"
    if NUMBER.match(v):
        return v
    v = v.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{v}'"


with open(OUT_FILE, "w", encoding="utf-8") as out:
    out.write("SET FOREIGN_KEY_CHECKS = 0;\nSET autocommit = 0;\n\n")
    for table in ORDER:
        fname = f"data/{table}.csv"

        with open(fname, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            skip = SKIP_COLUMNS.get(table, set())
            keep = [i for i, h in enumerate(header) if h not in skip]

            limit = MAX_ROWS.get(table)
            count = 0
            out.write(f"-- {table}\n")
            for row in reader:
                if limit is not None and count >= limit:
                    break
                vals = ", ".join(sql_value(row[i]) for i in keep)
                out.write(f"insert into {table} values ( {vals} );\n")
                count += 1
            out.write("COMMIT;\n\n")
            print(f"{table}: {count} rows")

    out.write("SET FOREIGN_KEY_CHECKS = 1;\n")

print(f"Done -> {OUT_FILE}")