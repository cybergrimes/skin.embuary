#!/usr/bin/env python3
"""Build the GitHub Pages Kodi repository feed under docs/repo.

Usage:
    python tools/build_kodi_repository.py --approved-dir "C:\\path\\to\\approved\\zips"

The approved add-on ZIPs (script.embuary.helper-<ver>.zip, script.embuary.info-<ver>.zip)
are copied byte-for-byte. The skin ZIP is deliberately NOT part of addons.xml: Kodi derives
the package filename from add-on id + version (skin.embuary-matrix-21.0.1.zip), but the
reviewed skin ZIP is named skin.embuary-omega-21.0.1.zip. It is shipped as a direct download
under docs/download/ instead.
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
REPO_ID = "repository.cybergrimes.embuary"
REPO_VERSION = "1.0.0"
ADDON_ZIPS = {
    "script.embuary.helper": "2.0.9",
    "script.embuary.info": "2.0.9",
}
SKIN_ZIP = "skin.embuary-omega-21.0.1.zip"

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO = DOCS / "repo"
DOWNLOAD = DOCS / "download"

REPO_ADDON_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<addon id="{REPO_ID}" name="Embuary Repository (cybergrimes fork)" version="{REPO_VERSION}" provider-name="cybergrimes">
	<extension point="xbmc.addon.repository" name="Embuary Repository (cybergrimes fork)">
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
    args = ap.parse_args()
    approved = Path(args.approved_dir)

    if REPO.exists():
        shutil.rmtree(REPO)
    REPO.mkdir(parents=True)
    DOWNLOAD.mkdir(parents=True, exist_ok=True)

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

    # skin ZIP: direct download only
    skin_src = approved / SKIN_ZIP
    if not skin_src.is_file():
        sys.exit(f"missing approved zip: {skin_src}")
    shutil.copyfile(skin_src, DOWNLOAD / SKIN_ZIP)

    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    addons_xml += "\n".join(entries) + "\n</addons>\n"
    (REPO / "addons.xml").write_bytes(addons_xml.encode("utf-8"))
    md5 = hashlib.md5(addons_xml.encode("utf-8")).hexdigest()
    (REPO / "addons.xml.md5").write_text(md5)
    (DOCS / ".nojekyll").write_text("")
    print("built", REPO)


if __name__ == "__main__":
    main()
