#!/usr/bin/env python3
"""
Analyze reordering vs drop logs.

Inputs (default filenames in current folder):
  - reordering_lqd_per_flow.txt
      Columns (per row): dst,src,recorder,dstport,srcport,expected,received,priority
      Note: some logs fuse header "priority" with first row; handled automatically.

  - drop_events_lqd.txt
      Columns: (either)
        A) src,dst,srcport,dstport,seq1,seq2,...
        B) dst,src,dstport,srcport,seq1,seq2,...   (script auto-detects & normalizes)

What it outputs (CSV in current folder):
  1) expected_seq_missing_ALL.csv
        One row per unique (flow, expected) that is missing in drops
        reason ∈ {"no_drop_flow", "not_in_drop_list"}

  2) missing_expected_where_drop_flow_absent.csv
        (subset of #1) rows where there is NO drop-line for that flow

  3) missing_expected_where_drop_flow_exists_but_missing.csv
        (subset of #1) rows where the drop-line exists but the expected seq isn’t listed

  4) flows_with_reordering_but_no_drop_entry.csv
        Per-flow summary of #2

  5) flows_with_drop_but_missing_expected_summary.csv
        Per-flow summary of #3

  6) expected_seq_matched_in_drops.csv
        Sanity list where expected seq DOES appear in drops

Console summary prints key counts.

Usage:
  python3 analyze_reordering_vs_drops.py \
      --reorder reordering_lqd_per_flow.txt \
      --drops drop_events_lqd.txt
(Args are optional if you keep the default names.)
"""
import argparse, csv, re, sys
from collections import defaultdict, OrderedDict
from pathlib import Path

def load_drops(path: Path):
    """
    Parse drops into: dict[(src, dst, srcport, dstport)] -> set(seqNums)
    Auto-detects orientation by looking at the first non-empty line.
    """
    if not path.exists():
        sys.exit(f"[ERROR] Drops file not found: {path}")

    # Detect orientation
    first_nonempty = ""
    with path.open() as f:
        for raw in f:
            t = raw.strip()
            if t:
                first_nonempty = t
                break
    is_dst_first = first_nonempty.lower().startswith("dst,src")
    is_src_first = first_nonempty.lower().startswith("src,dst")

    drops = {}
    with path.open() as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 4:
                continue
            # skip header-like line
            if parts[0].lower() in {"dst","src"} and parts[1].lower() in {"src","dst"}:
                continue
            try:
                if is_dst_first and not is_src_first:
                    # file is: dst,src,dstport,srcport,seqs...
                    dst, src = parts[0], parts[1]
                    dp, sp = int(parts[2]), int(parts[3])
                    key = (src, dst, sp, dp)
                    seq_fields = parts[4:]
                else:
                    # assume: src,dst,srcport,dstport,seqs...
                    src, dst = parts[0], parts[1]
                    sp, dp = int(parts[2]), int(parts[3])
                    key = (src, dst, sp, dp)
                    seq_fields = parts[4:]
            except ValueError:
                # malformed line; skip
                continue

            seqs = set()
            for x in seq_fields:
                x = x.strip()
                if not x:
                    continue
                try:
                    seqs.add(int(x))
                except ValueError:
                    # tolerate non-integers
                    pass
            drops[key] = seqs
    return drops

def load_reordering(path: Path):
    """
    Return:
      reord_by_flow: dict[(src, dst, srcport, dstport)] -> dict[expected] -> set(received variants)
    """
    if not path.exists():
        sys.exit(f"[ERROR] Reordering file not found: {path}")

    # Fix fused header if present
    raw_text = path.read_text()
    raw_text = raw_text.replace("priorityh", "priority\nh")

    rows = []
    for raw in raw_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("@"):
            continue
        if line.lower().startswith("dst,src,recorder"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 8:
            continue
        try:
            dst, src, recorder = parts[0], parts[1], parts[2]
            dstport, srcport = int(parts[3]), int(parts[4])
            expected, received = int(parts[5]), int(parts[6])
            # priority may contain stray chars; strip non-digits
            pristr = re.sub(r"[^\d-]+", "", parts[7])
            _priority = int(pristr) if pristr else None
        except Exception:
            continue
        rows.append((dst, src, recorder, dstport, srcport, expected, received))

    reord_by_flow = defaultdict(lambda: defaultdict(set))
    for (dst, src, _rec, dstport, srcport, exp, rcv) in rows:
        key = (src, dst, srcport, dstport)  # normalized direction for matching drops
        reord_by_flow[key][exp].add(rcv)
    return reord_by_flow

def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reorder", default="reordering_lqd_per_flow.txt", help="Reordering file")
    ap.add_argument("--drops", default="drop_events_lqd.txt", help="Drops file")
    args = ap.parse_args()

    reorder_path = Path(args.reorder)
    drops_path = Path(args.drops)

    drops = load_drops(drops_path)
    reord_by_flow = load_reordering(reorder_path)

    missing_all = []  # combined view with reason
    missing_no_drop_flow = []
    missing_drop_exists_but_not_listed = []
    matched = []

    # Summaries
    summary_no_drop = []
    summary_drop_exists_missing = []

    for flow, exp_map in reord_by_flow.items():
        src, dst, sp, dp = flow
        drop_seqs = drops.get(flow)

        # Build per-flow summaries:
        exp_list = sorted(exp_map.keys())

        if drop_seqs is None:
            # No drop line at all for this flow
            for e in exp_list:
                rset = sorted(exp_map[e])
                row = OrderedDict([
                    ("src", src), ("dst", dst), ("srcport", sp), ("dstport", dp),
                    ("expected_seqNum", e),
                    ("received_seqNums", " ".join(map(str, rset))),
                    ("n_received_variants", len(rset)),
                    ("reason", "no_drop_flow")
                ])
                missing_all.append(row)
                missing_no_drop_flow.append({k: row[k] for k in row.keys() if k != "reason"})

            summary_no_drop.append(OrderedDict([
                ("src", src), ("dst", dst), ("srcport", sp), ("dstport", dp),
                ("n_missing_expected", len(exp_list)),
                ("expected_seq_list", " ".join(map(str, exp_list))),
            ]))
        else:
            # Drop line exists; split into missing vs matched
            missing_here = []
            for e in exp_list:
                in_drop = (e in drop_seqs)
                rset = sorted(exp_map[e])
                if in_drop:
                    matched.append(OrderedDict([
                        ("src", src), ("dst", dst), ("srcport", sp), ("dstport", dp),
                        ("expected_seqNum", e),
                        ("received_seqNums", " ".join(map(str, rset))),
                        ("n_received_variants", len(rset)),
                    ]))
                else:
                    row = OrderedDict([
                        ("src", src), ("dst", dst), ("srcport", sp), ("dstport", dp),
                        ("expected_seqNum", e),
                        ("received_seqNums", " ".join(map(str, rset))),
                        ("n_received_variants", len(rset)),
                        ("reason", "not_in_drop_list")
                    ])
                    missing_all.append(row)
                    missing_drop_exists_but_not_listed.append({k: row[k] for k in row.keys() if k != "reason"})
                    missing_here.append(e)

            if missing_here:
                summary_drop_exists_missing.append(OrderedDict([
                    ("src", src), ("dst", dst), ("srcport", sp), ("dstport", dp),
                    ("n_missing_expected", len(missing_here)),
                    ("expected_seq_list", " ".join(map(str, sorted(missing_here)))),
                ]))

    # Write outputs
    write_csv("expected_seq_missing_ALL.csv",
              missing_all,
              ["src","dst","srcport","dstport","expected_seqNum","received_seqNums","n_received_variants","reason"])

    write_csv("missing_expected_where_drop_flow_absent.csv",
              missing_no_drop_flow,
              ["src","dst","srcport","dstport","expected_seqNum","received_seqNums","n_received_variants"])

    write_csv("missing_expected_where_drop_flow_exists_but_missing.csv",
              missing_drop_exists_but_not_listed,
              ["src","dst","srcport","dstport","expected_seqNum","received_seqNums","n_received_variants"])

    write_csv("expected_seq_matched_in_drops.csv",
              matched,
              ["src","dst","srcport","dstport","expected_seqNum","received_seqNums","n_received_variants"])

    write_csv("flows_with_reordering_but_no_drop_entry.csv",
              summary_no_drop,
              ["src","dst","srcport","dstport","n_missing_expected","expected_seq_list"])

    write_csv("flows_with_drop_but_missing_expected_summary.csv",
              summary_drop_exists_missing,
              ["src","dst","srcport","dstport","n_missing_expected","expected_seq_list"])

    # Console summary
    flows_total = len(reord_by_flow)
    flows_no_drop = len(summary_no_drop)
    uniq_missing_total = len({(r["src"], r["dst"], r["srcport"], r["dstport"], r["expected_seqNum"])
                              for r in missing_all})
    uniq_missing_no_drop = len({(r["src"], r["dst"], r["srcport"], r["dstport"], r["expected_seqNum"])
                                for r in missing_no_drop_flow})
    uniq_missing_drop_exists = len({(r["src"], r["dst"], r["srcport"], r["dstport"], r["expected_seqNum"])
                                    for r in missing_drop_exists_but_not_listed})

    print("\n=== SUMMARY ===")
    print(f"Reordering flows: {flows_total}")
    print(f"Flows with reordering but NO drop-line: {flows_no_drop}")
    print(f"Unique (flow, expected) MISSING in drops (ALL): {uniq_missing_total}")
    print(f"  - where drop flow ABSENT: {uniq_missing_no_drop}")
    print(f"  - where drop flow EXISTS but expected NOT listed: {uniq_missing_drop_exists}")
    print("\nCSV written:")
    for name in [
        "expected_seq_missing_ALL.csv",
        "missing_expected_where_drop_flow_absent.csv",
        "missing_expected_where_drop_flow_exists_but_missing.csv",
        "expected_seq_matched_in_drops.csv",
        "flows_with_reordering_but_no_drop_entry.csv",
        "flows_with_drop_but_missing_expected_summary.csv",
    ]:
        print(f"  - {name}")

if __name__ == "__main__":
    main()
