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
PRIMITIVES_PATH = ROOT / "scripts" / "platform_primitives.yaml"
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


def group_payload(payload: list[dict]) -> dict[tuple[int, int], list[dict]]:
    groups: dict[tuple[int, int], list[dict]] = {}
    for item in payload:
        position = item.get("position")
        if position is not None:
            key = (position["x"], position["y"])
            groups.setdefault(key, []).append(item)
    return groups


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


def validate_primitives(primitives: object, known_paths: set[str]) -> list[dict]:
    if not isinstance(primitives, list) or not primitives:
        raise ValueError("primitive configuration must be a non-empty list")

    required_fields = (
        "id",
        "title",
        "proposition",
        "cf_gap",
        "strategic_decision",
        "poc",
        "rfc_scope",
    )
    seen_ids = set()
    for primitive in primitives:
        if not isinstance(primitive, dict):
            raise ValueError("each primitive must be a mapping")
        for field in required_fields:
            if not isinstance(primitive.get(field), str) or not primitive[field].strip():
                raise ValueError(f"primitive requires a non-empty '{field}'")

        primitive_id = primitive["id"]
        if primitive_id in seen_ids:
            raise ValueError(f"duplicate primitive id: {primitive_id}")
        seen_ids.add(primitive_id)

        core = primitive.get("core")
        supporting = primitive.get("supporting")
        if not isinstance(core, list) or not core:
            raise ValueError(f"primitive '{primitive_id}' requires non-empty core membership")
        if not isinstance(supporting, list):
            raise ValueError(f"primitive '{primitive_id}' supporting membership must be a list")

        memberships = core + supporting
        if any(not isinstance(path, str) or not path.strip() for path in memberships):
            raise ValueError(f"primitive '{primitive_id}' note paths must be non-empty strings")
        if len(memberships) != len(set(memberships)):
            raise ValueError(f"primitive '{primitive_id}' has a duplicate note path")
        for path in memberships:
            if path not in known_paths:
                raise ValueError(f"primitive '{primitive_id}' references unknown note path: {path}")

    return primitives


def load_primitives() -> list[dict]:
    primitives = yaml.safe_load(PRIMITIVES_PATH.read_text(encoding="utf-8"))
    known_paths = {note.path.as_posix() for note in load_notes()}
    return validate_primitives(primitives, known_paths)


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
    plot_payloads = {plot_id: [note_payload(note, plot) for note in notes] for plot_id, plot in plots.items()}
    data = json.dumps(plot_payloads, ensure_ascii=True).replace("</", "<\\/")
    matrices = []
    for plot_id, plot in plots.items():
        payload = plot_payloads[plot_id]
        markers = []
        unplaced = []
        for key, group in group_payload(payload).items():
            p = group[0]["position"]
            if len(group) == 1:
                item = group[0]
                markers.append(
                    f'<button class="marker {item["kind"]}" style="left:{p["x"]}%;bottom:{p["y"]}%" data-plot="{html.escape(plot_id)}" data-id="{html.escape(item["id"])}" aria-label="{html.escape(item["title"])}"></button>'
                )
            else:
                cluster_id = f"{plot_id}:{p['x']}:{p['y']}"
                markers.append(
                    f'<button class="marker cluster" style="left:{p["x"]}%;bottom:{p["y"]}%" data-plot="{html.escape(plot_id)}" data-cluster="{html.escape(cluster_id)}" aria-label="{len(group)} notes at this position">{len(group)}</button>'
                )
        for item in payload:
            if item["position"] is None:
                label = "Research" if item["kind"] == "research" else "Idea"
                unplaced.append(f'<li><span class="note-kind {item["kind"]}"><span class="note-type {item["kind"]}">{label}</span></span><a href="{html.escape(item["url"])}">{html.escape(item["title"])}</a></li>')
        title = html.escape(plot["title"])
        x = plot["x"]
        y = plot["y"]
        matrices.append(f'''<section class="matrix"><h2>{title}</h2><div class="map" aria-label="{title}">{''.join(markers)}<span class="axis-x">{html.escape(x["low"])} &lt; {html.escape(x["label"])} &gt; {html.escape(x["high"])}</span><span class="axis-y">{html.escape(y["low"])} &lt; {html.escape(y["label"])} &gt; {html.escape(y["high"])}</span></div><details class="unplaced"><summary>Unplaced notes ({len(unplaced)})</summary><ul>{''.join(unplaced) or '<li>All notes are placed.</li>'}</ul></details></section>''')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:#101619; color:#e7f1ed; }}
body {{ max-width:1200px; margin:0 auto; padding:36px 24px; }} h1 {{ font-size:clamp(2rem,5vw,4rem); margin:0 0 8px; }}
.intro {{ color:#9eb4ac; max-width:760px; line-height:1.5; }} .map {{ position:relative; height:620px; margin:34px 42px 20px 90px; border-left:1px solid #668078; border-bottom:1px solid #668078; background:linear-gradient(90deg,transparent 49.9%,#243a35 50%,transparent 50.1%),linear-gradient(0deg,transparent 49.9%,#243a35 50%,transparent 50.1%); }}
.matrix {{ margin-top:48px; }} .axis-x,.axis-y {{ position:absolute; color:#9eb4ac; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; }} .axis-x {{ left:0; right:0; bottom:-34px; text-align:center; }} .axis-y {{ writing-mode:vertical-rl; transform:rotate(180deg) translateY(50%); left:-52px; top:50%; text-align:center; white-space:nowrap; }}
.marker {{ position:absolute; transform:translate(-50%,50%); width:18px; height:18px; border:2px solid #d9fff0; cursor:pointer; }} .marker.research {{ border-radius:50%; background:#64c5a0; }} .marker.idea {{ transform:translate(-50%,50%) rotate(45deg); background:#e6a85b; }} .marker.cluster {{ transform:translate(-50%,50%); width:30px; height:30px; border-radius:50%; background:#d9fff0; color:#10201b; font-weight:800; }}
.legend {{ display:flex; gap:22px; color:#b4c8c0; font-size:.9rem; }} .legend span::before {{ content:""; display:inline-block; width:11px; height:11px; margin-right:7px; background:#64c5a0; border-radius:50%; }} .legend .idea-key::before {{ background:#e6a85b; border-radius:0; transform:rotate(45deg); }}
.unplaced {{ margin-top:56px; border-top:1px solid #304640; padding-top:18px; }} .unplaced summary {{ color:#9eb4ac; cursor:pointer; }} .unplaced ul {{ list-style:none; margin:14px 0 0; padding:0; display:grid; gap:8px; }} .unplaced li {{ display:flex; align-items:center; gap:10px; background:#172320; border:1px solid #304640; border-radius:8px; padding:10px 12px; }} .note-kind,.picker-kind {{ display:inline-flex; align-items:center; flex:0 0 auto; border-radius:999px; padding:3px 8px; font-size:.68rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }} .note-kind.research,.picker-kind.research {{ color:#bff7df; background:#245744; }} .note-kind.idea,.picker-kind.idea {{ color:#ffe0ad; background:#654522; }} a {{ color:#8ee3bf; }} dialog {{ max-width:620px; width:calc(100% - 48px); color:#e7f1ed; background:#172320; border:1px solid #668078; border-radius:14px; padding:26px; font:inherit; }} dialog::backdrop {{ background:#020505bb; }} button {{ font:inherit; }} .close {{ float:right; background:#243a35; color:inherit; border:1px solid #668078; border-radius:6px; padding:2px 8px; font-size:1.2rem; line-height:1.2; cursor:pointer; }} .tag {{ color:#9eb4ac; margin-right:8px; }} .rating {{ border-top:1px solid #304640; padding:12px 0; }} .rating strong {{ color:#8ee3bf; }} .picker-item {{ display:block; width:100%; margin:8px 0; padding:12px 14px; text-align:left; color:inherit; background:#20322e; border:1px solid #46675c; border-radius:8px; cursor:pointer; }} .picker-item:hover,.picker-item:focus-visible {{ background:#2c4940; border-color:#8ee3bf; }} .picker-item small {{ color:#b4c8c0; }} .picker-kind {{ margin-right:8px; }}
@media(max-width:600px) {{ body {{ padding:24px 14px; }} .map {{ height:720px; margin-left:58px; }} .axis-y {{ left:-40px; }} }}
</style></head><body><main><p class="intro">Agentic Runtime Working Group - provisional workshop view</p><h1>Research and Ideas Landscape</h1>
<p class="intro">Recalibrated working-group ratings, shown to seed discussion rather than establish a permanent taxonomy. Click a note for its summary, rating justifications, and source.</p>
<div class="legend"><span>Research</span><span class="idea-key">Idea</span></div>{''.join(matrices)}</main>
<dialog id="detail"><button class="close" aria-label="Close">X</button><div id="content"></div></dialog>
<script>const plots={data};const dialog=document.querySelector('#detail'),content=document.querySelector('#content');document.querySelector('.close').onclick=()=>dialog.close();
function show(note){{const tags=(note.tags||[]).map(t=>`<span class="tag">#${{t}}</span>`).join('');const ratings=Object.entries(note.ratings||{{}}).map(([name,r])=>`<div class="rating"><strong>${{name}}: ${{r.value}}/100</strong><br>${{r.note}}</div>`).join('');content.innerHTML=`<p class="intro">${{note.kind}}</p><h2>${{note.title}}</h2><p>${{note.summary}}</p><p>${{tags}}</p>${{ratings}}<p><a href="${{note.url}}">Read the full Markdown note on GitHub</a></p>`;dialog.showModal()}}
function showCluster(items){{content.innerHTML=`<p class="intro">${{items.length}} notes at this position</p><h2>Select a note</h2>${{items.map((note,i)=>`<button class="picker-item" data-index="${{i}}"><span class="picker-kind ${{note.kind}}">${{note.kind}}</span><strong>${{note.title}}</strong><br><small>${{note.summary}}</small></button>`).join('')}}`;dialog.showModal();content.querySelectorAll('.picker-item').forEach(b=>b.onclick=()=>show(items[Number(b.dataset.index)]))}}
document.querySelectorAll('.marker').forEach(m=>m.onclick=()=>{{if(m.dataset.cluster){{const items=plots[m.dataset.plot].filter(n=>n.position&&`${{n.position.x}}:${{n.position.y}}`===m.dataset.cluster.split(':').slice(1).join(':'));showCluster(items)}}else{{show(plots[m.dataset.plot].find(n=>n.id===m.dataset.id))}}}});dialog.addEventListener('click',e=>{{if(e.target===dialog)dialog.close()}});</script></body></html>'''


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
