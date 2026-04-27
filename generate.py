#!/usr/bin/env python3
"""Generate Jekyll data files from votes.csv for JOI problem voting results."""

import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict
from urllib.error import URLError
from urllib.request import urlopen
import ssl

VOTES_FILE = "votes.csv"
OUTPUT_FILE = os.path.join("_data", "results.json")
TASKS_URL = "https://joi.goodbaton.com/data/tasks.json"

# Matches any URI scheme (e.g. http:, https:, javascript:, data:, …)
_ANY_SCHEME_RE = re.compile(r"^\w[\w+\-.]*:", re.IGNORECASE)
# Only http / https are considered safe for hrefs
_SAFE_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def is_safe_url(value: str) -> bool:
    """Return True only for http/https URLs (prevents javascript: etc.)."""
    return bool(_SAFE_URL_RE.match(value))


def fetch_tasks() -> list:
    """Fetch task metadata from the JOI API."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urlopen(TASKS_URL, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, Exception) as exc:
        print(f"Warning: Could not fetch tasks.json: {exc}", file=sys.stderr)
        return []


def build_task_lookup(tasks: list) -> dict:
    """Build a dict mapping task name/title → task info."""
    lookup: dict = {}
    for task in tasks:
        for key in ("name", "title", "id"):
            value = task.get(key)
            if value and isinstance(value, str):
                lookup.setdefault(value, task)
    return lookup


def read_votes(filename: str) -> list:
    """Read voting rows from the CSV file."""
    votes = []
    with open(filename, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header row
        for row in reader:
            if len(row) < 4:
                continue
            timestamp = row[0].strip()
            nickname = row[1].strip()
            problems = []
            for i in range(3):
                base = 3 + i * 3
                # Need at least the problem name column
                if base >= len(row):
                    break
                name = row[base].strip() if base < len(row) else ""
                source = row[base + 1].strip() if base + 1 < len(row) else ""
                reason = row[base + 2].strip() if base + 2 < len(row) else ""
                if name:
                    # If source looks like any URI scheme but is not http/https, blank it
                    if source and _ANY_SCHEME_RE.match(source) and not is_safe_url(source):
                        source = ""
                    problems.append(
                        {
                            "name": name,
                            "source": source,
                            "reason": reason,
                        }
                    )
            if problems:
                votes.append(
                    {
                        "timestamp": timestamp,
                        "nickname": nickname,
                        "problems": problems,
                    }
                )
    return votes


def aggregate_votes(votes: list, task_lookup: dict) -> list:
    """Count votes per problem, rank them, and attach comments."""
    vote_counts: dict = defaultdict(int)
    # Use the first seen source for each problem key
    first_source: dict = {}
    comments: dict = defaultdict(list)

    for vote in votes:
        display_name = vote["nickname"] if vote["nickname"] else "匿名"
        for problem in vote["problems"]:
            name = problem["name"]
            vote_counts[name] += 1
            if name not in first_source and problem["source"]:
                first_source[name] = problem["source"]
            if problem["reason"]:
                comments[name].append(
                    {
                        "nickname": display_name,
                        "reason": problem["reason"],
                    }
                )

    # Sort: descending vote count, then ascending problem name for deterministic order
    sorted_problems = sorted(vote_counts.items(), key=lambda x: (-x[1], x[0]))

    results = []
    current_rank = 0
    prev_count = None
    for position, (name, count) in enumerate(sorted_problems, start=1):
        if count != prev_count:
            current_rank = position
            prev_count = count

        source = first_source.get(name, "")
        source_url = ""

        # If the source field itself is already a URL, use it directly
        if is_safe_url(source):
            source_url = source
            source = ""

        # Try to enrich source and source URL from tasks.json if they are missing
        task_info = task_lookup.get(name)
        if task_info:
            if not source:
                source = task_info.get("source", "")
                
            if not source_url:
                for url_key in ("url", "link", "atcoder_url", "aoj_url"):
                    url_val = task_info.get(url_key, "")
                    if url_val and is_safe_url(url_val):
                        source_url = url_val
                        break
            
            if not source_url:
                atcoder_contest = task_info.get("atcoder_contest")
                atcoder_id = task_info.get("atcoder_id")
                if atcoder_contest and atcoder_id:
                    source_url = f"https://atcoder.jp/contests/{atcoder_contest}/tasks/{atcoder_id}"

        results.append(
            {
                "rank": current_rank,
                "name": name,
                "source": source,
                "source_url": source_url,
                "votes": count,
                "comments": comments[name],
            }
        )

    return results


def main() -> None:
    csv_files = glob.glob("votes/*.csv")
    if not csv_files:
        # Fallback for old filenames if they exist in the root
        csv_files = glob.glob("votes_*.csv")
        if not csv_files and os.path.exists("votes.csv"):
            csv_files = ["votes.csv"]
            
        if not csv_files:
            print("Warning: No .csv files found in votes/ directory.", file=sys.stderr)
            return

    tasks = fetch_tasks()
    task_lookup = build_task_lookup(tasks)

    os.makedirs(os.path.join("_data", "votes"), exist_ok=True)

    for csv_file in csv_files:
        basename = os.path.basename(csv_file)
        if basename.endswith(".csv"):
            vote_id = basename[:-4]
            if vote_id.startswith("votes_"):
                vote_id = vote_id[len("votes_"):]
        else:
            vote_id = "results"
            
        output_file = os.path.join("_data", "votes", f"{vote_id}.json")
        
        votes = read_votes(csv_file)
        results = aggregate_votes(votes, task_lookup)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"Generated {output_file} with {len(results)} problems from {len(votes)} votes.")


if __name__ == "__main__":
    main()
