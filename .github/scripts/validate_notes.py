#!/usr/bin/env python3
"""Validate research notes in research/ and ideas in ideas/.

For every research/*.md file except README.md and TEMPLATE.md this checks:
  - the filename is lowercase kebab-case ending in .md
  - a YAML frontmatter block is present and parses
  - required frontmatter keys are present and well-typed
  - the four required body section headings are present

Ideas are deliberately low-barrier. For every ideas/*.md file except README.md and
TEMPLATE.md this checks only:
  - the filename is lowercase kebab-case ending in .md
  - a title is present (a YAML 'title:' or a '# ' heading)

Exits non-zero (printing every problem) if any note or idea is invalid.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

import yaml

RESEARCH_DIR = pathlib.Path("research")
IDEAS_DIR = pathlib.Path("ideas")
SKIP = {"README.md", "TEMPLATE.md"}

REQUIRED_KEYS = {
    "title": str,
    "author": str,
    "date": object,  # validated separately
    "tags": list,
    "status": str,
    "sources": list,
}
ALLOWED_STATUS = {"draft", "reviewed"}
REQUIRED_SECTIONS = [
    "## Summary",
    "## Key findings",
    "## CF relevance",
    "## Open questions",
]
FILENAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
H1_RE = re.compile(r"^#\s+\S", re.MULTILINE)


def validate_file(path: pathlib.Path) -> list[str]:
    problems: list[str] = []
    name = path.name

    if not FILENAME_RE.match(name):
        problems.append(
            f"filename must be lowercase kebab-case ending in .md (got '{name}')"
        )

    text = path.read_text(encoding="utf-8")

    match = FRONTMATTER_RE.match(text)
    if not match:
        problems.append("missing YAML frontmatter block (must start with '---' on line 1)")
        return [f"{path}: {p}" for p in problems]

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        problems.append(f"frontmatter is not valid YAML: {exc}")
        return [f"{path}: {p}" for p in problems]

    if not isinstance(meta, dict):
        problems.append("frontmatter must be a YAML mapping")
        return [f"{path}: {p}" for p in problems]

    for key, expected_type in REQUIRED_KEYS.items():
        value = meta.get(key)
        if value in (None, "", [], {}):
            problems.append(f"missing required frontmatter key '{key}'")
            continue
        if expected_type is not object and not isinstance(value, expected_type):
            problems.append(f"frontmatter key '{key}' must be a {expected_type.__name__}")

    status = meta.get("status")
    if isinstance(status, str) and status not in ALLOWED_STATUS:
        problems.append(
            f"'status' must be one of {sorted(ALLOWED_STATUS)} (got '{status}')"
        )

    date_val = meta.get("date")
    if date_val not in (None, "", [], {}):
        if isinstance(date_val, dt.date):
            pass  # YAML already parsed a date
        elif isinstance(date_val, str) and DATE_RE.match(date_val):
            pass
        else:
            problems.append("'date' must be in YYYY-MM-DD format")

    body = text[match.end():]
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^{re.escape(section)}\s*$", body, re.MULTILINE):
            problems.append(f"missing required section heading '{section}'")

    return [f"{path}: {p}" for p in problems]


def validate_idea(path: pathlib.Path) -> list[str]:
    """Light validation: kebab-case filename plus a title of some kind."""
    problems: list[str] = []
    name = path.name

    if not FILENAME_RE.match(name):
        problems.append(
            f"filename must be lowercase kebab-case ending in .md (got '{name}')"
        )

    text = path.read_text(encoding="utf-8")

    has_title = False
    body = text
    match = FRONTMATTER_RE.match(text)
    if match:
        body = text[match.end():]
        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            problems.append(f"frontmatter is not valid YAML: {exc}")
        else:
            if isinstance(meta, dict) and str(meta.get("title") or "").strip():
                has_title = True

    if not has_title and not H1_RE.search(body):
        problems.append("idea needs a title (a YAML 'title:' or a '# ' heading)")

    return [f"{path}: {p}" for p in problems]


def main() -> int:
    if not RESEARCH_DIR.is_dir():
        print(f"error: '{RESEARCH_DIR}/' directory not found", file=sys.stderr)
        return 1

    notes = sorted(p for p in RESEARCH_DIR.glob("*.md") if p.name not in SKIP)
    ideas = (
        sorted(p for p in IDEAS_DIR.glob("*.md") if p.name not in SKIP)
        if IDEAS_DIR.is_dir()
        else []
    )

    problems: list[str] = []
    for note in notes:
        problems.extend(validate_file(note))
    for idea in ideas:
        problems.extend(validate_idea(idea))

    if problems:
        print("Validation failed:\n")
        for problem in problems:
            print(f"  - {problem}")
        print(
            f"\n{len(problems)} problem(s) across "
            f"{len(notes)} research note(s) and {len(ideas)} idea(s)."
        )
        return 1

    print(f"OK: {len(notes)} research note(s) and {len(ideas)} idea(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
