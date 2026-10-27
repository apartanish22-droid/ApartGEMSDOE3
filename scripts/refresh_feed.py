#!/usr/bin/env python3
"""Refresh a public leaderboard snapshot and nine source heads without logging in.

Failure keeps the last good observation with its original timestamp and records an
error; it is never relabelled fresh. No portal submissions or private data access.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "docs/data/live_feed.json"
LEADERBOARD = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
SITES = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")
UA = "ApartGEMSDOE3-research-feed/1.0 (+https://github.com/apartanish22-droid/ApartGEMSDOE3)"


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.table_depth = 0
        self.row = None
        self.cell = None
        self.rows = None
        self.tables = []
        self.cell_type = None
        self.nested_table = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.table_depth == 0:
                self.rows = []
                self.nested_table = False
            else:
                self.nested_table = True
            self.table_depth += 1
        elif self.table_depth == 1 and tag == "tr":
            self.row = []
        elif self.row is not None and tag in ("th", "td"):
            self.cell = []
            self.cell_type = tag
        elif self.cell is not None and tag in ("br", "div", "p"):
            self.cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None:
            self.row.append((self.cell_type, " ".join("".join(self.cell).split())))
            self.cell, self.cell_type = None, None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1
            if self.table_depth == 0:
                # Nested tables can change row/column semantics; do not guess.
                if not self.nested_table:
                    self.tables.append(self.rows)
                self.rows = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def parse_leaderboard(html: str) -> float:
    """Read rank and public-score columns from the *same* recognized table.

    Refuse multiple tables, ambiguous columns, nonnumeric scores, or a changed
    layout. Never accidentally take a rank-one value from an unrelated table.
    """
    parser = TableParser()
    parser.feed(html)
    matches = []
    for rows in parser.tables:
        for index, row in enumerate(rows):
            if not any(kind == "th" for kind, _ in row):
                continue
            labels = [text.lower().strip() for _, text in row]
            rank_columns = [i for i, text in enumerate(labels) if text == "rank"]
            score_columns = [i for i, text in enumerate(labels)
                             if "public" in text and "tversky" in text]
            if rank_columns and score_columns:
                if len(rank_columns) != 1 or len(score_columns) != 1:
                    raise ValueError("ambiguous leaderboard columns")
                matches.append((rows[index + 1:], len(row), rank_columns[0], score_columns[0]))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one public leaderboard table; found {len(matches)}")
    rows, width, rank_col, score_col = matches[0]
    candidates = []
    for row in rows:
        cells = [text for _, text in row]
        if len(cells) <= rank_col or not re.fullmatch(r"#?\s*1", cells[rank_col]):
            continue
        if len(cells) != width or not re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", cells[score_col]):
            raise ValueError("rank-one row has an unexpected width or nonnumeric score")
        candidates.append(float(cells[score_col]))
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one rank-one row; found {len(candidates)}")
    return candidates[0]


def fetch(url: str, token: str | None = None):
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json" if token else "text/html"}
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        final = response.geturl()
        if url == LEADERBOARD and not final.startswith(LEADERBOARD):
            raise ValueError("leaderboard redirected away from its public page")
        return response.read().decode("utf-8", errors="strict")


def refresh(previous: dict, *, skip_leaderboard=False, skip_heads=False) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    result = {**previous, "last_attempt_utc": now}
    if not skip_leaderboard:
        try:
            value = parse_leaderboard(fetch(LEADERBOARD))
            result["leaderboard"] = {"observed_utc": now, "value": value,
                                     "evidence_class": "PUBLIC LEADERBOARD, not a submission receipt",
                                     "source": LEADERBOARD,
                                     "retrieval": "public page, no submission filename or receipt"}
            result["leaderboard_error"] = None
            result["leaderboard_status"] = "success"
        except (OSError, ValueError, UnicodeError) as exc:
            result["leaderboard_error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            result["leaderboard_status"] = "error"
    else:
        result["leaderboard_status"] = "skipped"
    if not skip_heads:
        results = dict(previous.get("site_heads", {}))
        errors = {}
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        for site in SITES:
            try:
                data = json.loads(fetch(f"https://api.github.com/repos/buffedlizard55-lab/{site}/commits/main", token))
                sha = data["sha"]
                if not re.fullmatch(r"[a-f0-9]{40}", sha):
                    raise ValueError("invalid commit SHA")
                results[site] = {"sha": sha, "observed_utc": now}
            except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
                errors[site] = f"{type(exc).__name__}: {str(exc)[:200]}"
        result["site_heads"] = results
        result["site_head_errors"] = errors
        result["site_heads_status"] = "success" if not errors else "partial_or_failed"
    else:
        result["site_heads_status"] = "skipped"
    result["note"] = "Time-stamped snapshot; refresh can fail and a public board never authenticates a filename."
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-leaderboard", action="store_true", help="Use where direct competition-host access is restricted")
    ap.add_argument("--skip-heads", action="store_true")
    ap.add_argument("--out", type=Path, default=FEED)
    args = ap.parse_args(argv)
    previous = json.loads(args.out.read_text()) if args.out.exists() else {}
    result = refresh(previous, skip_leaderboard=args.skip_leaderboard, skip_heads=args.skip_heads)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    temporary.replace(args.out)
    print(f"Feed written; leaderboard_error={result.get('leaderboard_error')}; site_errors={len(result.get('site_head_errors', {}))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
