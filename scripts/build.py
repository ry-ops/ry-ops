#!/usr/bin/env python3
"""Refresh the generated parts of the profile README.

- assets/stats.svg      stat tiles + language bar, from public GitHub data
- assets/mcp-fleet.svg  the animated `claude mcp list` terminal
- README.md             the BLOG and INVENTORY sections between their markers

Standard library only. Set GITHUB_TOKEN for a higher API rate limit.
Run: python scripts/build.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = "ry-ops"
ORGS = ["m5stack-lab", "git-fabric", "cortex-io"]
SKIP = {"ry-ops/ry-ops"}
FEED = "https://ry-ops.dev/rss.xml"
UA = "Mozilla/5.0 (compatible; ry-ops-profile-refresh; +https://github.com/ry-ops/ry-ops)"

# The MCP servers shown in the terminal (repo, label, blurb).
MCP_SERVERS = [
    ("proxmox-mcp-server", "proxmox", "Proxmox VE · 338 tools · VMs, LXC, Ceph, SDN"),
    ("unifi-mcp-server", "unifi", "UniFi · devices, clients, firewall, WLANs"),
    ("k3s-mcp-server", "k3s", "K3s · kubectl operations for Claude"),
    ("cloudflare-mcp-server", "cloudflare", "Cloudflare · DNS, Workers, zones"),
    ("starlink-enterprise-mcp-server", "starlink", "Starlink Enterprise · terminal fleet"),
    ("microsoft-graph-mcp-server", "microsoft-graph", "Microsoft 365 · users, licenses, groups"),
    ("eagle-scout", "eagle-scout", "Docker Scout · CVE + SBOM scanning"),
    ("qdrant-fabric", "qdrant-fabric", "Qdrant · semantic search for RAG"),
    ("n8n-fabric", "n8n-fabric", "n8n · workflows with vector memory"),
    ("aiana", "aiana", "Claude Code · conversation memory"),
    ("git-steer", "git-steer", "GitHub · autonomous repo management"),
]

# Fallback descriptions for public repos that have none on GitHub.
DESCRIPTIONS = {
    "doomagotchi": "Self-playing DOOM on an M5Stack Tab5 that turns live 2.4 GHz RF into demons",
    "azure-help": "Notes and playbooks for the non-obvious corners of the Azure portal",
    "bloatkill": "Windows storage cleanup reference: a zero-dependency audit dashboard",
}

SECTIONS = [  # (title, predicate)
    ("🔌 MCP servers", lambda r: r["name"] in {s[0] for s in MCP_SERVERS} and r["owner"] == USER),
    ("🔬 Hardware · m5stack-lab", lambda r: r["owner"] == "m5stack-lab"),
    ("🎓 Tutorials", lambda r: "tutorial" in r["topics"]),
    ("🧪 Tools & experiments", lambda r: r["owner"] in (USER, "git-fabric")),
    ("🗄️ Archive · cortex-io", lambda r: r["owner"] == "cortex-io"),
]

# Language groups for the bar, in fixed categorical order (validated palette, dark steps).
LANG_GROUPS = [
    ("Python", {"Python"}, "#3987e5"),
    ("TypeScript", {"TypeScript"}, "#d95926"),
    ("C / C++", {"C", "C++"}, "#199e70"),
    ("JavaScript", {"JavaScript"}, "#c98500"),
    ("Shell", {"Shell"}, "#d55181"),
    ("HTML", {"HTML", "Astro"}, "#008300"),
]
OTHER_COLOR = "#6e7681"

SANS = '"Segoe UI",-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace'


# --- data ------------------------------------------------------------------------

def api(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": UA})
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def repos_of(owner: str, is_org: bool) -> list[dict]:
    out, page = [], 1
    base = f"/orgs/{owner}/repos?type=public" if is_org else f"/users/{owner}/repos?type=owner"
    while True:
        batch = api(f"{base}&per_page=100&page={page}")
        out += batch
        if len(batch) < 100:
            break
        page += 1
    return [{
        "owner": owner, "name": r["name"], "full": r["full_name"], "url": r["html_url"],
        "desc": r["description"] or DESCRIPTIONS.get(r["name"], ""), "stars": r["stargazers_count"],
        "lang": r["language"], "topics": r.get("topics", []), "fork": r["fork"],
        "archived": r["archived"], "pushed": r["pushed_at"],
    } for r in out if not r["private"] and r["full_name"] not in SKIP and r["name"] != ".github"]


def blog_posts(n: int = 5) -> list[tuple[str, str, str]] | None:
    try:
        req = urllib.request.Request(FEED, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            root = ET.fromstring(resp.read())
    except Exception as exc:  # feed unreachable: keep the current list
        print(f"blog feed skipped: {exc}", file=sys.stderr)
        return None
    posts = []
    for item in root.iter("item"):
        title, link, date = (item.findtext(k, "").strip() for k in ("title", "link", "pubDate"))
        try:
            day = parsedate_to_datetime(date).strftime("%b %-d, %Y")
        except (TypeError, ValueError):
            day = ""
        posts.append((title, link, day))
    return posts[:n]


# --- svg -------------------------------------------------------------------------

def stats_svg(repos: list[dict], since: int) -> str:
    stars = sum(r["stars"] for r in repos)
    years = datetime.now(timezone.utc).year - since
    tiles = [(len(repos), "public repos"), (stars, "stars earned"),
             (len(MCP_SERVERS), "MCP servers"), (f"{years} yrs", f"shipping since {since}")]
    W, gap, x0 = 900, 16, 24
    tw = (W - 2 * x0 - 3 * gap) / 4
    out = []
    for i, (num, label) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        out.append(
            f'<rect x="{x:.1f}" y="24" width="{tw:.1f}" height="96" rx="12" fill="#161b22" stroke="#30363d"/>'
            f'<rect x="{x + 18:.1f}" y="40" width="28" height="4" rx="2" fill="#2dd4bf"/>'
            f'<text x="{x + 18:.1f}" y="88" font-family=\'{SANS}\' font-size="36" font-weight="700" fill="#e6edf3" '
            f'class="pop" style="animation-delay:{i * 0.15:.2f}s">{escape(str(num))}</text>'
            f'<text x="{x + 18:.1f}" y="108" font-family=\'{SANS}\' font-size="13" fill="#8b949e">{escape(label)}</text>')

    counts = Counter(r["lang"] for r in repos if r["lang"])
    total = sum(counts.values())
    segs = []
    for name, langs, color in LANG_GROUPS:
        n = sum(counts[l] for l in langs)
        if n:
            segs.append((name, n, color))
    other = total - sum(n for _, n, _ in segs)
    if other:
        segs.append(("Other", other, OTHER_COLOR))
    bx, bw, by, bh = x0, W - 2 * x0, 160, 12
    x, bar, legend, lx = bx, [], [], bx
    for name, n, color in segs:
        w = bw * n / total
        bar.append(f'<rect x="{x:.1f}" y="{by}" width="{max(w - 2, 1):.1f}" height="{bh}" fill="{color}"/>')
        x += w
        pct = round(100 * n / total)
        legend.append(
            f'<rect x="{lx}" y="{by + 26}" width="10" height="10" rx="2" fill="{color}"/>'
            f'<text x="{lx + 16}" y="{by + 35}" font-family=\'{SANS}\' font-size="12.5" fill="#c9d1d9">{escape(name)} '
            f'<tspan fill="#8b949e">{pct}%</tspan></text>')
        lx += 30 + 8 * (len(name) + len(str(pct)) + 2)
    H = by + 56
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">At a glance</title>
  <desc id="d">{len(repos)} public repos, {stars} stars, {len(MCP_SERVERS)} MCP servers, shipping since {since}. Languages by repo: {", ".join(f"{n} {round(100 * c / total)}%" for n, c, _ in segs)}.</desc>
  <defs><clipPath id="bar"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="{bh / 2}"/></clipPath></defs>
  <style>
    .pop{{animation:pop .8s ease-out both}}
    @keyframes pop{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
    @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
  </style>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="#0d1117" stroke="#30363d"/>
  {"".join(out)}
  <text x="{bx}" y="{by - 10}" font-family='{MONO}' font-size="11.5" fill="#8b949e">LANGUAGES · by public repo</text>
  <g clip-path="url(#bar)">{"".join(bar)}</g>
  {"".join(legend)}
</svg>
"""


def fleet_svg() -> str:
    cycle, end, W, y0, dy = 16.0, 14.4, 900, 76, 22
    lines: list[tuple[float | None, str | None]] = [
        (0.2, '<text x="32" y="{y}"><tspan fill="#3fb950">$</tspan> claude mcp list</text>'),
        (1.2, '<text x="32" y="{y}" style="fill:#8b949e">Checking MCP server health…</text>'),
        (None, None),
    ]
    t = 1.9
    for _, label, blurb in MCP_SERVERS:
        lines.append((t, f'<text x="32" y="{{y}}"><tspan fill="#e6edf3">{escape(label)}</tspan>'
                         f'<tspan x="210" fill="#3fb950">✓ connected</tspan>'
                         f'<tspan x="350" fill="#8b949e">{escape(blurb)}</tspan></text>'))
        t += 0.32
    lines += [(None, None),
              (t + 0.4, f'<text x="32" y="{{y}}" style="fill:#2dd4bf">{len(MCP_SERVERS)} servers · all connected</text>'),
              (t + 1.0, '<text x="32" y="{y}"><tspan fill="#3fb950">$</tspan> <tspan class="cur">▋</tspan></text>')]
    H = y0 + dy * (len(lines) - 1) + 30
    css, body = [], []
    for i, (start, text) in enumerate(lines):
        if start is None:
            continue
        a, b = start / cycle * 100, (start + 0.08) / cycle * 100
        c, d = end / cycle * 100, (end + 0.5) / cycle * 100
        css.append(f"@keyframes k{i}{{0%,{a:.2f}%{{opacity:0}}{b:.2f}%,{c:.2f}%{{opacity:1}}{d:.2f}%,100%{{opacity:0}}}}"
                   f".l{i}{{animation:k{i} {cycle}s linear infinite}}")
        body.append(text.replace("<text ", f'<text class="l{i}" ', 1).replace("{y}", str(y0 + dy * i)))
    names = ", ".join(s[1] for s in MCP_SERVERS)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">claude mcp list</title>
  <desc id="d">A terminal listing the {len(MCP_SERVERS)} MCP servers built by ry-ops: {names}.</desc>
  <style>
    text{{font-family:{MONO};font-size:14px;fill:#c9d1d9}}
    .title{{font-size:12px;fill:#8b949e}}
    .cur{{fill:#2dd4bf;animation:blink 1s steps(1) infinite}}
    @keyframes blink{{50%{{opacity:0}}}}
    {"".join(css)}
    @media (prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important}}}}
  </style>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="#0d1117" stroke="#30363d"/>
  <path d="M1 15A14 14 0 0 1 15 1H{W - 15}A14 14 0 0 1 {W - 1} 15V40H1Z" fill="#161b22"/>
  <line x1="1" y1="40" x2="{W - 1}" y2="40" stroke="#30363d"/>
  <circle cx="24" cy="21" r="6" fill="#ff5f57"/><circle cx="44" cy="21" r="6" fill="#febc2e"/><circle cx="64" cy="21" r="6" fill="#28c840"/>
  <text x="{W // 2}" y="25" text-anchor="middle" class="title">ry-ops@homelab — zsh — claude mcp list</text>
  {(chr(10) + "  ").join(body)}
</svg>
"""


# --- readme ----------------------------------------------------------------------

def row(r: dict) -> str:
    name = r["name"] if r["owner"] == USER else r["full"]
    desc = r["desc"].replace("|", "\\|") + (" <sub>(fork)</sub>" if r["fork"] else "")
    return f'| [{name}]({r["url"]}) | {desc} | {r["stars"]} |'


def inventory_md(repos: list[dict]) -> str:
    left = sorted(repos, key=lambda r: (-r["stars"], r["name"].lower()))
    parts = []
    for title, pred in SECTIONS:
        group = [r for r in left if pred(r)]
        left = [r for r in left if r not in group]
        if not group:
            continue
        rows = "\n".join(row(r) for r in group)
        parts.append(f"**{title}**\n\n| Repo | What it is | ★ |\n|---|---|--:|\n{rows}")
    return "\n\n".join(parts)


def blog_md(posts: list[tuple[str, str, str]]) -> str:
    return "\n".join(f"- [{t}]({l}) <sub>· {d}</sub>" for t, l, d in posts)


def replace_section(text: str, name: str, body: str) -> str:
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise SystemExit(f"README is missing the {name} markers")
    return pattern.sub(lambda _: f"{start}\n{body}\n{end}", text)


def main() -> None:
    user = api(f"/users/{USER}")
    repos = repos_of(USER, False)
    for org in ORGS:
        repos += repos_of(org, True)
    since = int(user["created_at"][:4])

    (ROOT / "assets" / "stats.svg").write_text(stats_svg(repos, since))
    (ROOT / "assets" / "mcp-fleet.svg").write_text(fleet_svg())

    readme = ROOT / "README.md"
    text = readme.read_text()
    text = replace_section(text, "INVENTORY", inventory_md(repos))
    posts = blog_posts()
    if posts:
        text = replace_section(text, "BLOG", blog_md(posts))
    readme.write_text(text)
    print(f"{len(repos)} public repos, {sum(r['stars'] for r in repos)} stars, "
          f"{len(posts) if posts else 'no'} blog posts")


if __name__ == "__main__":
    main()
