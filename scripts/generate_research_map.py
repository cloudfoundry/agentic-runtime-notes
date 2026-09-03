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
FOCUS_USE_CASES_PATH = ROOT / "scripts" / "focus_use_cases.yaml"
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

    if len(primitives) != 3:
        raise ValueError("primitive configuration must contain exactly 3 initial primitives")
    return primitives


def load_primitives() -> list[dict]:
    primitives = yaml.safe_load(PRIMITIVES_PATH.read_text(encoding="utf-8"))
    known_paths = {note.path.as_posix() for note in load_notes()}
    return validate_primitives(primitives, known_paths)


def validate_focus_use_cases(
    use_cases: object, known_paths: set[str], primitive_ids: set[str]
) -> list[dict]:
    if not isinstance(use_cases, list) or len(use_cases) != 2:
        raise ValueError("focus use case configuration must contain exactly 2 entries")

    required_ids = {
        "cf-hosted-coding-harnesses",
        "user-facing-agentic-applications",
    }
    string_fields = (
        "id",
        "title",
        "workshop_outcome",
        "primary_actor",
        "beneficiary",
        "lifecycle",
        "authority_boundary",
        "failure_domain",
        "poc",
    )
    list_fields = ("unique_capabilities", "rfc_decisions")
    allowed_applicability = {"core", "conditional", "supporting"}
    seen_ids = set()
    for use_case in use_cases:
        if not isinstance(use_case, dict):
            raise ValueError("each focus use case must be a mapping")
        for field in string_fields:
            if not isinstance(use_case.get(field), str) or not use_case[field].strip():
                raise ValueError(f"focus use case requires a non-empty '{field}'")
        for field in list_fields:
            values = use_case.get(field)
            if (
                not isinstance(values, list)
                or not values
                or any(not isinstance(value, str) or not value.strip() for value in values)
            ):
                raise ValueError(f"focus use case requires a non-empty '{field}' list of strings")

        use_case_id = use_case["id"]
        if use_case_id in seen_ids:
            raise ValueError(f"duplicate focus use case id: {use_case_id}")
        seen_ids.add(use_case_id)

        core = use_case.get("core")
        supporting = use_case.get("supporting")
        if not isinstance(core, list) or not core:
            raise ValueError(f"focus use case '{use_case_id}' requires non-empty core membership")
        if not isinstance(supporting, list):
            raise ValueError(f"focus use case '{use_case_id}' supporting membership must be a list")
        memberships = core + supporting
        if any(not isinstance(path, str) or not path.strip() for path in memberships):
            raise ValueError(f"focus use case '{use_case_id}' note paths must be non-empty strings")
        if len(memberships) != len(set(memberships)):
            raise ValueError(f"focus use case '{use_case_id}' has a duplicate note path")
        for path in memberships:
            if path not in known_paths:
                raise ValueError(f"focus use case '{use_case_id}' references unknown note path: {path}")

        applicability = use_case.get("primitive_applicability")
        if not isinstance(applicability, dict) or set(applicability) != primitive_ids:
            raise ValueError(
                f"focus use case '{use_case_id}' primitive applicability must contain exactly the known primitive ids"
            )
        for primitive_id, value in applicability.items():
            if value not in allowed_applicability:
                raise ValueError(
                    f"focus use case '{use_case_id}' has invalid applicability '{value}' for primitive '{primitive_id}'"
                )

    if seen_ids != required_ids:
        raise ValueError("focus use case configuration must contain the approved focus use case ids")
    return use_cases


def load_focus_use_cases() -> list[dict]:
    use_cases = yaml.safe_load(FOCUS_USE_CASES_PATH.read_text(encoding="utf-8"))
    known_paths = {note.path.as_posix() for note in load_notes()}
    primitive_ids = {primitive["id"] for primitive in load_primitives()}
    return validate_focus_use_cases(use_cases, known_paths, primitive_ids)


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


def generate_html(notes: list[Note], plots: dict, primitives: list[dict]) -> str:
    plot_payloads = {plot_id: [note_payload(note, plot) for note in notes] for plot_id, plot in plots.items()}
    data = json.dumps(plot_payloads, ensure_ascii=True).replace("</", "<\\/")
    primitive_memberships = {}
    for primitive in primitives:
        for relationship in ("core", "supporting"):
            for path in primitive[relationship]:
                primitive_memberships.setdefault(path, {})[primitive["id"]] = relationship
    membership_data = json.dumps(primitive_memberships, ensure_ascii=True).replace("</", "<\\/")
    note_titles = {note.path.as_posix(): note.title for note in notes}
    accents = ("#68d5ac", "#f1b866", "#8eb8ff")
    cards = []
    for primitive, accent in zip(primitives, accents):
        primitive_id = html.escape(primitive["id"])
        memberships = []
        for relationship in ("core", "supporting"):
            links = "".join(
                f'<li><a href="{html.escape(github_url(pathlib.Path(path)))}">{html.escape(note_titles.get(path, pathlib.Path(path).stem.replace("-", " ").title()))}</a></li>'
                for path in primitive[relationship]
            )
            memberships.append(f'<section><h4>{relationship.title()}</h4><ul>{links}</ul></section>')
        cards.append(f'''<article class="primitive-card" style="--primitive-accent:{accent}">
<button id="primitive-{primitive_id}" class="primitive-select" type="button" data-primitive="{primitive_id}" aria-pressed="false"><span class="primitive-title">{html.escape(primitive["title"])}</span><span>{html.escape(primitive["proposition"])}</span><span class="strategic-decision"><strong>Strategic decision:</strong> {html.escape(primitive["strategic_decision"])}</span></button>
<details class="primitive-details"><summary>Gap, experiments, and evidence</summary><dl><dt>Current CF gap</dt><dd>{html.escape(primitive["cf_gap"])}</dd><dt>Candidate POC</dt><dd>{html.escape(primitive["poc"])}</dd><dt>Candidate RFC scope</dt><dd>{html.escape(primitive["rfc_scope"])}</dd></dl><div class="primitive-links">{''.join(memberships)}</div></details></article>''')
    matrices = []
    tabs = []
    for index, (plot_id, plot) in enumerate(plots.items()):
        payload = plot_payloads[plot_id]
        markers = []
        unplaced = []
        for key, group in group_payload(payload).items():
            p = group[0]["position"]
            if len(group) == 1:
                item = group[0]
                markers.append(
                    f'<button class="marker {html.escape(item["kind"])}" style="left:{p["x"]}%;bottom:{p["y"]}%" data-plot="{html.escape(plot_id)}" data-id="{html.escape(item["id"])}" aria-label="{html.escape(item["title"])}"></button>'
                )
            else:
                cluster_id = f"{plot_id}-cluster-{len(markers)}"
                note_ids = html.escape(json.dumps([item["id"] for item in group]), quote=True)
                markers.append(
                    f'<button class="marker cluster" style="left:{p["x"]}%;bottom:{p["y"]}%" data-plot="{html.escape(plot_id)}" data-cluster="{html.escape(cluster_id)}" data-note-ids="{note_ids}" aria-label="{len(group)} notes at this position">{len(group)}</button>'
                )
        for item in payload:
            if item["position"] is None:
                label = "Research" if item["kind"] == "research" else "Idea"
                escaped_kind = html.escape(item["kind"])
                unplaced.append(f'<li><span class="note-kind {escaped_kind}"><span class="note-type {escaped_kind}">{label}</span></span><a href="{html.escape(item["url"])}">{html.escape(item["title"])}</a></li>')
        title = html.escape(plot["title"])
        x = plot["x"]
        y = plot["y"]
        selected = "true" if index == 0 else "false"
        tab_index = "0" if index == 0 else "-1"
        hidden = "" if index == 0 else " hidden"
        escaped_plot_id = html.escape(plot_id)
        tabs.append(f'<button id="tab-{escaped_plot_id}" role="tab" aria-selected="{selected}" tabindex="{tab_index}" aria-controls="panel-{escaped_plot_id}" type="button">{title}</button>')
        matrices.append(f'''<section id="panel-{escaped_plot_id}" class="matrix" role="tabpanel" aria-labelledby="tab-{escaped_plot_id}"{hidden}><h2>{title}</h2><div class="map" aria-label="{title}">{''.join(markers)}<span class="axis-x">{html.escape(x["low"])} &lt; {html.escape(x["label"])} &gt; {html.escape(x["high"])}</span><span class="axis-y">{html.escape(y["low"])} &lt; {html.escape(y["label"])} &gt; {html.escape(y["high"])}</span></div><details class="unplaced"><summary>Unplaced notes ({len(unplaced)})</summary><ul>{''.join(unplaced) or '<li>All notes are placed.</li>'}</ul></details></section>''')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Research and Ideas Landscape</title><style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:#101619; color:#e7f1ed; }}
body {{ max-width:1200px; margin:0 auto; padding:36px 24px; }} h1 {{ font-size:clamp(2rem,5vw,4rem); margin:0 0 8px; }}
.intro {{ color:#9eb4ac; max-width:760px; line-height:1.5; }} .map {{ position:relative; height:620px; margin:34px 42px 20px 90px; border-left:1px solid #668078; border-bottom:1px solid #668078; background:linear-gradient(90deg,transparent 49.9%,#243a35 50%,transparent 50.1%),linear-gradient(0deg,transparent 49.9%,#243a35 50%,transparent 50.1%); }}
.primitive-heading {{ margin-top:44px; }} .primitive-actions {{ display:flex; justify-content:flex-end; margin-bottom:12px; }} .show-all {{ color:#bff7df; background:#1b302b; border:1px solid #46675c; border-radius:999px; padding:8px 16px; cursor:pointer; }} .show-all:hover,.show-all:focus-visible {{ border-color:#8ee3bf; background:#24433a; }} .primitive-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }} .primitive-card {{ min-width:0; background:#15211e; border:1px solid #304640; border-top:3px solid var(--primitive-accent); border-radius:12px; overflow:hidden; }} .primitive-select {{ display:flex; flex-direction:column; gap:12px; width:100%; min-height:100%; padding:20px; color:inherit; background:#172723; border:0; text-align:left; cursor:pointer; }} .primitive-select:hover,.primitive-select:focus-visible,.primitive-select[aria-pressed="true"] {{ background:#203630; box-shadow:inset 0 0 0 1px var(--primitive-accent); }} .primitive-title {{ color:var(--primitive-accent); font-size:1.15rem; font-weight:800; line-height:1.25; }} .strategic-decision {{ margin-top:auto; color:#c8d8d2; }} .primitive-details {{ border-top:1px solid #304640; padding:14px 20px 18px; }} .primitive-details summary {{ color:var(--primitive-accent); cursor:pointer; font-weight:700; }} .primitive-details dl {{ margin-bottom:0; }} .primitive-details dt {{ margin-top:14px; color:#b4c8c0; font-weight:700; }} .primitive-details dd {{ margin:4px 0 0; color:#d5e3de; line-height:1.45; }} .primitive-links {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }} .primitive-links ul {{ margin:8px 0 0; padding-left:18px; }} .primitive-links li {{ margin:6px 0; }} .matrix-tabs {{ display:flex; gap:8px; margin-top:44px; padding:4px; overflow-x:auto; scrollbar-color:#46675c #15211e; }} .matrix-tabs [role="tab"] {{ flex:0 0 auto; color:#b4c8c0; background:#172723; border:1px solid #304640; border-radius:8px; padding:10px 14px; cursor:pointer; }} .matrix-tabs [role="tab"]:hover,.matrix-tabs [role="tab"]:focus-visible {{ color:#e7f1ed; border-color:#668078; background:#203630; }} .matrix-tabs [aria-selected="true"] {{ color:#10201b; background:#8ee3bf; border-color:#8ee3bf; font-weight:800; }} .matrix[hidden] {{ display:none; }} .matrix {{ margin-top:28px; }} .axis-x,.axis-y {{ position:absolute; color:#9eb4ac; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; }} .axis-x {{ left:0; right:0; bottom:-34px; text-align:center; }} .axis-y {{ writing-mode:vertical-rl; transform:rotate(180deg) translateY(50%); left:-52px; top:50%; text-align:center; white-space:nowrap; }}
.marker {{ position:absolute; transform:translate(-50%,50%); width:18px; height:18px; border:2px solid #d9fff0; cursor:pointer; transition:opacity .15s,box-shadow .15s,border-color .15s; }} .marker.research {{ border-radius:50%; background:#64c5a0; }} .marker.idea {{ transform:translate(-50%,50%) rotate(45deg); background:#e6a85b; }} .marker.cluster {{ transform:translate(-50%,50%); width:30px; height:30px; border-radius:50%; background:#d9fff0; color:#10201b; font-weight:800; }} .marker.related {{ border-color:var(--selected-accent); box-shadow:0 0 0 4px color-mix(in srgb,var(--selected-accent) 35%,transparent); }} .marker.cluster.related {{ background:var(--selected-accent); }} .marker.dimmed {{ opacity:.22; }} .marker.dimmed:focus-visible {{ opacity:1; outline:3px solid #fff; outline-offset:3px; }}
.legend {{ display:flex; gap:22px; color:#b4c8c0; font-size:.9rem; }} .legend span::before {{ content:""; display:inline-block; width:11px; height:11px; margin-right:7px; background:#64c5a0; border-radius:50%; }} .legend .idea-key::before {{ background:#e6a85b; border-radius:0; transform:rotate(45deg); }}
.unplaced {{ margin-top:56px; border-top:1px solid #304640; padding-top:18px; }} .unplaced summary {{ color:#9eb4ac; cursor:pointer; }} .unplaced ul {{ list-style:none; margin:14px 0 0; padding:0; display:grid; gap:8px; }} .unplaced li {{ display:flex; align-items:center; gap:10px; background:#172320; border:1px solid #304640; border-radius:8px; padding:10px 12px; }} .note-kind,.picker-kind {{ display:inline-flex; align-items:center; flex:0 0 auto; border-radius:999px; padding:3px 8px; font-size:.68rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }} .note-kind.research,.picker-kind.research {{ color:#bff7df; background:#245744; }} .note-kind.idea,.picker-kind.idea {{ color:#ffe0ad; background:#654522; }} a {{ color:#8ee3bf; }} dialog {{ max-width:620px; width:calc(100% - 48px); color:#e7f1ed; background:#172320; border:1px solid #668078; border-radius:14px; padding:26px; font:inherit; }} dialog::backdrop {{ background:#020505bb; }} button {{ font:inherit; }} .close {{ float:right; background:#243a35; color:inherit; border:1px solid #668078; border-radius:6px; padding:2px 8px; font-size:1.2rem; line-height:1.2; cursor:pointer; }} .tag {{ color:#9eb4ac; margin-right:8px; }} .primitive-badge {{ display:inline-block; margin-left:8px; padding:3px 8px; color:#101619; background:var(--selected-accent); border-radius:999px; font-size:.72rem; font-weight:800; text-transform:uppercase; }} .rating {{ border-top:1px solid #304640; padding:12px 0; }} .rating strong {{ color:#8ee3bf; }} .picker-item {{ display:block; width:100%; margin:8px 0; padding:12px 14px; text-align:left; color:inherit; background:#20322e; border:1px solid #46675c; border-radius:8px; cursor:pointer; }} .picker-item:hover,.picker-item:focus-visible {{ background:#2c4940; border-color:#8ee3bf; }} .picker-item small {{ color:#b4c8c0; }} .picker-kind {{ margin-right:8px; }}
@media(max-width:800px) {{ .primitive-grid {{ grid-template-columns:1fr; }} .primitive-select {{ min-height:0; }} }}
@media(max-width:600px) {{ body {{ padding:24px 14px; }} .primitive-links {{ grid-template-columns:1fr; gap:0; }} .matrix-tabs {{ margin-left:-14px; margin-right:-14px; padding-left:14px; padding-right:14px; }} .map {{ height:720px; margin-left:58px; }} .axis-y {{ left:-40px; }} }}
</style></head><body><main><p class="intro">Agentic Runtime Working Group - provisional workshop view</p><h1>Research and Ideas Landscape</h1>
<p class="intro">Recalibrated working-group ratings, shown to seed discussion rather than establish a permanent taxonomy. Click a note for its summary, rating justifications, and source.</p>
<div class="legend"><span>Research</span><span class="idea-key">Idea</span></div><h2 class="primitive-heading">Candidate platform primitives</h2><div class="primitive-actions"><button class="show-all" type="button">Show all</button></div><div class="primitive-grid">{''.join(cards)}</div><div class="matrix-tabs" role="tablist" aria-label="Rating matrices">{''.join(tabs)}</div>{''.join(matrices)}</main>
<dialog id="detail" aria-labelledby="dialog-title"><button class="close" aria-label="Close">X</button><div id="content"></div></dialog>
<script>const plots={data};const primitiveMemberships={membership_data};const dialog=document.querySelector('#detail'),content=document.querySelector('#content');let selectedPrimitive=null;document.querySelector('.close').onclick=()=>dialog.close();
 function escapeHtml(value){{return String(value).replace(/[&<>"']/g,character=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[character]))}}
 function updateMarkers(){{document.querySelectorAll('.marker').forEach(m=>{{if(m.dataset.noteIds){{const noteIds=JSON.parse(m.dataset.noteIds);const relatedCount=noteIds.filter(id=>selectedPrimitive&&primitiveMemberships[id]?.[selectedPrimitive]).length;m.textContent=relatedCount?`${{relatedCount}}/${{noteIds.length}}`:String(noteIds.length);m.setAttribute('aria-label',relatedCount?`${{relatedCount}} of ${{noteIds.length}} related notes at this position`:`${{noteIds.length}} notes at this position`);m.classList.toggle('related',relatedCount>0);m.classList.toggle('dimmed',Boolean(selectedPrimitive&&!relatedCount))}}else{{const related=Boolean(selectedPrimitive&&primitiveMemberships[m.dataset.id]?.[selectedPrimitive]);m.classList.toggle('related',related);m.classList.toggle('dimmed',Boolean(selectedPrimitive&&!related))}}}})}}
 function updatePrimitiveControls(){{document.querySelectorAll('.primitive-select').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.primitive===selectedPrimitive)))}}
 function selectPrimitive(button){{selectedPrimitive=selectedPrimitive===button.dataset.primitive?null:button.dataset.primitive;if(selectedPrimitive)document.documentElement.style.setProperty('--selected-accent',button.closest('.primitive-card').style.getPropertyValue('--primitive-accent'));updatePrimitiveControls();updateMarkers()}}
 function clearPrimitiveSelection(){{selectedPrimitive=null;updatePrimitiveControls();updateMarkers()}}
function relationshipBadge(note){{const relationship=selectedPrimitive&&primitiveMemberships[note.id]?.[selectedPrimitive];return relationship?`<span class="primitive-badge">${{relationship==='core'?'Core':'Supporting'}}</span>`:''}}
 function show(note){{const tags=(note.tags||[]).map(t=>`<span class="tag">#${{escapeHtml(t)}}</span>`).join('');const ratings=Object.entries(note.ratings||{{}}).map(([name,r])=>`<div class="rating"><strong>${{escapeHtml(name)}}: ${{escapeHtml(r.value)}}/100</strong><br>${{escapeHtml(r.note)}}</div>`).join('');content.innerHTML=`<p class="intro">${{escapeHtml(note.kind)}}${{relationshipBadge(note)}}</p><h2 id="dialog-title">${{escapeHtml(note.title)}}</h2><p>${{escapeHtml(note.summary)}}</p><p>${{tags}}</p>${{ratings}}<p><a href="${{escapeHtml(note.url)}}">Read the full Markdown note on GitHub</a></p>`;dialog.showModal()}}
 function showCluster(items){{const isRelated=note=>Boolean(primitiveMemberships[note.id]?.[selectedPrimitive]);const ordered=selectedPrimitive?[...items.filter(isRelated),...items.filter(note=>!isRelated(note))]:[...items];content.innerHTML=`<p class="intro">${{ordered.length}} notes at this position</p><h2 id="dialog-title">Select a note</h2>${{ordered.map((note,i)=>`<button class="picker-item" data-index="${{i}}"><span class="picker-kind ${{escapeHtml(note.kind)}}">${{escapeHtml(note.kind)}}</span><strong>${{escapeHtml(note.title)}}</strong>${{relationshipBadge(note)}}<br><small>${{escapeHtml(note.summary)}}</small></button>`).join('')}}`;dialog.showModal();content.querySelectorAll('.picker-item').forEach(b=>b.onclick=()=>show(ordered[Number(b.dataset.index)]))}}
 function activateTab(index){{tabs.forEach((tab,i)=>{{const selected=i===index;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1;panels[i].hidden=!selected}});tabs[index].focus();updateMarkers()}}
 function handleTabKey(event,index){{let next;switch(event.key){{case 'ArrowLeft':next=(index-1+tabs.length)%tabs.length;break;case 'ArrowRight':next=(index+1)%tabs.length;break;case 'Home':next=0;break;case 'End':next=tabs.length-1;break;default:return}}event.preventDefault();activateTab(next)}}
 const tabs=[...document.querySelectorAll('[role="tab"]')],panels=tabs.map(tab=>document.querySelector(`#${{tab.getAttribute('aria-controls')}}`));tabs.forEach((tab,index)=>{{tab.onclick=()=>activateTab(index);tab.onkeydown=event=>handleTabKey(event,index)}});document.querySelectorAll('.primitive-select').forEach(button=>button.onclick=()=>selectPrimitive(button));document.querySelector('.show-all').onclick=clearPrimitiveSelection;document.querySelectorAll('.marker').forEach(m=>m.onclick=()=>{{if(m.dataset.cluster){{const noteIds=JSON.parse(m.dataset.noteIds);const items=noteIds.map(id=>plots[m.dataset.plot].find(note=>note.id===id));showCluster(items)}}else{{show(plots[m.dataset.plot].find(n=>n.id===m.dataset.id))}}}});dialog.addEventListener('click',e=>{{if(e.target===dialog)dialog.close()}});dialog.addEventListener('keydown',e=>{{if(e.key==='Escape')dialog.close()}});</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        output = generate_html(load_notes(), load_plots(), load_primitives())
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
