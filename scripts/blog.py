#!/usr/bin/env python3
"""Write the blog from the posts in blog/posts/*.md: blog/<slug>.html and blog/og/<slug>.png for each post,
blog/index.html and blog/feed.xml.

Run it from the site's root after adding or changing a post: python3 scripts/blog.py
A post starts with a front matter block (title, slug, date as YYYY-MM-DD, description, and optionally kind) and
is written in the small part of Markdown the posts use: ## and ### headings, paragraphs, - lists, > notes,
fenced code blocks (swift and python are colored), `code`, **bold** and [links](url). The pages use terms.html's
frame one folder down; the share images need Pillow and the Inter fonts in scripts/fonts.
"""
import datetime
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://yardlet.app"
FONTS = ROOT / "scripts" / "fonts"


# --- Markdown ---------------------------------------------------------------------------------------------

def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit("a post must start with a --- front matter block")
    meta = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    for key in ("title", "slug", "date", "description"):
        if not meta.get(key):
            sys.exit(f"front matter needs {key}")
    return meta, text[m.end():]


def inline(text):
    out = []
    for part in re.split(r"(`[^`]+`)", text):
        if len(part) > 1 and part.startswith("`") and part.endswith("`"):
            # Short code stays on one line; a long one may break, or it would push a phone's page wider.
            cls = ' class="long"' if len(part) > 26 else ""
            out.append(f"<code{cls}>{html.escape(part[1:-1], quote=False)}</code>")
            continue
        part = html.escape(part, quote=False)
        part = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", part)
        part = re.sub(r"\[([^\]]+)\]\(((?:https?://|/|\.\./)[^)\s]+)\)", r'<a href="\2">\1</a>', part)
        out.append(part)
    return "".join(out)


KEYWORDS = {
    "swift": {"static", "let", "var", "func", "guard", "else", "return", "public", "private", "internal", "struct",
              "class", "enum", "extension", "import", "if", "in", "for", "while", "init", "self", "true", "false",
              "nil", "try", "await", "async", "throws", "some", "any"},
    "python": {"import", "from", "def", "return", "for", "in", "if", "elif", "else", "and", "or", "not", "continue",
               "break", "while", "with", "as", "class", "None", "True", "False", "lambda", "try", "except"},
}
TOKEN = {
    "swift": re.compile(r'(?P<c>//[^\n]*)|(?P<s>"(?:\\.|[^"\\\n])*")|(?P<a>@\w+)|(?P<n>\b\d+(?:\.\d+)?\b)|(?P<w>\b[A-Za-z_]\w*\b)'),
    "python": re.compile(r'(?P<c>#[^\n]*)|(?P<s>[rbf]?"(?:\\.|[^"\\\n])*"|[rbf]?\'(?:\\.|[^\'\\\n])*\')|(?P<n>\b\d+(?:\.\d+)?\b)|(?P<w>\b[A-Za-z_]\w*\b)'),
}


def highlight(code, lang):
    """Colors for the languages the posts use; anything else is set as it is."""
    pattern = TOKEN.get(lang)
    if not pattern:
        return html.escape(code, quote=False)
    out, last = [], 0
    for m in pattern.finditer(code):
        out.append(html.escape(code[last:m.start()], quote=False))
        text = html.escape(m.group(0), quote=False)
        kind = m.lastgroup
        if kind == "w":
            word = m.group(0)
            if word in KEYWORDS[lang]:
                out.append(f'<span class="hl-k">{text}</span>')
            elif lang == "swift" and word[0].isupper():
                out.append(f'<span class="hl-t">{text}</span>')
            else:
                out.append(text)
        else:
            out.append(f'<span class="hl-{kind}">{text}</span>')
        last = m.end()
    out.append(html.escape(code[last:], quote=False))
    return "".join(out)


LANGUAGE_NAMES = {"swift": "Swift", "python": "Python", "": "Output", "text": "Output", "sh": "Shell"}


def body_html(markdown):
    blocks, para, items, note = [], [], [], []
    lines = markdown.split("\n")

    def flush():
        if para:
            blocks.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            blocks.append("<ul>\n" + "".join(f"<li>{inline(x)}</li>\n" for x in items) + "</ul>")
            items.clear()
        if note:
            paragraphs = [p for p in "\n".join(note).split("\n\n") if p.strip()]
            blocks.append('<aside class="note">' + "".join(f"<p>{inline(' '.join(p.split()))}</p>" for p in paragraphs) + "</aside>")
            note.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush()
            # A fence may name a label after the language: ```text Crash report
            lang, _, given = line[3:].strip().partition(" ")
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            label = given.strip() or LANGUAGE_NAMES.get(lang, lang.capitalize())
            blocks.append(f'<figure class="code"><figcaption><span>{html.escape(label)}</span>'
                          f'<button class="copy" type="button" hidden>Copy</button></figcaption>'
                          f'<pre><code>{highlight(chr(10).join(code), lang)}</code></pre></figure>')
        elif line.startswith("> ") or line == ">":
            if para or items:
                flush()
            note.append(line[2:] if line.startswith("> ") else "")
        elif line.startswith("### "):
            flush()
            blocks.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("## "):
            flush()
            title = line[3:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            blocks.append(f'<h2 id="{anchor}"><a class="anchor" href="#{anchor}" aria-hidden="true">#</a>{inline(title)}</h2>')
        elif line.startswith("- "):
            if para or note:
                flush()
            items.append(line[2:].strip())
        elif line.startswith("  ") and items and line.strip():
            items[-1] += " " + line.strip()
        elif not line.strip():
            if not note:
                flush()
            else:
                note.append("")
        else:
            if items or note:
                flush()
            para.append(line.strip())
        i += 1
    flush()
    return "\n".join(blocks)


def reading_minutes(markdown):
    prose = re.sub(r"```.*?```", "", markdown, flags=re.S)
    return max(1, math.ceil(len(re.findall(r"\w+", prose)) / 230))


def say_date(day):
    return f"{day:%B} {day.day}, {day.year}"


# --- Share images -----------------------------------------------------------------------------------------

def share_image(post, path):
    """A 1200x630 card for links to the post: the blog's name, the title and the date."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow is not installed: share images left as they are")
        return False
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, h - 10, w, h], fill=(221, 226, 234))
    icon = Image.open(ROOT / "assets" / "icon-256.png").convert("RGBA").resize((64, 64), Image.LANCZOS)
    img.paste(icon, (80, 72), icon)
    label = ImageFont.truetype(str(FONTS / "Inter-SemiBold.ttf"), 30)
    draw.text((164, 87), "Yardlet blog", font=label, fill=(75, 75, 82))
    size = 68
    while True:
        font = ImageFont.truetype(str(FONTS / "InterDisplay-Bold.ttf"), size)
        words, lines, line = post["title"].split(), [], ""
        for word in words:
            test = (line + " " + word).strip()
            if draw.textlength(test, font=font) <= w - 160:
                line = test
            else:
                lines.append(line)
                line = word
        lines.append(line)
        if len(lines) <= 4 or size <= 44:
            break
        size -= 4
    y = 200
    for line in lines:
        draw.text((80, y), line, font=font, fill=(29, 29, 31))
        y += int(size * 1.12)
    small = ImageFont.truetype(str(FONTS / "Inter-Medium.ttf"), 26)
    draw.text((80, h - 84), f"{say_date(post['day'])} · {post['minutes']} min read", font=small, fill=(107, 107, 115))
    tag = "yardlet.app"
    draw.text((w - 80 - draw.textlength(tag, font=small), h - 84), tag, font=small, fill=(107, 107, 115))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return True


# --- Pages ------------------------------------------------------------------------------------------------

def frame(title, description, canonical, main, extra_head, current_index):
    """terms.html's page one folder down, with this page's head and main, and site.js for the copy buttons."""
    page = (ROOT / "terms.html").read_text()
    page = re.sub(r'(href|src)="(?!https?:|#|mailto:|/|\.\./)([^"]*)"', lambda m: f'{m.group(1)}="../{m.group(2)}"', page)
    page = page.replace('href=".././', 'href="../').replace('href="../blog/"', 'href="./"')
    page = page.replace("default-src 'none'; img-src 'self'; style-src 'self';",
                        "default-src 'none'; script-src 'self'; img-src 'self'; style-src 'self';", 1)
    page = re.sub(r"<title>.*?</title>", lambda _: f"<title>{html.escape(title)}</title>", page, count=1)
    page = re.sub(r'<meta name="description" content="[^"]*">',
                  lambda _: f'<meta name="description" content="{html.escape(description)}">\n'
                            f'<link rel="canonical" href="{canonical}">\n'
                            f'<link rel="alternate" type="application/atom+xml" title="Yardlet blog" href="{SITE}/blog/feed.xml">\n'
                            + extra_head, page, count=1)
    page = page.replace('<link rel="stylesheet" href="../style.css">',
                        '<link rel="stylesheet" href="../style.css">\n<link rel="stylesheet" href="../blog.css">\n'
                        '<script src="../site.js" defer></script>', 1)
    page = page.replace(' aria-current="page"', "", 1)
    if current_index:
        page = page.replace('<a class="task" href="./">', '<a class="task" href="./" aria-current="page">', 1)
    page = page.replace('<span class="jump-title">Terms of use</span>', '<span class="jump-title">Blog</span>')
    page = re.sub(r'<main class="doc" id="main">.*?</main>', lambda _: main, page, count=1, flags=re.S)
    for needed in ("<title>", 'rel="canonical"', '<span class="jump-title">Blog</span>', 'href="../blog.css"',
                   "script-src 'self'", 'src="../site.js"'):
        if needed not in page:
            sys.exit(f"terms.html no longer has the frame this script expects ({needed!r} missing)")
    return page


def meta_line(p, kind=True):
    parts = []
    if kind:
        parts.append(f'<span class="kind">{html.escape(p.get("kind") or "Engineering")}</span>')
    parts.append(f'<span><time datetime="{p["day"].isoformat()}">{say_date(p["day"])}</time></span>')
    parts.append(f'<span>{p["minutes"]} min read</span>')
    return '<p class="post-meta">' + "".join(parts) + "</p>"


def post_page(p, others):
    url = f"{SITE}/blog/{p['slug']}.html"
    image = f"{SITE}/blog/og/{p['slug']}.png" if p.get("image") else f"{SITE}/screens/og.jpg"
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": p["description"],
          "datePublished": p["day"].isoformat(), "url": url, "image": image, "mainEntityOfPage": url,
          "author": {"@type": "Organization", "name": "Yardlet", "url": SITE + "/"},
          "publisher": {"@type": "Organization", "name": "Yardlet", "url": SITE + "/"}}
    head = (f'<meta property="og:type" content="article">\n<meta property="og:site_name" content="Yardlet">\n'
            f'<meta property="og:url" content="{url}">\n<meta property="og:title" content="{html.escape(p["title"])}">\n'
            f'<meta property="og:description" content="{html.escape(p["description"])}">\n'
            f'<meta property="og:image" content="{image}">\n<meta property="og:image:width" content="1200">\n'
            f'<meta property="og:image:height" content="630">\n<meta property="article:published_time" content="{p["day"].isoformat()}">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:image" content="{image}">\n'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    i = others.index(p)
    newer = others[i - 1] if i > 0 else None  # the next post up the list, newest first
    nav_right = f'<a href="{newer["slug"]}.html">{html.escape(newer["title"])} →</a>' if newer else '<a href="feed.xml">Feed</a>'
    main = (
        '<main class="doc blog" id="main">\n<article class="post">\n<header class="post-head">\n'
        f"{meta_line(p)}\n<h1>{inline(p['title'])}</h1>\n<p class=\"dek\">{inline(p['description'])}</p>\n</header>\n"
        f'<div class="post-body">\n{p["body"]}\n</div>\n</article>\n'
        '<footer class="post-end">\n<div class="about">\n<img src="../assets/icon-256.png" alt="" width="44" height="44">\n'
        '<div><p><strong>Yardlet</strong> is a free, open-source app that runs Codex, Claude Code and other coding '
        'agent CLIs side by side, each with its own sign-in and history.</p>\n<p class="links">'
        '<a class="btn btn-small" href="../#install">Download for Mac</a>'
        '<a class="btn btn-small btn-quiet" href="https://github.com/zzunkie/yardlet">View on GitHub</a></p></div>\n</div>\n'
        f'<nav class="post-nav" aria-label="Posts"><a href="./">← All posts</a>{nav_right}</nav>\n</footer>\n</main>')
    return frame(p["title"] + " · Yardlet blog", p["description"], url, main, head, False)


def index_page(posts):
    items = "\n".join(
        f'<li>{meta_line(p)}\n<h2><a href="{p["slug"]}.html">{inline(p["title"])}</a></h2>\n<p>{inline(p["description"])}</p></li>'
        for p in posts)
    main = ('<main class="doc blog" id="main">\n<header class="blog-head">\n<h1>Yardlet blog</h1>\n'
            '<p>Notes from building Yardlet, an app for running coding agents side by side: what broke, what we '
            'measured and what we changed.</p>\n<p class="feed"><a href="feed.xml">Subscribe to the feed</a></p>\n</header>\n'
            f'<ul class="post-list">\n{items}\n</ul>\n</main>')
    head = ('<meta property="og:type" content="website">\n<meta property="og:title" content="Yardlet blog">\n'
            f'<meta property="og:url" content="{SITE}/blog/">\n<meta property="og:image" content="{SITE}/screens/og.jpg">\n'
            '<meta name="twitter:card" content="summary_large_image">')
    return frame("Yardlet blog", "Notes from building Yardlet, an app for running coding agents side by side.",
                 f"{SITE}/blog/", main, head, True)


def feed(posts):
    updated = (posts[0]["day"] if posts else datetime.date.today()).isoformat() + "T00:00:00Z"
    entries = "".join(
        "  <entry>\n"
        f"    <title>{html.escape(p['title'])}</title>\n"
        f'    <link href="{SITE}/blog/{p["slug"]}.html"/>\n'
        f"    <id>{SITE}/blog/{p['slug']}.html</id>\n"
        f"    <updated>{p['day'].isoformat()}T00:00:00Z</updated>\n"
        f"    <summary>{html.escape(p['description'])}</summary>\n"
        f'    <content type="html">{html.escape(p["body"])}</content>\n'
        "  </entry>\n" for p in posts)
    return ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n'
            "  <title>Yardlet blog</title>\n"
            f'  <link href="{SITE}/blog/"/>\n  <link rel="self" href="{SITE}/blog/feed.xml"/>\n'
            f"  <id>{SITE}/blog/</id>\n  <updated>{updated}</updated>\n"
            "  <author><name>Yardlet</name></author>\n" + entries + "</feed>\n")


def main():
    posts = []
    for path in sorted((ROOT / "blog" / "posts").glob("*.md"), reverse=True):
        meta, body = front_matter(path.read_text())
        meta["day"] = datetime.date.fromisoformat(meta["date"])
        meta["minutes"] = reading_minutes(body)
        meta["body"] = body_html(body)
        posts.append(meta)
    posts.sort(key=lambda p: p["day"], reverse=True)
    out = ROOT / "blog"
    for p in posts:
        p["image"] = share_image(p, out / "og" / f"{p['slug']}.png")
    for p in posts:
        (out / f"{p['slug']}.html").write_text(post_page(p, posts))
    (out / "index.html").write_text(index_page(posts))
    (out / "feed.xml").write_text(feed(posts))
    print(f"blog: {len(posts)} posts")


if __name__ == "__main__":
    main()
