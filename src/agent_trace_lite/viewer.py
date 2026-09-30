"""Self-contained static HTML viewer for normalized trace events."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def render_html(events: list[dict[str, Any]], *, title: str = "Agent Trace Lite") -> str:
    """Render events into a dependency-free, local HTML document."""
    # Escape HTML-significant characters so trace text cannot terminate the script element.
    payload = (
        json.dumps(events, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    rows = []
    for event in events:
        data = html.escape(json.dumps(event["data"], ensure_ascii=False, sort_keys=True, indent=2))
        rows.append(
            f'<article class="event" data-type="{html.escape(event["type"])}">'
            f'<div class="marker"></div><div class="meta"><span class="badge">{html.escape(event["type"])}</span>'
            f'<time>{html.escape(event["timestamp"] or "unspecified time")}</time><code>{html.escape(event["id"])}</code></div>'
            f'<details><summary>{html.escape(event["trace_id"])} · sequence {event["sequence"]}</summary><pre>{data}</pre></details></article>'
        )
    body = "\n".join(rows) or '<p class="empty">No events found.</p>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
:root{{--bg:#0e1628;--panel:#17223a;--muted:#9eacc7;--ink:#eef3ff;--accent:#72e0bd;--line:#334362;--danger:#ff8f8f}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#0e1628,#101c32 65%,#142943);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}main{{max-width:1000px;margin:0 auto;padding:48px 24px 80px}}h1{{font-size:clamp(2rem,5vw,4rem);letter-spacing:-.05em;margin:0 0 8px}}.lede{{color:var(--muted);margin:0 0 28px}}.toolbar{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;background:var(--panel);border:1px solid var(--line);padding:14px 16px;border-radius:14px;margin-bottom:28px}}input,button{{font:inherit;border-radius:8px;border:1px solid var(--line);padding:8px 12px;background:#101a2e;color:var(--ink)}}input{{min-width:230px}}button{{cursor:pointer}}.count{{color:var(--muted);margin-left:auto}}.timeline{{position:relative}}.timeline:before{{content:"";position:absolute;left:9px;top:0;bottom:0;width:2px;background:var(--line)}}.event{{position:relative;margin:0 0 16px 32px;padding:16px 18px;background:rgba(23,34,58,.88);border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 30px #060b1450}}.marker{{position:absolute;left:-30px;top:22px;width:12px;height:12px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px var(--bg)}}.meta{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;color:var(--muted);font-size:.85rem}}.badge{{color:#07151a;background:var(--accent);border-radius:99px;padding:2px 9px;font-weight:700;text-transform:uppercase;font-size:.7rem;letter-spacing:.08em}}time{{font-variant-numeric:tabular-nums}}code{{font-family:ui-monospace,SFMono-Regular,monospace}}summary{{cursor:pointer;margin-top:9px;color:var(--ink)}}pre{{overflow:auto;background:#0b1221;border-radius:8px;padding:14px;color:#c7d3ec;font-size:.83rem}}.empty{{color:var(--muted)}}.event[data-type=error] .marker{{background:var(--danger)}}.event[data-type=guardrail] .marker{{background:#ffd27a}}
</style></head><body><main><h1>{html.escape(title)}</h1><p class="lede">Offline, deterministic trace timeline. Secrets are redacted before display.</p>
<div class="toolbar"><label for="filter">Filter events</label><input id="filter" type="search" placeholder="model, tool, error…" autocomplete="off"><span class="count" id="count"></span></div>
<section class="timeline" id="timeline">{body}</section></main><script>
const source={payload};const cards=[...document.querySelectorAll('.event')];const filter=document.querySelector('#filter');const count=document.querySelector('#count');
function update(){{const query=filter.value.trim().toLowerCase();let shown=0;cards.forEach((card,i)=>{{const match=!query||JSON.stringify(source[i]).toLowerCase().includes(query);card.hidden=!match;if(match)shown++}});count.textContent=`${{shown}} / ${{cards.length}} events`}}filter.addEventListener('input',update);update();
</script></body></html>"""


def write_html(events: list[dict[str, Any]], output: str | Path, *, title: str = "Agent Trace Lite") -> Path:
    path = Path(output)
    path.write_text(render_html(events, title=title), encoding="utf-8")
    return path
