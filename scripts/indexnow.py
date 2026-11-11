#!/usr/bin/env python3
"""Tell the search engines that share IndexNow (Bing, Yandex, Naver, Seznam and others) which pages changed.

.github/workflows/indexnow.yml runs this once GitHub Pages has published a push to main, with the commits before
and after the push, so a change reaches these engines without anyone having to remember. By hand, from the site's
root:
python3 scripts/indexnow.py            the pages changed by the last commit
python3 scripts/indexnow.py A B        the pages changed between commits A and B
python3 scripts/indexnow.py --all      every page in sitemap.xml
Only pages listed in sitemap.xml before or after the change are sent, so drafts and 404.html stay out. The engines
check KEY below against the file <KEY>.txt at the site's root before they take the list.
"""
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "yardlet.app"
KEY = "ee600072bc8b9ec9d818fe4279efd4f9"
ENDPOINT = "https://api.indexnow.org/indexnow"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def sitemap_urls(commit=None):
    """The addresses in sitemap.xml as it is on disk, or as it was at a commit (none if it had no sitemap)."""
    try:
        text = git("show", f"{commit}:sitemap.xml") if commit else (ROOT / "sitemap.xml").read_text()
    except subprocess.CalledProcessError:
        return set()
    return set(re.findall(r"<loc>(.*?)</loc>", text))


def url_of(path):
    """The address GitHub Pages serves a file at: an index.html stands for its folder."""
    if path == "index.html" or path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return f"https://{HOST}/{path}"


def changed(before, after):
    try:
        git("rev-parse", "--verify", "--quiet", f"{before}^{{commit}}")
    except subprocess.CalledProcessError:
        before = f"{after}~1"  # a first push or a force push: compare with the parent instead
    files = git("diff", "--name-only", before, after).split()
    return sorted({url_of(f) for f in files} & (sitemap_urls(before) | sitemap_urls(after)))


def submit(urls):
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls})
    request = urllib.request.Request(ENDPOINT, body.encode(), {"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


if __name__ == "__main__":
    args = sys.argv[1:]
    urls = sorted(sitemap_urls()) if args == ["--all"] else changed(*(args or ["HEAD~1", "HEAD"]))
    if not urls:
        print("indexnow: no page in the sitemap changed")
        sys.exit(0)
    status = submit(urls)
    print(f"indexnow: {status} for {len(urls)} pages", *urls, sep="\n  ")
    # 200: received. 202: received, the key is still being checked. Anything else is refused.
    sys.exit(0 if status in (200, 202) else 1)
