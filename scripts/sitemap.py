#!/usr/bin/env python3
"""Write sitemap.xml: the site's pages and every post in blog/posts, each with the date it last changed.

scripts/blog.py and scripts/changelog.py run this. After changing a page by hand, run it from the site's root:
python3 scripts/sitemap.py
"""
import datetime
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://yardlet.app"
PAGES = {"": "index.html", "privacy.html": "privacy.html", "terms.html": "terms.html",
         "changelog.html": "changelog.html", "blog/": "blog/index.html"}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def last_change(path):
    """The day of the page's last commit, or today while it has changes not committed yet."""
    if git("status", "--porcelain", "--", path):
        return datetime.date.today().isoformat()
    return git("log", "-1", "--format=%cs", "--", path) or datetime.date.today().isoformat()


def write():
    urls = [(f"{SITE}/{url}", last_change(path)) for url, path in PAGES.items()]
    for post in sorted((ROOT / "blog" / "posts").glob("*.md"), reverse=True):
        meta = dict(re.findall(r"(?m)^(slug|date|updated): *(\S+)$", post.read_text().split("\n---\n", 1)[0]))
        urls.append((f"{SITE}/blog/{meta['slug']}.html", meta.get("updated") or meta["date"]))
    entries = "".join(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{day}</lastmod>\n  </url>\n" for loc, day in urls)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      f"{entries}</urlset>\n")


if __name__ == "__main__":
    write()
