#!/usr/bin/env python3
"""Write the blog from the posts in blog/posts/*.md: blog/<slug>.html for each post, blog/index.html and
blog/feed.xml.

Run it from the site's root after adding or changing a post: python3 scripts/blog.py
A post starts with a front matter block (title, slug, date as YYYY-MM-DD, description) and is written in the
small part of Markdown the posts use: ## and ### headings, paragraphs, - lists, fenced code blocks, `code`,
**bold** and [links](url). The pages use terms.html's frame, one folder down.
"""
import datetime
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://yardlet.app"


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
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f"<code>{html.escape(part[1:-1], quote=False)}</code>")
            continue
        part = html.escape(part, quote=False)
        part = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", part)
        part = re.sub(r"\[([^\]]+)\]\(((?:https?://|/|\.\./)[^)\s]+)\)", r'<a href="\2">\1</a>', part)
        out.append(part)
    return "".join(out)


def body_html(markdown):
    blocks, para, items = [], [], []
    lines = markdown.split("\n")
    i = 0

    def flush():
        if para:
            blocks.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            blocks.append("<ul>\n" + "".join(f"  <li>{inline(x)}</li>\n" for x in items) + "</ul>")
            items.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush()
            lang = line[3:].strip()
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            blocks.append(f"<pre><code{cls}>{html.escape(chr(10).join(code), quote=False)}</code></pre>")
        elif line.startswith("### "):
            flush()
            blocks.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("## "):
            flush()
            title = line[3:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            blocks.append(f'<h2 id="{anchor}">{inline(title)}</h2>')
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
        i += 1
    flush()
    return "\n".join(blocks)


def say_date(day):
    return f"{day:%B} {day.day}, {day.year}"


def frame(title, description, canonical, main, current):
    """terms.html's page with paths one folder down, this page's title, description and main."""
    page = (ROOT / "terms.html").read_text()
    page = re.sub(r'(href|src)="(?!https?:|#|mailto:|/|\.\./)([^"]*)"', lambda m: f'{m.group(1)}="../{m.group(2)}"', page)
    page = page.replace('href=".././', 'href="../').replace('href="../"', 'href="../"')
    page = page.replace('href="../blog/"', 'href="./"')
    page = re.sub(r"<title>.*?</title>", lambda _: f"<title>{html.escape(title)}</title>", page, count=1)
    page = re.sub(r'<meta name="description" content="[^"]*">',
                  lambda _: f'<meta name="description" content="{html.escape(description)}">\n'
                            f'<link rel="canonical" href="{canonical}">\n'
                            f'<link rel="alternate" type="application/atom+xml" title="Yardlet blog" href="{SITE}/blog/feed.xml">',
                  page, count=1)
    page = page.replace(' aria-current="page"', "", 1)
    page = page.replace('<a class="task" href="./">', '<a class="task" href="./" aria-current="page">', 1) if current else page
    page = page.replace('<span class="jump-title">Terms of use</span>', '<span class="jump-title">Blog</span>')
    page = re.sub(r'<main class="doc" id="main">.*?</main>', lambda _: main, page, count=1, flags=re.S)
    for needed in ("<title>", 'rel="canonical"', '<span class="jump-title">Blog</span>', 'href="../style.css"'):
        if needed not in page:
            sys.exit(f"terms.html no longer has the frame this script expects ({needed!r} missing)")
    return page


def main():
    posts = []
    for path in sorted((ROOT / "blog" / "posts").glob("*.md")):
        meta, body = front_matter(path.read_text())
        meta["day"] = datetime.date.fromisoformat(meta["date"])
        meta["body"] = body_html(body)
        posts.append(meta)
    posts.sort(key=lambda p: p["day"], reverse=True)
    out = ROOT / "blog"
    for p in posts:
        url = f"{SITE}/blog/{p['slug']}.html"
        main_html = (
            '<main class="doc" id="main">\n  <article class="narrow">\n'
            f"    <h1>{inline(p['title'])}</h1>\n"
            f'    <p class="updated"><time datetime="{p["day"].isoformat()}">{say_date(p["day"])}</time> · '
            '<a href="./">Yardlet blog</a></p>\n'
            # The body goes in as it is: indenting its lines would indent the code blocks too.
            + p["body"] + "\n  </article>\n</main>"
        )
        (out / f"{p['slug']}.html").write_text(frame(p["title"] + " · Yardlet", p["description"], url, main_html, False))
    items = "\n".join(
        f'      <li><h2><a href="{p["slug"]}.html">{inline(p["title"])}</a></h2>\n'
        f'        <p class="updated"><time datetime="{p["day"].isoformat()}">{say_date(p["day"])}</time></p>\n'
        f'        <p>{inline(p["description"])}</p></li>' for p in posts)
    index_main = (
        '<main class="doc" id="main">\n  <div class="narrow">\n    <h1>Yardlet blog</h1>\n'
        '    <p class="summary">Notes from building Yardlet, a Mac app for running coding agents side by side. '
        '<a href="feed.xml">Feed</a></p>\n'
        f'    <ul class="posts">\n{items}\n    </ul>\n  </div>\n</main>')
    (out / "index.html").write_text(frame("Yardlet blog", "Notes from building Yardlet, a Mac app for running coding agents side by side.",
                                          f"{SITE}/blog/", index_main, True))
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
    (out / "feed.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n'
        "  <title>Yardlet blog</title>\n"
        f'  <link href="{SITE}/blog/"/>\n  <link rel="self" href="{SITE}/blog/feed.xml"/>\n'
        f"  <id>{SITE}/blog/</id>\n  <updated>{updated}</updated>\n"
        "  <author><name>Yardlet</name></author>\n" + entries + "</feed>\n")
    print(f"blog: {len(posts)} posts")


if __name__ == "__main__":
    main()
