#!/usr/bin/env python3
"""Summarize and validate rating distributions across all notes."""

from __future__ import annotations

import argparse
import statistics
import sys
from itertools import combinations

if __package__:
    from scripts.generate_research_map import load_notes
else:
    from generate_research_map import load_notes


REQUIRED_RATINGS = ("platform-impact", "maturity", "novelty", "actionability")
MATRICES = {
    "platform-impact-maturity": ("platform-impact", "maturity"),
    "platform-impact-novelty": ("platform-impact", "novelty"),
    "platform-impact-actionability": ("platform-impact", "actionability"),
    "novelty-actionability": ("actionability", "novelty"),
    "maturity-novelty": ("maturity", "novelty"),
    "maturity-actionability": ("maturity", "actionability"),
}


def summarize_ratings(notes) -> dict:
    values = {name: [] for name in REQUIRED_RATINGS}
    rows = []
    for note in notes:
        ratings = note.metadata.get("ratings", {})
        row = {
            name: rating["value"]
            for name, rating in ratings.items()
            if name in values
            and isinstance(rating, dict)
            and isinstance(rating.get("value"), (int, float))
        }
        rows.append(row)
        for name, value in row.items():
            values[name].append(value)

    rating_summaries = {}
    for name, observed in values.items():
        if not observed:
            continue
        quartiles = (
            statistics.quantiles(observed, n=4, method="inclusive")
            if len(observed) > 1
            else (observed[0], observed[0], observed[0])
        )
        distinct = len(set(observed))
        rating_summaries[name] = {
            "count": len(observed),
            "minimum": min(observed),
            "maximum": max(observed),
            "median": statistics.median(observed),
            "first_quartile": quartiles[0],
            "third_quartile": quartiles[2],
            "distinct": distinct,
            "duplicates": len(observed) - distinct,
        }

    correlations = {}
    for first, second in combinations(REQUIRED_RATINGS, 2):
        paired = [(row[first], row[second]) for row in rows if first in row and second in row]
        key = f"{first}:{second}"
        try:
            correlations[key] = statistics.correlation(
                [pair[0] for pair in paired], [pair[1] for pair in paired]
            )
        except statistics.StatisticsError:
            correlations[key] = None

    matrices = {}
    for matrix, (vertical, horizontal) in MATRICES.items():
        quadrants = {"low-low": 0, "low-high": 0, "high-low": 0, "high-high": 0}
        for row in rows:
            if vertical in row and horizontal in row:
                vertical_side = "low" if row[vertical] <= 50 else "high"
                horizontal_side = "low" if row[horizontal] <= 50 else "high"
                quadrants[f"{vertical_side}-{horizontal_side}"] += 1
        matrices[matrix] = quadrants

    return {
        "count": len(rows),
        "ratings": rating_summaries,
        "correlations": correlations,
        "matrices": matrices,
    }


def validate_summary(summary: dict) -> None:
    ratings = summary["ratings"]
    for name in REQUIRED_RATINGS:
        if name not in ratings or ratings[name]["count"] != summary["count"]:
            raise ValueError(f"missing required rating: {name}")
    for name in REQUIRED_RATINGS:
        rating = ratings[name]
        if rating["distinct"] < 5:
            raise ValueError(f"rating '{name}' has fewer than 5 distinct values")
        if rating["maximum"] <= 50:
            raise ValueError(f"rating '{name}' values are strictly below 50")
        if rating["minimum"] >= 50:
            raise ValueError(f"rating '{name}' values are strictly above 50")


def print_summary(summary: dict) -> None:
    for name, rating in summary["ratings"].items():
        print(
            f"{name}: count={rating['count']} min={rating['minimum']} "
            f"max={rating['maximum']} median={rating['median']} "
            f"q1={rating['first_quartile']} q3={rating['third_quartile']} "
            f"distinct={rating['distinct']} duplicates={rating['duplicates']}"
        )
    print("correlations:")
    for pair, correlation in summary["correlations"].items():
        value = "undefined" if correlation is None else f"{correlation:.3f}"
        print(f"  {pair}: {value}")
    print("matrix quadrants (vertical-horizontal):")
    for matrix, quadrants in summary["matrices"].items():
        counts = " ".join(f"{name}={count}" for name, count in quadrants.items())
        print(f"  {matrix}: {counts}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        summary = summarize_ratings(load_notes())
        print_summary(summary)
        if args.check:
            validate_summary(summary)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
