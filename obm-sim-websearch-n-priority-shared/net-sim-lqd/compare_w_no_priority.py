#!/usr/bin/env python3
"""
Outputs flows where FCT is worse with priority, as tuple lines:
(hS,hD,flowsize,starttime,finishtime,fct)

Input (same folder):
  - flows_under_100_no_priority.txt
  - flows_under_100_w_priority.txt

Output:
  - flows_worse_with_priority.txt  # sorted by starttime (ascending), then by delta desc
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NO_FILE  = HERE / "flows_under_100_no_priority.txt"
YES_FILE = HERE / "flows_under_100_w_priority.txt"

TUPLE_RE = re.compile(r"\((h\d+),(h\d+),(\d+),(\d+),(\d+),(\d+)\)")

def parse_file(path: Path):
    """
    Map (src,dst,flowsize,start) -> {'finish': avg_int, 'fct': avg_int, '_n': count}
    Averages if duplicates exist for the same key.
    """
    m = {}
    with open(path, "r") as f:
        for line in f:
            mo = TUPLE_RE.search(line)
            if not mo:
                continue
            src, dst, size, start, finish, fct = mo.groups()
            key = (src, dst, int(size), int(start))
            if key in m:
                c = m[key]["_n"] + 1
                m[key]["finish"] = (m[key]["finish"] * (c - 1) + int(finish)) / c
                m[key]["fct"]    = (m[key]["fct"]    * (c - 1) + int(fct))    / c
                m[key]["_n"] = c
            else:
                m[key] = {"finish": int(finish), "fct": int(fct), "_n": 1}
    return m

def main():
    if not NO_FILE.exists() or not YES_FILE.exists():
        sys.exit("Place this script with the two input files in the same folder.")

    no_map  = parse_file(NO_FILE)
    yes_map = parse_file(YES_FILE)

    # Intersect on (src,dst,flowsize,start)
    keys = no_map.keys() & yes_map.keys()

    # Collect flows where priority regressed (fct_yes > fct_no)
    worse = []
    for key in keys:
        fct_no  = no_map[key]["fct"]
        fct_yes = yes_map[key]["fct"]
        if fct_yes > fct_no:
            src, dst, size, start = key
            finish_yes = int(round(yes_map[key]["finish"]))
            fct_yes_i  = int(round(fct_yes))
            delta = fct_yes - fct_no
            # Store tuple + delta for sorting; we'll only write the tuple
            worse.append(((src, dst, size, start, finish_yes, fct_yes_i), delta))

    # Sort by starttime (tuple index 4th if 1-based; index 3 if 0-based), then by delta desc
    worse.sort(key=lambda x: (x[0][3], -x[1]))

    out_path = HERE / "flows_worse_with_priority.txt"
    with open(out_path, "w") as out:
        for tup, _ in worse:
            src, dst, size, start, finish, fct = tup
            out.write(f"({src},{dst},{size},{start},{finish},{fct})\n")

    print(f"Matched flows: {len(keys)}")
    print(f"Worse with priority: {len(worse)}")
    print(f"Wrote: {out_path}")

if __name__ == "__main__":
    main()
