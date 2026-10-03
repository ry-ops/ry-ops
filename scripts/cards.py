#!/usr/bin/env python3
"""Generate the animated project cards in assets/cards/.

Each card is a self-contained SVG: a shared frame (name, description, language,
tags) plus a small hand-drawn animation on the right. Edit CARDS to change copy.
"""

from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "cards"
W, H = 430, 180

LANG_COLOR = {"Python": "#3572A5", "TypeScript": "#3178c6", "Go": "#00ADD8", "HTML": "#e34c26"}

# Illustrations live in a 120x140 box whose top-left corner is (296, 20).
ART = {
    "rack": """
  <g transform="translate(306 28)">
    <rect width="100" height="124" rx="8" fill="#161b22" stroke="#30363d"/>
    {units}
  </g>""",
    "wifi": """
  <g transform="translate(356 112)" fill="none" stroke="#58a6ff" stroke-linecap="round" stroke-width="4">
    <path class="wave w1" d="M-22 -14A30 30 0 0 1 22 -14"/>
    <path class="wave w2" d="M-36 -28A50 50 0 0 1 36 -28"/>
    <path class="wave w3" d="M-50 -42A70 70 0 0 1 50 -42"/>
  </g>
  <ellipse cx="356" cy="128" rx="34" ry="11" fill="#161b22" stroke="#30363d"/>
  <ellipse class="pulse" cx="356" cy="126" rx="10" ry="3.5" fill="#58a6ff"/>""",
    "hats": """
  <g transform="translate(300 28)">
    <rect width="112" height="58" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="10" y="22" class="mono" font-size="11" fill="#3fb950">&gt; recon</text>
    <text x="10" y="37" class="mono" font-size="11" fill="#3fb950">&gt; exploit</text>
    <text x="10" y="52" class="mono" font-size="11" fill="#3fb950">&gt; report<tspan class="blink">_</tspan></text>
    <g class="hat h1" transform="translate(8 82)"><path d="M6 20h28M10 20c0-14 4-18 10-18s10 4 10 18" fill="#e6edf3" stroke="#e6edf3" stroke-width="3" stroke-linejoin="round"/></g>
    <g class="hat h2" transform="translate(38 82)"><path d="M6 20h28M10 20c0-14 4-18 10-18s10 4 10 18" fill="#8b949e" stroke="#8b949e" stroke-width="3" stroke-linejoin="round"/></g>
    <g class="hat h3" transform="translate(68 82)"><path d="M6 20h28M10 20c0-14 4-18 10-18s10 4 10 18" fill="#0d1117" stroke="#6e7681" stroke-width="3" stroke-linejoin="round"/></g>
  </g>""",
    "graph": """
  <g transform="translate(316 26)" fill="none" stroke-width="3" stroke-linecap="round">
    <path d="M20 4V124" stroke="#30363d"/>
    <path class="draw" d="M20 40C20 58 72 52 72 70S20 82 20 100" stroke="#a371f7"/>
    <circle cx="20" cy="12" r="6" fill="#0d1117" stroke="#8b949e"/>
    <circle cx="20" cy="40" r="6" fill="#0d1117" stroke="#8b949e"/>
    <circle class="pop p1" cx="72" cy="70" r="6" fill="#0d1117" stroke="#a371f7"/>
    <circle class="pop p2" cx="20" cy="100" r="7" fill="#a371f7" stroke="#a371f7"/>
    <circle cx="20" cy="124" r="6" fill="#0d1117" stroke="#8b949e"/>
  </g>""",
    "pods": """
  <g transform="translate(356 92)">
    <path class="spin" d="M0-50L43-25V25L0 50-43 25V-25Z" fill="none" stroke="#e3b341" stroke-width="2" stroke-dasharray="8 6"/>
    <circle r="14" fill="#161b22" stroke="#e3b341" stroke-width="2"/>
    <text y="5" text-anchor="middle" class="mono" font-size="12" font-weight="700" fill="#e3b341">k3s</text>
    {pods}
  </g>""",
    "memory": """
  <g transform="translate(300 24)">
    <path id="mp" d="M14 30L54 14L98 40L70 78L102 114L44 120L20 82L54 14M70 78L20 82" fill="none" stroke="#30363d" stroke-width="2"/>
    <g fill="#161b22" stroke="#db61a2" stroke-width="2">
      <circle cx="14" cy="30" r="6"/><circle cx="54" cy="14" r="6"/><circle cx="98" cy="40" r="6"/>
      <circle cx="70" cy="78" r="8"/><circle cx="102" cy="114" r="6"/><circle cx="44" cy="120" r="6"/><circle cx="20" cy="82" r="6"/>
    </g>
    <circle class="pkt" r="4" fill="#db61a2"><animateMotion dur="6s" repeatCount="indefinite"><mpath href="#mp"/></animateMotion></circle>
  </g>""",
    "stack": """
  <g transform="translate(306 30)">
    <g class="layer s4"><rect y="0" width="100" height="24" rx="5" fill="#161b22" stroke="#2dd4bf"/><text x="50" y="16" text-anchor="middle" class="mono" font-size="10" fill="#2dd4bf">grafana</text></g>
    <g class="layer s3"><rect y="32" width="100" height="24" rx="5" fill="#161b22" stroke="#2dd4bf"/><text x="50" y="48" text-anchor="middle" class="mono" font-size="10" fill="#2dd4bf">prometheus</text></g>
    <g class="layer s2"><rect y="64" width="100" height="24" rx="5" fill="#161b22" stroke="#2dd4bf"/><text x="50" y="80" text-anchor="middle" class="mono" font-size="10" fill="#2dd4bf">k3s / k3d</text></g>
    <g><rect y="96" width="100" height="24" rx="5" fill="#2dd4bf" fill-opacity=".15" stroke="#2dd4bf"/><text x="50" y="112" text-anchor="middle" class="mono" font-size="10" fill="#2dd4bf">bare metal</text></g>
  </g>""",
    "gauge": """
  <g transform="translate(356 108)">
    <path d="M-52 0A52 52 0 0 1 52 0" fill="none" stroke="#30363d" stroke-width="10" stroke-linecap="round"/>
    <path d="M-52 0A52 52 0 0 1 52 0" fill="none" stroke="#79c0ff" stroke-width="10" stroke-linecap="round" stroke-dasharray="163" class="arc"/>
    <g class="needle"><path d="M0 0L-3-2 0-44 3-2Z" fill="#e6edf3"/></g>
    <circle r="6" fill="#e6edf3"/>
    <text y="30" text-anchor="middle" class="mono" font-size="12" fill="#8b949e">service due</text>
  </g>""",
}

CSS_ART = {
    "rack": ".led{animation:led 1.6s steps(1) infinite}@keyframes led{50%{opacity:.2}}",
    "wifi": ".wave{opacity:.15;animation:wave 2.4s ease-in-out infinite}.w2{animation-delay:.3s}.w3{animation-delay:.6s}"
            "@keyframes wave{0%,100%{opacity:.15}40%{opacity:1}}"
            ".pulse{animation:wave 2.4s ease-in-out infinite}",
    "hats": ".hat{opacity:.35;animation:hat 4.5s infinite}.h2{animation-delay:1.5s}.h3{animation-delay:3s}"
            "@keyframes hat{0%,33%{opacity:1}34%,100%{opacity:.35}}"
            ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
    "graph": ".draw{stroke-dasharray:120;stroke-dashoffset:120;animation:draw 4s ease-in-out infinite}"
             "@keyframes draw{0%{stroke-dashoffset:120}50%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:0;opacity:0}}"
             ".pop{opacity:0;animation:pop 4s infinite}.p1{animation-delay:.6s}.p2{animation-delay:1.6s}"
             "@keyframes pop{0%{opacity:0}10%,70%{opacity:1}85%,100%{opacity:0}}",
    "pods": ".spin{transform-origin:0 0;animation:spin 18s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
            ".pod{animation:pod 3s ease-in-out infinite}@keyframes pod{0%,100%{opacity:.35}50%{opacity:1}}",
    "memory": "",
    "stack": ".layer{animation:drop 6s ease-out infinite}.s3{animation-delay:.4s}.s4{animation-delay:.8s}"
             "@keyframes drop{0%{transform:translateY(-30px);opacity:0}12%,80%{transform:none;opacity:1}92%,100%{opacity:0}}",
    "gauge": ".needle{animation:sweep 5s ease-in-out infinite}"
             "@keyframes sweep{0%,100%{transform:rotate(-80deg)}50%{transform:rotate(55deg)}}"
             ".arc{stroke-dashoffset:163;animation:fill 5s ease-in-out infinite}"
             "@keyframes fill{0%,100%{stroke-dashoffset:163}50%{stroke-dashoffset:25}}",
}

CARDS = [
    ("proxmox-mcp-server", "#f0883e", "Python", "rack", "MCP · Proxmox VE",
     ["338 tools for Proxmox VE: VMs, LXC,", "storage, Ceph, SDN and firewall,", "plus a read-only mode for safe use."]),
    ("unifi-mcp-server", "#58a6ff", "Python", "wifi", "MCP · UniFi",
     ["UniFi monitoring and management", "for Claude: devices, clients, firewall,", "WLANs and agent-to-agent (A2A)."]),
    ("mr-robot", "#3fb950", "Python", "hats", "Kali · HackTheBox",
     ["ADR-driven security framework for", "Kali: a HackTheBox co-pilot running", "hat-persona Claude agents."]),
    ("git-steer", "#a371f7", "TypeScript", "graph", "MCP · GitHub",
     ["Self-hosting GitHub autonomy engine:", "repos, branches, security and Actions", "through MCP, rate-limit hardened."]),
    ("k3s-mcp-server", "#e3b341", "Python", "pods", "MCP · Kubernetes",
     ["kubectl for Claude: run K3s cluster", "operations through MCP, from pods", "and deployments to nodes and logs."]),
    ("aiana", "#db61a2", "Python", "memory", "MCP · Claude Code",
     ["Conversation memory for Claude Code:", "records sessions, embeds them as", "vectors, injects relevant context."]),
    ("stackforge", "#2dd4bf", "HTML", "stack", "homelab · k3s",
     ["Guided homelab bootstrapper: k3s on", "bare metal or k3d on Docker Desktop,", "with Grafana and Prometheus ready."]),
    ("DriveIQ", "#79c0ff", "Python", "gauge", "FastAPI · RAG",
     ["Vehicle maintenance tracking with", "service reminders, CARFAX import and", "RAG over your owner's manual."]),
]


def art(kind: str, accent: str) -> str:
    snippet = ART[kind]
    if kind == "rack":
        units = []
        for i in range(4):
            y = 10 + i * 28
            leds = "".join(
                f'<circle class="led" cx="{70 + j * 9}" cy="{y + 11}" r="2.6" fill="{c}" '
                f'style="animation-delay:{(i * 3 + j) * 0.23:.2f}s"/>'
                for j, c in enumerate([accent, "#3fb950", accent]))
            units.append(f'<rect x="8" y="{y}" width="84" height="22" rx="4" fill="#0d1117" stroke="#30363d"/>'
                         f'<rect x="16" y="{y + 8}" width="34" height="6" rx="3" fill="#30363d"/>{leds}')
        snippet = snippet.format(units="\n    ".join(units))
    if kind == "pods":
        import math
        pods = []
        for i in range(6):
            a = math.radians(i * 60 - 90)
            pods.append(f'<circle class="pod" cx="{32 * math.cos(a):.1f}" cy="{32 * math.sin(a):.1f}" r="6" '
                        f'fill="#e3b341" style="animation-delay:{i * 0.5}s"/>')
        snippet = snippet.format(pods="\n    ".join(pods))
    return snippet


def card(name, accent, lang, kind, tags, desc) -> str:
    lines = "\n  ".join(
        f'<text x="26" y="{82 + i * 20}" class="sans" font-size="13.5" fill="#8b949e">{escape(l)}</text>'
        for i, l in enumerate(desc))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">{escape(name)}</title>
  <desc id="d">{escape(" ".join(desc))}</desc>
  <style>
    .sans{{font-family:"Segoe UI",-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif}}
    .mono{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}}
    {CSS_ART[kind]}
    @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.pkt{{display:none}}}}
  </style>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="#0d1117" stroke="#30363d"/>
  <clipPath id="clip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
  <rect x="0" y="0" width="6" height="{H}" fill="{accent}" clip-path="url(#clip)"/>
  <text x="26" y="44" class="sans" font-size="20" font-weight="700" fill="#e6edf3">{escape(name)}</text>
  {lines}
  <circle cx="31" cy="156" r="5" fill="{LANG_COLOR.get(lang, "#8b949e")}"/>
  <text x="42" y="160" font-size="12.5"><tspan class="sans" fill="#c9d1d9">{escape(lang)}</tspan><tspan class="mono" dx="12" font-size="11.5" fill="{accent}">{escape(tags)}</tspan></text>
  {art(kind, accent)}
</svg>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for c in CARDS:
        (OUT / f"{c[0].lower()}.svg").write_text(card(*c))
        print("wrote", c[0])


if __name__ == "__main__":
    main()
