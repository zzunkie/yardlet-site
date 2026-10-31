#!/usr/bin/env python3
"""Write changelog.html from the release notes of Yardlet's app releases on GitHub.

Run it from the site's root after publishing a release: python3 scripts/changelog.py
It reads the releases with the GitHub CLI (`gh`), keeps the app releases ("Yardlet 0.11.0" and later, not the
legacy CLI or build inputs), and puts their notes into terms.html's page frame.
"""
import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "zzunkie/yardlet"
ROOT = Path(__file__).resolve().parent.parent
APP_RELEASE = re.compile(r"^Yardlet (\d+)\.(\d+)\.(\d+)$")


def releases():
    out = subprocess.run(
        ["gh", "api", "--paginate", f"repos/{REPO}/releases?per_page=100", "--jq", ".[]"],
        check=True, capture_output=True, text=True,
    ).stdout
    found = []
    for line in out.splitlines():
        r = json.loads(line)
        m = APP_RELEASE.match(r.get("name") or "")
        if m and not r["draft"] and not r["prerelease"] and tuple(map(int, m.groups())) >= (0, 11, 0):
            found.append(r)
    found.sort(key=lambda r: tuple(map(int, APP_RELEASE.match(r["name"]).groups())), reverse=True)
    return found


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', text)


def body_html(markdown):
    """The small part of Markdown the release notes use: ## headings, - lists with indented continuations,
    and paragraphs. The notes' own # title is left out; the page gives each release its heading. So is their
    Install section, which points at the release's own download ("below") and says what the page already says."""
    markdown = re.split(r"(?m)^## Install\s*$", markdown, maxsplit=1)[0]
    blocks, items, para = [], [], []

    def flush():
        if items:
            blocks.append("<ul>\n" + "".join(f"  <li>{inline(i)}</li>\n" for i in items) + "</ul>")
            items.clear()
        if para:
            blocks.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()

    for line in markdown.replace("\r\n", "\n").split("\n"):
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            flush()
            blocks.append(f"<h3>{inline(line[3:].strip())}</h3>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:].strip())
        elif line.startswith("  ") and items and line.strip():
            items[-1] += " " + line.strip()
        elif not line.strip():
            flush()
        else:
            if items:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(blocks)


def page(rels):
    template = (ROOT / "terms.html").read_text()
    sections = []
    for r in rels:
        version = APP_RELEASE.match(r["name"]).group(0).split(" ", 1)[1]
        day = datetime.datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")).date()
        date = f"{day:%B} {day.day}, {day.year}"
        sections.append(
            f'    <section class="release" id="v{version}" aria-labelledby="v{version}-title">\n'
            f'      <h2 id="v{version}-title">Yardlet {version}</h2>\n'
            f'      <p class="updated"><time datetime="{day.isoformat()}">{date}</time> · '
            f'<a href="{r["html_url"]}">Release on GitHub</a></p>\n'
            + "\n".join("      " + l for l in body_html(r["body"] or "").split("\n")) + "\n"
            f"    </section>"
        )
    main = (
        '<main class="doc" id="main">\n  <div class="narrow">\n'
        "    <h1>Yardlet Changelog</h1>\n"
        '    <p class="summary">What changed in each version of the Yardlet app. Yardlet updates itself, and '
        '<a href="https://github.com/zzunkie/yardlet/releases">GitHub Releases</a> has the downloads. Changes on '
        "<code>main</code> that are not released yet are not listed.</p>\n\n"
        + "\n\n".join(sections) + "\n  </div>\n</main>"
    )
    out = re.sub(r'<main class="doc" id="main">.*?</main>', lambda _: main, template, count=1, flags=re.S)
    out = out.replace("<title>Yardlet Terms of Use</title>", "<title>Yardlet Changelog</title>", 1)
    out = re.sub(r'<meta name="description" content="[^"]*">',
                 '<meta name="description" content="What changed in each version of Yardlet, the free Mac app '
                 'for Codex, Claude Code and other coding agent CLIs.">\n'
                 '<link rel="canonical" href="https://yardlet.app/changelog.html">', out, count=1)
    out = out.replace(' aria-current="page"', "", 1)
    out = out.replace('<a class="task" href="changelog.html">', '<a class="task" href="changelog.html" aria-current="page">', 1)
    out = out.replace('<span class="jump-title">Terms of use</span>', '<span class="jump-title">Changelog</span>')
    for needed in ("Yardlet Changelog", 'aria-current="page"', '<span class="jump-title">Changelog</span>'):
        if needed not in out:
            sys.exit(f"terms.html no longer has the frame this script expects ({needed!r} missing)")
    return out


if __name__ == "__main__":
    rels = releases()
    if not rels:
        sys.exit("no app releases found")
    (ROOT / "changelog.html").write_text(page(rels))
    print(f"changelog.html: {len(rels)} releases, latest {rels[0]['name']}")
