#!/usr/bin/env python3
"""Generate the animated README demo (assets/demo-v<__version__>.svg) from the real UI.

Usage:  python assets/make_demo.py

The screen is rendered by RivetRook's own functions (print_banner,
print_tools_table, tool_prompt, update_all_hint...) with sample data, in
English, at a fixed terminal size. The captured ANSI output is turned into a
character grid and written as a self-contained SVG: a terminal window where
`rivetrook` is typed, the banner appears, a "Checking tools" progress bar runs,
the table is revealed row by row and the prompt waits with a blinking cursor.
Pure CSS/SMIL animation (GitHub renders it in <img>), no external fonts.

Only the standard library is needed; it works on Windows, macOS and Linux.
Remember to point both READMEs at the new file name after a release.
"""

import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
COLS = 104

# ─── Sample data shown in the demo ────────────────────────────────────────────
# Installed tools and their versions; anything else shows as not installed.
INSTALLED = {
    "codex": "0.165.0",
    "pi": "1.4.0",
    "claude": "2.1.327",
    "opencode": "2.3.2",
    "kilocode": "7.8.8",
    "cline": "3.0.74",
    "grok": "1.0.70",
    "cursor-agent": "2026.11.13",
    "cursor": "3.29.9",
    "zed": "1.29.1",
    "opencode-desktop": "installed",
}
# Newer published versions (the "↑ update available" marker).
LATEST = {
    "codex": "0.169.0",
    "pi": "1.5.2",
    "kilocode": "7.8.27",
    "cursor": "3.30.14",
}
API_KEY_SET = {"grok"}


# ─── Capture the real UI ──────────────────────────────────────────────────────


class _TTYBuffer(io.StringIO):
    """A stdout replacement that claims to be a terminal, so RivetRook emits colors."""

    def isatty(self) -> bool:  # noqa: D401
        return True


def capture_screen() -> Tuple[List[str], Dict[str, int], object]:
    """Render the demo screen with RivetRook itself; return ANSI lines and row marks."""
    os.environ["COLORTERM"] = "truecolor"
    os.environ.pop("NO_COLOR", None)
    os.environ["TERM"] = "xterm-256color"
    os.environ["RIVETROOK_NO_UPDATE"] = "1"
    sys.argv = [sys.argv[0]]
    sys.path.insert(0, str(ROOT / "src"))

    buf = _TTYBuffer()
    real_stdout = sys.stdout
    sys.stdout = buf
    try:
        import RivetRook as R  # noqa: N812  (imported with the fake TTY in place)
    finally:
        sys.stdout = real_stdout

    config = json.loads((ROOT / "src" / "config.json").read_text(encoding="utf-8"))
    R._STRINGS = config["i18n"]["en"]
    R._CURRENT_LANG = "en"
    R._term_width = lambda: COLS
    R.tool_access_state = lambda block, os_name: "path"
    R._api_key_configured = lambda cfg: True
    tools, ides = config["tools"], config["ides"]
    for name, block in {**tools, **ides}.items():
        if name not in API_KEY_SET:
            block.pop("configure", None)
    versions = {n: INSTALLED.get(n) for n in {**tools, **ides}}
    latest = {n: LATEST.get(n, INSTALLED.get(n)) for n in {**tools, **ides}}

    marks: Dict[str, int] = {}
    out = _TTYBuffer()
    sys.stdout = out

    def mark(name: str) -> None:
        marks[name] = out.getvalue().count("\n")

    try:
        mark("banner")
        R.print_banner(R._t("tagline"))
        badge = "{} {}".format(
            R._pill("linux (debian)", R._GRAD[1]),
            R._pill("Python {}.{}".format(*sys.version_info[:2]), R._GRAD[3]),
        )
        print()
        print("  {}".format(R._t("system_label", badge)))
        mark("table")
        R.print_tools_table(tools, ides, versions, "linux", latest)
        mark("hint")
        outdated = sum(1 for n in versions if R.is_update_available(versions[n], latest[n]))
        print(R.update_all_hint(outdated) + "\n")
        mark("prompt")
        print(R.tool_prompt())
        mark("end")
    finally:
        sys.stdout = real_stdout

    return out.getvalue().split("\n"), marks, R


# ─── ANSI → cell grid ─────────────────────────────────────────────────────────

Cell = Tuple[str, str, Optional[str], bool]  # char, fg, bg, bold
DEFAULT_FG = "#E5E7EB"
BG = "#0B0F17"
BASIC = {
    30: "#1F2937", 31: "#F87171", 32: "#4ADE80", 33: "#FBBF24", 34: "#60A5FA",
    35: "#C084FC", 36: "#7DD3FC", 37: "#E5E7EB", 90: "#94A3B8", 91: "#F87171",
    92: "#4ADE80", 93: "#FBBF24", 94: "#60A5FA", 95: "#C084FC", 96: "#22D3EE",
    97: "#F8FAFC",
}


def _hex(rgb: Tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _blend(fg: str, bg: str, t: float) -> str:
    a = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return _hex(tuple(int(x * (1 - t) + y * t) for x, y in zip(a, b)))


def parse_ansi(line: str) -> List[Cell]:
    cells: List[Cell] = []
    fg, bg, bold, dim = DEFAULT_FG, None, False, False
    for tok in re.split(r"(\x1b\[[0-9;]*m)", line):
        if not tok:
            continue
        if tok.startswith("\x1b["):
            codes = [int(c) if c else 0 for c in tok[2:-1].split(";")]
            i = 0
            while i < len(codes):
                c = codes[i]
                if c == 0:
                    fg, bg, bold, dim = DEFAULT_FG, None, False, False
                elif c == 1:
                    bold = True
                elif c == 2:
                    dim = True
                elif c in BASIC:
                    fg = BASIC[c]
                elif c in (38, 48) and i + 4 < len(codes) + 1 and codes[i + 1] == 2:
                    col = _hex(tuple(codes[i + 2:i + 5]))
                    if c == 38:
                        fg = col
                    else:
                        bg = col
                    i += 4
                i += 1
            continue
        tok = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", tok)
        for ch in tok:
            if ch in "\r":
                continue
            color = _blend(fg, BG, 0.45) if dim else fg
            cells.append((ch, color, bg, bold))
    return cells


# ─── SVG writer ───────────────────────────────────────────────────────────────

CW, RH = 9.2, 20.0      # cell width / row height (px)
X0, TOP0 = 26.0, 58.0   # left margin, top of row 0 (row 0 = shell prompt)
BASE = 14.4             # text baseline inside a row
FONT = 15.2
DUR = 20.0              # loop length (s)
LIGHT = "─│╭╮╰╯"
DOUBLE = "═║╔╗╚╝"
GRAD = ["#A78BFA", "#60A5FA", "#22D3EE", "#34D399"]


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _pct(t: float) -> str:
    return "{:.3f}%".format(max(0.0, min(100.0, t / DUR * 100)))


# Two keyframes at the same offset make the later one win, which turns an
# instant switch into a slow fade from 0%: keep every transition this long.
_MIN_STEP = 0.01


class Svg:
    def __init__(self) -> None:
        self.css: List[str] = []
        self.body: List[str] = []

    def appear(self, name: str, t_on: float, fade: float = 0.25) -> str:
        """Class that fades in at *t_on* and stays until the loop fades out."""
        fade = max(fade, _MIN_STEP)
        self.css.append(
            "@keyframes {n}{{0%,{a}{{opacity:0}}{b},97%{{opacity:1}}100%{{opacity:0}}}}"
            ".{n}{{animation:{n} {d}s linear infinite}}".format(
                n=name, a=_pct(t_on), b=_pct(t_on + fade), d=DUR
            )
        )
        return name

    def window(self, name: str, t_on: float, t_off: float, fade: float = 0.0) -> str:
        """Class visible only between *t_on* and *t_off*."""
        fade = max(fade, _MIN_STEP)
        t_off = max(t_off, t_on + fade + _MIN_STEP)
        self.css.append(
            "@keyframes {n}{{0%,{a}{{opacity:0}}{b},{c}{{opacity:1}}{e},100%{{opacity:0}}}}"
            ".{n}{{opacity:0;animation:{n} {d}s linear infinite}}".format(
                n=name, a=_pct(t_on), b=_pct(t_on + fade), c=_pct(t_off),
                e=_pct(t_off + fade), d=DUR,
            )
        )
        return name


def _box_path(ch: str, x: float, top: float) -> str:
    """Path data drawing a box-drawing character inside its cell."""
    r, cx, cy, right, bottom, d = 4.0, x + CW / 2, top + RH / 2, x + CW, top + RH, 1.6
    light = {
        "─": "M{x} {cy}H{right}",
        "│": "M{cx} {top}V{bottom}",
        "╭": "M{right} {cy}H{cxr}Q{cx} {cy} {cx} {cyd}V{bottom}",
        "╮": "M{x} {cy}H{cxl}Q{cx} {cy} {cx} {cyd}V{bottom}",
        "╰": "M{cx} {top}V{cyu}Q{cx} {cy} {cxr} {cy}H{right}",
        "╯": "M{cx} {top}V{cyu}Q{cx} {cy} {cxl} {cy}H{x}",
        "═": "M{x} {cyu2}H{right}M{x} {cyd2}H{right}",
        "║": "M{cxl2} {top}V{bottom}M{cxr2} {top}V{bottom}",
        "╔": "M{right} {cyu2}H{cxl2}V{bottom}M{right} {cyd2}H{cxr2}V{bottom}",
        "╗": "M{x} {cyu2}H{cxr2}V{bottom}M{x} {cyd2}H{cxl2}V{bottom}",
        "╚": "M{cxl2} {top}V{cyd2}H{right}M{cxr2} {top}V{cyu2}H{right}",
        "╝": "M{cxr2} {top}V{cyd2}H{x}M{cxl2} {top}V{cyu2}H{x}",
    }[ch]
    v = dict(
        x=x, cx=cx, cy=cy, right=right, top=top, bottom=bottom,
        cxr=cx + r, cxl=cx - r, cyd=cy + r, cyu=cy - r,
        cxl2=cx - d, cxr2=cx + d, cyu2=cy - d, cyd2=cy + d,
    )
    return light.format(**{k: "{:.1f}".format(val) for k, val in v.items()})


def render_row(cells: List[Cell], row: int) -> str:
    """SVG elements for one terminal row."""
    top = TOP0 + row * RH
    y = "{:.1f}".format(top + BASE)
    parts: List[str] = []
    paths: Dict[Tuple[str, float], List[str]] = {}

    # Backgrounds (pills / key badges).
    col = 0
    while col < len(cells):
        bg = cells[col][2]
        if bg:
            start = col
            while col < len(cells) and cells[col][2] == bg:
                col += 1
            parts.append(
                '<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" rx="3" fill="{}"/>'.format(
                    X0 + start * CW, top + 2, (col - start) * CW, RH - 4, bg
                )
            )
        else:
            col += 1

    col = 0
    while col < len(cells):
        ch, fg, bg, bold = cells[col]
        x = X0 + col * CW
        if ch == " ":
            col += 1
            continue
        if ch == "█":
            parts.append(
                '<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="{}"/>'.format(
                    x, top, CW + 0.35, RH + 0.35, fg
                )
            )
            col += 1
            continue
        if ch in LIGHT or ch in DOUBLE:
            width = 1.2
            paths.setdefault((fg, width), []).append(_box_path(ch, x, top))
            col += 1
            continue
        weight = ' font-weight="700"' if bold else ""
        if ord(ch) > 127:
            # Symbols are centered on their cell so font metrics never shift them.
            parts.append(
                '<text x="{:.1f}" y="{}" text-anchor="middle" fill="{}"{}>{}</text>'.format(
                    x + CW / 2, y, fg, weight, _esc(ch)
                )
            )
            col += 1
            continue
        # ASCII run with the same style, spaces included, until a symbol or style change.
        start = col
        while (
            col < len(cells)
            and ord(cells[col][0]) <= 127
            and cells[col][1:] == (fg, bg, bold)
        ):
            col += 1
        text = "".join(c[0] for c in cells[start:col]).rstrip()
        if text:
            parts.append(
                '<text x="{:.1f}" y="{}" textLength="{:.1f}" lengthAdjust="spacingAndGlyphs" '
                'fill="{}"{}>{}</text>'.format(
                    X0 + start * CW, y, len(text) * CW, fg, weight, _esc(text)
                )
            )
    for (color, width), segs in paths.items():
        parts.append(
            '<path d="{}" stroke="{}" stroke-width="{}" fill="none" stroke-linecap="square"/>'.format(
                "".join(segs), color, width
            )
        )
    return "".join(parts)


def build_svg(lines: List[str], marks: Dict[str, int], version: str) -> str:
    grid = [parse_ansi(ln) for ln in lines[: marks["end"]]]
    rows_total = len(grid) + 1  # + shell prompt row
    width = round(X0 * 2 + COLS * CW)
    height = round(TOP0 + rows_total * RH + 18)
    svg = Svg()

    # Timeline (seconds).
    t_type, t_char = 0.6, 0.11
    t_banner = t_type + 9 * t_char + 0.45
    banner_rows = range(marks["banner"], marks["table"])
    t_scan = t_banner + len(banner_rows) * 0.07 + 0.3
    scan_len = 2.6
    t_table = t_scan + scan_len + 0.15
    table_rows = range(marks["table"], marks["end"])
    row_step = 0.065

    body: List[str] = []
    # Shell prompt with the command being typed.
    y0 = "{:.1f}".format(TOP0 + BASE)
    body.append(
        '<text x="{:.1f}" y="{}" textLength="{:.1f}" lengthAdjust="spacingAndGlyphs" '
        'fill="#64748B" font-weight="700">~/projects</text>'.format(X0, y0, 10 * CW)
    )
    body.append(
        '<text x="{:.1f}" y="{}" text-anchor="middle" fill="#A78BFA" font-weight="700">❯</text>'.format(
            X0 + 11 * CW + CW / 2, y0
        )
    )
    for i, ch in enumerate("rivetrook"):
        cls = svg.appear("c{}".format(i), t_type + i * t_char, 0.01)
        body.append(
            '<g class="{}"><text x="{:.1f}" y="{}" textLength="{:.1f}" lengthAdjust="spacingAndGlyphs" '
            'fill="#E5E7EB">{}</text></g>'.format(cls, X0 + (13 + i) * CW, y0, CW, ch)
        )
    # Cursor while typing.
    cls = svg.window("ct", 0.0, t_banner - 0.2)
    body.append(
        '<g class="{}"><rect class="blink" x="{:.1f}" y="{:.1f}" width="{:.1f}" height="16" fill="#22D3EE"/></g>'.format(
            cls, X0 + 22 * CW, TOP0 + 2, CW
        )
    )

    # Banner and system line.
    for k, r in enumerate(banner_rows):
        cls = svg.appear("b{}".format(r), t_banner + k * 0.07)
        body.append('<g class="{}">{}</g>'.format(cls, render_row(grid[r], r + 1)))

    # "Checking tools" progress bar on the first table row (the app clears it
    # right before drawing the table).
    scan_row = marks["table"] + 1
    top = TOP0 + scan_row * RH
    y = "{:.1f}".format(top + BASE)
    label = "Checking tools"
    bar_x = X0 + (4 + len(label) + 1) * CW
    bar_w = 30 * CW
    pg = svg.window("pg", t_scan, t_scan + scan_len + 0.3)
    spin = []
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for i, f in enumerate(frames):
        svg.css.append(
            "@keyframes sp{i}{{0%,{a:.1f}%{{opacity:0}}{a:.1f}%,{b:.1f}%{{opacity:1}}{b:.1f}%,100%{{opacity:0}}}}"
            ".sp{i}{{opacity:0;animation:sp{i} 1s steps(1) infinite}}".format(i=i, a=i * 10.0, b=(i + 1) * 10.0)
        )
        spin.append(
            '<text class="sp{}" x="{:.1f}" y="{}" text-anchor="middle" fill="#22D3EE">{}</text>'.format(
                i, X0 + 2 * CW + CW / 2, y, f
            )
        )
    pcts = []
    for i, p in enumerate(range(0, 101, 10)):
        t_on = t_scan + scan_len * p / 100.0
        t_off = t_scan + scan_len * (p + 10) / 100.0 if p < 100 else t_scan + scan_len + 0.3
        cls = svg.window("pc{}".format(p), t_on, t_off)
        pcts.append(
            '<text class="{}" x="{:.1f}" y="{}" textLength="{:.1f}" lengthAdjust="spacingAndGlyphs" '
            'fill="#A78BFA" font-weight="700">{:>4}</text>'.format(
                cls, bar_x + bar_w + CW, y, 4 * CW, "{}%".format(p)
            )
        )
    # The bar grows on the same CSS clock as everything else.
    svg.css.append(
        "@keyframes bar{{0%,{a}{{transform:scaleX(0)}}{b},100%{{transform:scaleX(1)}}}}"
        ".bar{{transform-box:fill-box;transform-origin:left center;animation:bar {d}s linear infinite}}".format(
            a=_pct(t_scan), b=_pct(t_scan + scan_len), d=DUR
        )
    )
    body.append(
        '<g class="{pg}">{spin}<text x="{lx:.1f}" y="{y}" textLength="{lw:.1f}" lengthAdjust="spacingAndGlyphs" '
        'fill="#E5E7EB">{label}</text><path d="M{bx:.1f} {by:.1f}h{bw:.1f}" stroke="#475569" stroke-width="3.4"/>'
        '<rect class="bar" x="{bx:.1f}" y="{ry:.1f}" width="{bw:.1f}" height="3.4" fill="url(#brand)"/>'
        "{pcts}</g>".format(
            pg=pg, spin="".join(spin), lx=X0 + 4 * CW, y=y, lw=len(label) * CW, label=label,
            bx=bar_x, by=top + RH / 2, bw=bar_w, ry=top + RH / 2 - 1.7, pcts="".join(pcts),
        )
    )

    # Table, hint and prompt, revealed row by row.
    for k, r in enumerate(table_rows):
        if not grid[r]:
            continue
        cls = svg.appear("r{}".format(r), t_table + k * row_step)
        body.append('<g class="{}">{}</g>'.format(cls, render_row(grid[r], r + 1)))

    # Blinking cursor after the prompt.
    prompt_row = marks["prompt"]
    t_end = t_table + len(table_rows) * row_step + 0.2
    cls = svg.appear("cf", t_end, 0.01)
    body.append(
        '<g class="{}"><rect class="blink" x="{:.1f}" y="{:.1f}" width="{:.1f}" height="16" fill="#22D3EE"/></g>'.format(
            cls, X0 + len(grid[prompt_row]) * CW, TOP0 + (prompt_row + 1) * RH + 2, CW
        )
    )

    stops = "".join(
        '<stop offset="{:.2f}" stop-color="{}"/>'.format(i / 3, c) for i, c in enumerate(GRAD)
    )
    defs = (
        "<defs>"
        '<linearGradient id="brand" x1="0" x2="1">{stops}</linearGradient>'
        '<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#A78BFA" stop-opacity="0.6"/>'
        '<stop offset="0.5" stop-color="#1F2937"/><stop offset="1" stop-color="#34D399" stop-opacity="0.5"/></linearGradient>'
        '<radialGradient id="glow" cx="0.15" cy="0" r="0.7"><stop offset="0" stop-color="#A78BFA" stop-opacity="0.12"/>'
        '<stop offset="1" stop-color="#A78BFA" stop-opacity="0"/></radialGradient>'
        "</defs>"
    ).format(stops=stops)
    style = (
        "<style>text{{font-family:'Cascadia Mono','SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace;"
        "font-size:{f}px;white-space:pre}}.blink{{animation:blink 1.06s steps(1) infinite}}"
        "@keyframes blink{{50%{{opacity:0}}}}{css}</style>"
    ).format(f=FONT, css="".join(svg.css))
    chrome = (
        '<rect x="1" y="1" width="{w}" height="{h}" rx="14" fill="{bg}"/>'
        '<rect x="1" y="1" width="{w}" height="{h}" rx="14" fill="url(#glow)"/>'
        '<rect x="1" y="1" width="{w}" height="{h}" rx="14" fill="none" stroke="url(#edge)" stroke-width="1.5"/>'
        '<circle cx="24" cy="22" r="6" fill="#F87171"/><circle cx="44" cy="22" r="6" fill="#FBBF24"/>'
        '<circle cx="64" cy="22" r="6" fill="#4ADE80"/>'
        '<text x="{mid}" y="27" text-anchor="middle" fill="#64748B" font-size="13">rivetrook — {cols}×{rows}</text>'
        '<path d="M1 42H{w}" stroke="#1F2937"/>'
    ).format(w=width - 2, h=height - 2, bg=BG, mid=width // 2, cols=COLS, rows=rows_total)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Animated demo of the RivetRook terminal interface"><title>RivetRook demo v{v}</title>'
        "{defs}{style}{chrome}{body}</svg>"
    ).format(w=width, h=height, v=version, defs=defs, style=style, chrome=chrome, body="".join(body))


def main() -> None:
    lines, marks, R = capture_screen()
    version = R.__version__
    out = ROOT / "assets" / "demo-v{}.svg".format(version)
    out.write_text(build_svg(lines, marks, version), encoding="utf-8")
    print("Wrote {} ({:,} bytes)".format(out.relative_to(ROOT), out.stat().st_size))
    print("Now update both READMEs to: assets/{}".format(out.name))


if __name__ == "__main__":
    main()
