#!/usr/bin/env python3
"""Point the home page's phone section at the newest Android APK on GitHub, and bring sitemap.xml up to date.

Run it from the site's root after publishing an Android release: python3 scripts/android.py
It reads the releases tagged android-v<version> with the GitHub CLI (`gh`) and rewrites what index.html holds
between <!-- android:start --> and <!-- android:end -->.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import sitemap

REPO = "zzunkie/yardlet"
ROOT = Path(__file__).resolve().parent.parent
TAG = re.compile(r"^android-v(\d+)\.(\d+)\.(\d+)$")


def latest():
    out = subprocess.run(
        ["gh", "api", "--paginate", f"repos/{REPO}/releases?per_page=100", "--jq", ".[]"],
        check=True, capture_output=True, text=True,
    ).stdout
    found = [r for r in map(json.loads, out.splitlines())
             if TAG.match(r["tag_name"]) and not r["draft"] and not r["prerelease"]]
    if not found:
        sys.exit("no Android releases found")
    return max(found, key=lambda r: tuple(map(int, TAG.match(r["tag_name"]).groups())))


def block(r):
    version = r["tag_name"].removeprefix("android-v")
    apks = {a["name"]: a["browser_download_url"] for a in r["assets"] if a["name"].endswith(".apk")}
    main = apks.get(f"yardlet-remote-{version}.apk")
    foss = apks.get(f"yardlet-remote-{version}-foss.apk")
    if not main or not foss:
        sys.exit(f"{r['tag_name']} lacks the APKs this script expects: {sorted(apks)}")
    return (
        "<!-- android:start -->\n"
        "            <p>The Android app is in testing, for Android&nbsp;10 and later. In Yardlet on your Mac, turn on\n"
        "              Settings&nbsp;›&nbsp;Remote, choose Pair a phone and scan the QR code. To update, install a newer APK\n"
        "              over it or follow the <code>android-v</code> releases in Obtainium; the app tells you when one is out.</p>\n"
        '            <p class="phone-get">\n'
        f'              <a class="btn" href="{main}">Download for Android</a>\n'
        f'              <a class="btn btn-quiet" href="{foss}">Without Google Play services</a>\n'
        "            </p>\n"
        f'            <p class="approve-alt"><a href="{r["html_url"]}">Version {version}</a> · checksums and the signing\n'
        "              certificate are on the release page.</p>\n"
        "            <!-- android:end -->"
    )


if __name__ == "__main__":
    r = latest()
    home = ROOT / "index.html"
    text = home.read_text()
    new, n = re.subn(r"<!-- android:start -->.*?<!-- android:end -->", lambda _: block(r), text, count=1, flags=re.S)
    if n != 1:
        sys.exit("index.html no longer has the android:start and android:end markers")
    home.write_text(new)
    sitemap.write()
    print(f"index.html: {r['tag_name']}")
