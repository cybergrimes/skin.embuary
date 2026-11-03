#!/usr/bin/env python3
"""Build the GitHub Pages Kodi repository feed under docs/repo.

Usage:
    python tools/build_kodi_repository.py --approved-dir "C:\\path\\to\\approved\\zips"

The approved add-on ZIPs (script.embuary.helper-<ver>.zip, script.embuary.info-<ver>.zip)
are copied byte-for-byte. The skin ZIP (skin.embuary-omega-<ver>.zip in the approved dir, or
--skin-zip) is read for its add-on id/version, listed in addons.xml and published byte-identical
as repo/skin.embuary-matrix/skin.embuary-matrix-<ver>.zip (the name Kodi derives from id +
version). The same file is also kept as docs/download/skin.embuary-omega-<ver>.zip.
Releasing a new skin version: bump addon.xml, build the ZIP, run this script, run the validator, merge.
"""
import argparse
import hashlib
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

BASE_URL = "https://cybergrimes.github.io/skin.embuary/repo/"
REPO_ID = "repository.embuary"
REPO_VERSION = "1.0.0"
ADDON_ZIPS = {
    "script.embuary.helper": "2.0.9",
    "script.embuary.info": "2.0.9",
}
SKIN_ID = "skin.embuary-matrix"

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO = DOCS / "repo"
DOWNLOAD = DOCS / "download"

REPO_ADDON_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<addon id="{REPO_ID}" name="Embuary Repository" version="{REPO_VERSION}" provider-name="cybergrimes (fork), sualfred (original author)">
	<extension point="xbmc.addon.repository" name="Embuary Repository">
		<dir>
			<info compressed="false">{BASE_URL}addons.xml</info>
			<checksum>{BASE_URL}addons.xml.md5</checksum>
			<datadir zip="true">{BASE_URL}</datadir>
		</dir>
	</extension>
	<extension point="xbmc.addon.metadata">
		<summary lang="en_GB">Feed for the Embuary Omega fork add-ons</summary>
		<description lang="en_GB">Provides script.embuary.helper and script.embuary.info for the Embuary (Omega) skin fork by cybergrimes, based on the work of Sualfred.</description>
		<platform>all</platform>
		<license>CC-BY-NC-ND-4.0</license>
		<source>https://github.com/cybergrimes/skin.embuary</source>
	</extension>
</addon>
"""


def vkey(v):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.]", v))


def vkey(v):
    return tuple(int(x) if x.isdigit() else 0 for x in v.split("."))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def addon_xml_from_zip(zip_path, addon_id):
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:
            sys.exit(f"corrupt zip: {zip_path}")
        roots = {n.split("/")[0] for n in z.namelist()}
        if roots != {addon_id}:
            sys.exit(f"{zip_path}: root must be {addon_id}, got {roots}")
        return z.read(f"{addon_id}/addon.xml").decode("utf-8")


def strip_decl(xml):
    return re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", xml).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--approved-dir", required=True)
    ap.add_argument("--skin-zip", help="skin ZIP; default: highest skin.embuary-omega-*.zip in approved dir")
    args = ap.parse_args()
    approved = Path(args.approved_dir)

    if args.skin_zip:
        skin_src = Path(args.skin_zip)
    else:
        found = sorted(approved.glob("skin.embuary-omega-*.zip"), key=lambda p: vkey(p.stem.split("-")[-1]))
        if not found:
            sys.exit("no skin.embuary-omega-*.zip in approved dir")
        skin_src = found[-1]
    if not skin_src.is_file():
        sys.exit(f"missing skin zip: {skin_src}")
    skin_xml = addon_xml_from_zip(skin_src, SKIN_ID)
    m = re.search(r"<addon\b[^>]*\bid=\"([^\"]+)\"[^>]*\bversion=\"([^\"]+)\"", skin_xml)
    if not m or m.group(1) != SKIN_ID:
        sys.exit("skin addon.xml id mismatch")
    skin_version = m.group(2)

    for d in (REPO, DOWNLOAD):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    entries = []

    # repository add-on (zip built deterministically)
    repo_dir = REPO / REPO_ID
    repo_dir.mkdir()
    repo_zip = repo_dir / f"{REPO_ID}-{REPO_VERSION}.zip"
    with zipfile.ZipFile(repo_zip, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo(f"{REPO_ID}/addon.xml", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, REPO_ADDON_XML.encode("utf-8"))
    entries.append(strip_decl(REPO_ADDON_XML))

    # approved add-ons, copied byte-identical
    for addon_id, version in ADDON_ZIPS.items():
        name = f"{addon_id}-{version}.zip"
        src = approved / name
        if not src.is_file():
            sys.exit(f"missing approved zip: {src}")
        xml = addon_xml_from_zip(src, addon_id)
        m = re.search(r'<addon\b[^>]*\bid="([^"]+)"[^>]*\bversion="([^"]+)"', xml)
        if not m or m.group(1) != addon_id or m.group(2) != version:
            sys.exit(f"{name}: addon.xml id/version mismatch")
        dest_dir = REPO / addon_id
        dest_dir.mkdir()
        shutil.copyfile(src, dest_dir / name)
        if sha256(src) != sha256(dest_dir / name):
            sys.exit(f"copy of {name} is not byte-identical")
        entries.append(strip_decl(xml))

    # skin: feed entry plus direct download, byte-identical to the approved ZIP
    skin_dir = REPO / SKIN_ID
    skin_dir.mkdir()
    feed_zip = skin_dir / f"{SKIN_ID}-{skin_version}.zip"
    shutil.copyfile(skin_src, feed_zip)
    shutil.copyfile(skin_src, DOWNLOAD / f"skin.embuary-omega-{skin_version}.zip")
    if sha256(skin_src) != sha256(feed_zip):
        sys.exit("skin copy is not byte-identical")
    entries.append(strip_decl(skin_xml))

    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    addons_xml += "\n".join(entries) + "\n</addons>\n"
    (REPO / "addons.xml").write_bytes(addons_xml.encode("utf-8"))
    md5 = hashlib.md5(addons_xml.encode("utf-8")).hexdigest()
    (REPO / "addons.xml.md5").write_text(md5)
    (DOCS / ".nojekyll").write_text("")
    print("built", REPO)


if __name__ == "__main__":
    main()
