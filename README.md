# skin.embuary
This is a fork of the Embuary skin by Sualfred (https://github.com/sualfred/skin.embuary), adapted for Kodi 21 Omega by cybergrimes. Original work and artwork by Sualfred, licensed CC BY-NC-ND 4.0 (unchanged).

Embuary is based on the web UI of Emby and has been developed for Emby-For-kodi users, but it doesn't require Emby at all and will also work with a regular Kodi setup.

# Terms of use
With the installation of the skin you agree that you don't use it in combination with blacklisted and illegal Kodi add-ons.
I'm not associated with any available build and I won't give any support to blacklisted, banned or illegal third party addons.

# License
This work has been released under CC by-nc-nd 4.0.

You are allowed to:
- Change whatever if you want to use it for your your personal use, but don't share it to the public. That restriction also applies to public GitHub repositories.
- If you fork and add your personal modifications you are allowed to release it to the public if you don't change the addon title/name to someting complete different (rebranding). Modification tags behind the addon title are okay. Example: ID "skin.embuary-moddedbyme" Name "Embuary Skin - Modded by me". The addon.xml has to include proper credits and the information that it's a fork based on my work. The license model cannot be changed.


# Kodi repository feed (GitHub Pages)
The folder `docs/` is served by GitHub Pages at https://cybergrimes.github.io/skin.embuary/. `docs/repo/addons.xml` lists the skin, `script.embuary.helper`, `script.embuary.info` and the repository add-on `repository.cybergrimes.embuary`. With that repository installed, Kodi offers new skin versions as normal add-on updates. The other skin dependencies (`xbmc.gui`, `resource.uisounds.embuary`, `plugin.program.autocompletion`, `script.skinshortcuts`) come from Kodi's official repository.

## Releasing a new skin version
1. Bump `version` in `addon.xml` and add a `changelog.txt` entry. Kodi only offers an update when the version number is higher.
2. Build the skin ZIP named `skin.embuary-omega-<version>.zip` (single root folder `skin.embuary-matrix/`, no .git/tooling, no .psd) and put it in one folder with the approved Helper/Info ZIPs.
3. Run `python tools/build_kodi_repository.py --approved-dir <folder>`. It regenerates `docs/repo/` (feed ZIP `skin.embuary-matrix-<version>.zip`, `addons.xml`, `addons.xml.md5`) and `docs/download/`.
4. Run `python tools/validate_kodi_repository.py --approved-dir <folder>` (must exit 0).
5. Update the version links in `docs/index.html`, commit and merge to `master`; Pages publishes `/docs`.