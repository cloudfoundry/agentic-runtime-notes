#!/usr/bin/env python3
"""Generate the static workshop map from repository notes."""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
from dataclasses import dataclass

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLOTS_PATH = ROOT / "scripts" / "research_map_plots.yaml"
OUTPUT_PATH = ROOT / "generated" / "research-map.html"
GITHUB_BASE = "https://github.com/cloudfoundry/agentic-runtime-notes/blob/main"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass
class Note:
    path: pathlib.Path
    kind: str
    title: str
    summary: str
    metadata: dict


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter block")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return metadata, text[match.end() :]


def _section_body(body: str, heading: str) -> str | None:
    match = re.search(rf"^## {re.escape(heading)}\s*$", body, re.MULTILINE)
    if not match:
        return None
    section = body[match.end() :]
    section = re.split(r"^##\s+", section, maxsplit=1, flags=re.MULTILINE)[0]
    paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
    return paragraphs[0] if paragraphs else None


def _plain_text(value: str) -> str:
    value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_`>#]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_summary(path: str | pathlib.Path, body: str) -> str:
    heading = "Summary" if str(path).startswith("research/") else "The idea"
    summary = _section_body(body, heading)
    if summary is None:
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        summary = paragraphs[0] if paragraphs else "No summary provided."
    return _plain_text(summary)


def validate_ratings(ratings: object) -> dict:
    if ratings is None:
        return {}
    if not isinstance(ratings, dict):
        raise ValueError("ratings must be a mapping")
    for name, rating in ratings.items():
        if not isinstance(rating, dict):
            raise ValueError(f"rating '{name}' must be a mapping")
        value = rating.get("value")
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError(f"rating '{name}' value must be an integer in 0..100")
        if not isinstance(rating.get("note"), str) or not rating["note"].strip():
            raise ValueError(f"rating '{name}' requires a non-empty note")
    return ratings


def parse_note(path: pathlib.Path, text: str) -> Note:
    metadata, body = parse_frontmatter(text)
    relative = path.as_posix()
    kind = "research" if relative.startswith("research/") else "idea"
    title = str(metadata.get("title") or path.stem.replace("-", " ").title())
    ratings = validate_ratings(metadata.get("ratings"))
    metadata["ratings"] = ratings
    return Note(path, kind, title, extract_summary(relative, body), metadata)


def derive_position(ratings: dict, plot: dict) -> dict | None:
    x_name = plot["x"]["rating"]
    y_name = plot["y"]["rating"]
    if x_name not in ratings or y_name not in ratings:
        return None
    return {"x": ratings[x_name]["value"], "y": ratings[y_name]["value"]}


def github_url(path: pathlib.Path) -> str:
    return f"{GITHUB_BASE}/{path.as_posix()}"


def validate_plot(plot: dict) -> None:
    for axis in ("x", "y"):
        if not isinstance(plot.get(axis), dict) or not plot[axis].get("rating"):
            raise ValueError(f"plot axis '{axis}' must name a rating")


def load_notes(root: pathlib.Path = ROOT) -> list[Note]:
    notes = []
    for directory, kind in ((root / "research", "research"), (root / "ideas", "idea")):
        for path in sorted(directory.glob("*.md")):
            if path.name in {"README.md", "TEMPLATE.md"}:
                continue
            notes.append(parse_note(path.relative_to(root), path.read_text(encoding="utf-8")))
    return notes


def load_plots() -> dict:
    plots = yaml.safe_load(PLOTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(plots, dict) or not plots:
        raise ValueError("plot configuration must be a non-empty mapping")
    for plot in plots.values():
        validate_plot(plot)
    return plots


def note_payload(note: Note, plot: dict) -> dict:
    ratings = note.metadata["ratings"]
    return {
        "id": note.path.as_posix(),
        "kind": note.kind,
        "title": note.title,
        "summary": note.summary,
        "tags": note.metadata.get("tags", []),
        "author": note.metadata.get("author", ""),
        "date": str(note.metadata.get("date", "")),
        "ratings": ratings,
        "position": derive_position(ratings, plot),
        "url": github_url(note.path),
    }


def generate_html(notes: list[Note], plots: dict) -> str:
    plot_id, plot = next(iter(plots.items()))
    payload = [note_payload(note, plot) for note in notes]
    data = json.dumps(payload, ensure_ascii=True).replace("</", "<\\/")
    title = html.escape(plot["title"])
    x = plot["x"]
    y = plot["y"]
    markers = []
    unplaced = []
    for item in payload:
        if item["position"]:
            p = item["position"]
            markers.append(
                f'<button class="marker {item["kind"]}" style="left:{p["x"]}%;bottom:{p["y"]}%" data-id="{html.escape(item["id"])}" aria-label="{html.escape(item["title"])}"></button>'
            )
        else:
            unplaced.append(f'<li><a href="{html.escape(item["url"])}">{html.escape(item["title"])}</a></li>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:#101619; color:#e7f1ed; }}
body {{ max-width:1200px; margin:0 auto; padding:36px 24px; }} h1 {{ font-size:clamp(2rem,5vw,4rem); margin:0 0 8px; }}
.intro {{ color:#9eb4ac; max-width:760px; line-height:1.5; }} .map {{ position:relative; height:620px; margin:34px 42px 20px 90px; border-left:1px solid #668078; border-bottom:1px solid #668078; background:linear-gradient(90deg,transparent 49.9%,#243a35 50%,transparent 50.1%),linear-gradient(0deg,transparent 49.9%,#243a35 50%,transparent 50.1%); }}
.axis-x,.axis-y {{ position:absolute; color:#9eb4ac; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; }} .axis-x {{ left:0; right:0; bottom:-34px; text-align:center; }} .axis-y {{ transform:rotate(-90deg); left:-78px; top:50%; }}
.marker {{ position:absolute; transform:translate(-50%,50%); width:18px; height:18px; border:2px solid #d9fff0; cursor:pointer; }} .marker.research {{ border-radius:50%; background:#64c5a0; }} .marker.idea {{ transform:translate(-50%,50%) rotate(45deg); background:#e6a85b; }}
.legend {{ display:flex; gap:22px; color:#b4c8c0; font-size:.9rem; }} .legend span::before {{ content:""; display:inline-block; width:11px; height:11px; margin-right:7px; background:#64c5a0; border-radius:50%; }} .legend .idea-key::before {{ background:#e6a85b; border-radius:0; transform:rotate(45deg); }}
.unplaced {{ margin-top:56px; border-top:1px solid #304640; padding-top:18px; }} a {{ color:#8ee3bf; }} dialog {{ max-width:620px; width:calc(100% - 48px); color:#e7f1ed; background:#172320; border:1px solid #668078; border-radius:14px; padding:26px; }} dialog::backdrop {{ background:#020505bb; }} .close {{ float:right; background:none; color:inherit; border:0; font-size:1.5rem; cursor:pointer; }} .tag {{ color:#9eb4ac; margin-right:8px; }} .rating {{ border-top:1px solid #304640; padding:12px 0; }} .rating strong {{ color:#8ee3bf; }}
@media(max-width:600px) {{ body {{ padding:24px 14px; }} .map {{ height:720px; margin-left:58px; }} .axis-y {{ left:-64px; }} }}
</style></head><body><main><p class="intro">Agentic Runtime Working Group · provisional workshop view</p><h1>{title}</h1>
<p class="intro">Initial working-group ratings, shown to seed discussion rather than establish a permanent taxonomy. Click a note for its summary, rating justifications, and source.</p>
<div class="legend"><span>Research</span><span class="idea-key">Idea</span></div><section class="map" aria-label="{title}">{''.join(markers)}<span class="axis-x">{html.escape(x["low"])} ← {html.escape(x["label"])} → {html.escape(x["high"])}</span><span class="axis-y">{html.escape(y["low"])} ← {html.escape(y["label"])} → {html.escape(y["high"])}</span></section>
<section class="unplaced"><h2>Unplaced notes</h2><ul>{''.join(unplaced) or '<li>All notes are placed.</li>'}</ul></section></main>
<dialog id="detail"><button class="close" aria-label="Close">X</button><div id="content"></div></dialog>
<script>const notes={data};const dialog=document.querySelector('#detail'),content=document.querySelector('#content');
function show(note){{const tags=(note.tags||[]).map(t=>`<span class="tag">#${{t}}</span>`).join('');const ratings=Object.entries(note.ratings||{{}}).map(([name,r])=>`<div class="rating"><strong>${{name}}: ${{r.value}}/100</strong><br>${{r.note}}</div>`).join('');content.innerHTML=`<button class="close" aria-label="Close">X</button><p class="intro">${{note.kind}}</p><h2>${{note.title}}</h2><p>${{note.summary}}</p><p>${{tags}}</p>${{ratings}}<p><a href="${{note.url}}">Read the full Markdown note on GitHub</a></p>`;dialog.showModal();dialog.querySelectorAll('.close').forEach(b=>b.onclick=()=>dialog.close())}}
document.querySelectorAll('.marker').forEach(m=>m.onclick=()=>show(notes.find(n=>n.id===m.dataset.id)));dialog.addEventListener('click',e=>{{if(e.target===dialog)dialog.close()}});</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        output = generate_html(load_notes(), load_plots())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != output:
            print(f"{OUTPUT_PATH} is stale; run the generator", file=sys.stderr)
            return 1
    else:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(output, encoding="utf-8")
        print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
