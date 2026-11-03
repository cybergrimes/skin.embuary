#!/usr/bin/env python3
"""Validate docs/repo: every URL path resolves to a file, MD5 matches, ZIPs match the approved files.

Usage: python tools/validate_kodi_repository.py --approved-dir <dir>
"""
import argparse
import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PAGES = "https://cybergrimes.github.io/skin.embuary/"
errors = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        errors.append(msg)


def local(url):
    assert url.startswith(PAGES), url
    return DOCS / url[len(PAGES):]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--approved-dir", required=True)
    approved = Path(ap.parse_args().approved_dir)

    addons = (DOCS / "repo" / "addons.xml").read_bytes()
    md5 = (DOCS / "repo" / "addons.xml.md5").read_text().strip()
    check(hashlib.md5(addons).hexdigest() == md5, "addons.xml.md5 matches addons.xml")
    tree = ET.fromstring(addons)
    ids = {}
    for a in tree.findall("addon"):
        ids[a.get("id")] = a.get("version")
    check(set(ids) == {"repository.cybergrimes.embuary", "script.embuary.helper", "script.embuary.info"},
          f"addons.xml entries: {ids}")
    check("skin.embuary-matrix" not in ids, "skin not listed in addons.xml (direct download only)")

    for aid, ver in ids.items():
        z = DOCS / "repo" / aid / f"{aid}-{ver}.zip"
        check(z.is_file(), f"{z.relative_to(DOCS)} exists")
        if not z.is_file():
            continue
        with zipfile.ZipFile(z) as zf:
            check(zf.testzip() is None, f"{z.name} CRC ok")
            check({n.split('/')[0] for n in zf.namelist()} == {aid}, f"{z.name} single root {aid}")
            m = re.search(r'<addon\b[^>]*\bversion="([^"]+)"', zf.read(f"{aid}/addon.xml").decode("utf-8"))
            check(m and m.group(1) == ver, f"{z.name} addon.xml version {ver}")
        if aid.startswith("script."):
            a = approved / z.name
            check(a.is_file() and a.read_bytes() == z.read_bytes(), f"{z.name} byte-identical to approved file")

    skin = DOCS / "download" / "skin.embuary-omega-21.0.1.zip"
    a = approved / skin.name
    check(skin.is_file() and a.is_file() and skin.read_bytes() == a.read_bytes(), "skin ZIP byte-identical to approved file")

    # repository add-on URLs resolve
    with zipfile.ZipFile(DOCS / "repo" / "repository.cybergrimes.embuary" / "repository.cybergrimes.embuary-1.0.0.zip") as zf:
        r = ET.fromstring(zf.read("repository.cybergrimes.embuary/addon.xml"))
    d = r.find(".//dir")
    for tag in ("info", "checksum"):
        check(local(d.find(tag).text).is_file(), f"repo add-on <{tag}> URL resolves: {d.find(tag).text}")
    datadir = d.find("datadir").text
    for aid, ver in ids.items():
        check(local(f"{datadir}{aid}/{aid}-{ver}.zip").is_file(), f"datadir URL resolves: {datadir}{aid}/{aid}-{ver}.zip")
    check(local(PAGES + "download/skin.embuary-omega-21.0.1.zip").is_file(), "download URL resolves")
    check((DOCS / "index.html").is_file(), "index.html present")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
