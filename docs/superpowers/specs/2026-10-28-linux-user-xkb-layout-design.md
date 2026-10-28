# Livonian XKB layout as a per-user install

Date: 2026-10-28

## Goal

Ship the Livonian keyboard for Linux so that a user can install it without root, without overwriting system files in `/usr/share/X11/xkb`, and without getting it into xkeyboard-config upstream. It must show up as "Livonian" in the desktop's keyboard settings.

## Decisions

- **Scope: Wayland sessions only.** libxkbcommon (used by Wayland compositors) reads `$XDG_CONFIG_HOME/xkb` (default `~/.config/xkb`) before the system directory, and libxkbregistry (used by KDE's keyboard settings, `kcm_keyboard.so` links it on Plasma 6.8) merges a user `rules/evdev.xml` into the layout list. XWayland apps get the keymap from the compositor, so they work too. X11 sessions are not supported: `xkbcomp` ignores user directories. The README says so.
- **A new layout `liv`, not a variant of `lv`.** A user `symbols/lv` would shadow the whole system `lv` file. A separate `symbols/liv` (ISO 639-3 code for Livonian) can `include "lv(basic)"` from the system without conflict.
- **Two variants:** the default (apostrophe + backtick, matching the README and the bookmarklet) and `linguistic` (port of the old `livlinguapxtd`).
- **The old approach is removed:** the copies of the system `rules/{base,evdev}.{xml,lst}`, the modified full `symbols/lv` and `linux/.gitignore` are deleted. Git history keeps them.
- **The bookmarklet stays the source of truth.** The Linux test reads its expectations from `deadKeyMap` in `bookmarklet/livonian-keyboard.js`.

## Findings that shaped the design

Probing the old variants with libxkbcommon 1.6 (ctypes, keymap compiled from the repo's `lv` file):

- `livonianapxtd` is broken: after the apostrophe latch only the Latvian letters come out (ē ŗ ū ī ō ā š ģ ķ ļ ž č ņ, plus ţ ȳ ḑ), q w p j x m stay plain, and the backtick (Level 5) latch does nothing. Its six-symbol keys have no explicit key type.
- `livlinguapxtd` works: it sets `FOUR_LEVEL`, `EIGHT_LEVEL` and `EIGHT_LEVEL_ALPHABETIC` explicitly, and both latch rows match the README. But after the backtick latch, letters with no Livonian character type nothing, while the bookmarklet passes them through.

## Files

`linux/` mirrors the `~/.config/xkb` tree.

### `linux/symbols/liv`

A marker comment on the first line (`// livonian-keyboard`) so the installer can recognise the file.

- `default partial alphanumeric_keys modifier_keys xkb_symbols "basic"`, `name[Group1] = "Livonian"`:
  - `include "lv(basic)"`, so the Latvian QWERTY layout and its AltGr (Level 3) characters stay.
  - `<AC11>` (apostrophe): `ISO_Level3_Latch`, Shift gives `quotedbl`, level 3 gives `apostrophe`.
  - `<TLDE>` (backtick): `ISO_Level5_Latch`, Shift gives `asciitilde`, level 3 gives `grave`, level 5 gives `grave`, plus `modifier_map Mod3 { <TLDE> }`.
  - `<SPCE>`: level 3 gives `apostrophe`, level 5 gives `grave`.
  - `<AC11>` level 5 gives `apostrophe`, so `` ` `` then `'` types `'`.
  - `<AC11>`, `<TLDE>` and `<SPCE>` use an explicit `EIGHT_LEVEL` type.
  - Letter keys use an explicit `EIGHT_LEVEL_ALPHABETIC` type, as the working `livlinguapxtd` does, so Caps Lock uppercases the Livonian characters too (Caps Lock + `'` `q` → `Ä`, like the bookmarklet, which gets `Q`). Levels 3/4 hold the apostrophe characters, levels 5/6 the backtick characters. A level with no Livonian character repeats the plain letter (lower/upper), so latch + unmapped letter types the letter.
- `xkb_symbols "linguistic"`, `name[Group1] = "Livonian (linguistic)"`: the old `livlinguapxtd` section, with levels 5/6 of letters without a backtick character filled with the plain letter, and `<AC11>` level 5 giving `apostrophe`.
- Author header comment kept from the old file. No X11 licence block: the file no longer copies the system `lv` file, it includes it.

### `linux/rules/evdev.xml`

A minimal `xkbConfigRegistry` (version 1.1) with a marker comment (`<!-- livonian-keyboard -->`) and one layout:

- `name` `liv`, `shortDescription` `liv`, `description` `Livonian`, `languageList` with `iso639Id` `liv`
- one variant: `name` `linguistic`, `description` `Livonian (linguistic)`

No `rules/evdev` file: the system rules map layout `liv` to `symbols/liv` with their wildcard rule, and libxkbcommon finds the file in the user directory.

### `linux/install.sh`

Bash, no root, `set -euo pipefail`.

- Target: `${XDG_CONFIG_HOME:-$HOME/.config}/xkb`.
- Install: for each of `symbols/liv` and `rules/evdev.xml`, if the target exists and doesn't contain the marker, abort with a message (for `evdev.xml`, print the `<layout>` block to add by hand). Otherwise create the directories and copy the file.
- `--uninstall`: remove each of the two files only if it contains the marker; remove the directories only if they become empty.
- After install, print the next step: KDE System Settings → Keyboard → Layouts → Add → Livonian; for GNOME, `gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'liv')]"` (or append to the existing list), because GNOME Settings may not list user layouts. Mention logging out and in if the layout doesn't show up.
- Any other argument prints usage and exits non-zero.

### `test/linux_layout_test.py`

Python 3 standard library only, runs with `python3 -I`. Uses ctypes on the system `libxkbcommon.so.0`.

- Compile with `XKB_CONTEXT_NO_DEFAULT_INCLUDES` and include paths `[<repo>/linux, /usr/share/X11/xkb]`, so the developer's own `~/.config/xkb` can't affect the result. Rules `evdev`, model `pc105`.
- Simulate typing like a Wayland client: read a key's UTF-8 from the state before pressing it, then press and release it.
- Parse `deadKeyMap` from `bookmarklet/livonian-keyboard.js` (the `"'"` and ``"`"`` blocks, `key: "char"` entries). Fail if fewer than 40 entries are found, so a format change can't silently empty the test.
- For both `liv` and `liv(linguistic)`:
  - plain letters type themselves, Shift + letter the uppercase letter
  - every `deadKeyMap` entry: latch + key types the mapped character, uppercase entries via latch + Shift + key and via Caps Lock + latch + key
  - every other letter after either latch types the plain letter
  - `''` → `'`, ` `` ` → `` ` ``, `'` Space → `'`, `` ` `` Space → `` ` ``, `'` `` ` `` → `` ` ``, `` ` `` `'` → `'`
  - the latch is cleared after one key: `'` `q` `q` → `äq`
- `rules/evdev.xml` parses, declares layout `liv`, and each variant it lists compiles.
- Exit code 0 on success, 1 with a list of failures otherwise.

### Wiring

- `package.json`: `"linux-test": "python3 -I test/linux_layout_test.py"`.
- `.github/workflows/ci.yml`: install `libxkbcommon0 xkb-data` with apt, then `npm run linux-test`.

### Docs

- `README.md`: a "Linux" section covering install (`linux/install.sh`), manual install (copy the two files), uninstall, Wayland only (X11 not supported), the GNOME `gsettings` note, the linguistic variant, and the known difference (in the default layout `'` + digit or punctuation types the Latvian AltGr symbol, e.g. `¹`, because AltGr and the apostrophe latch share level 3).
- `AGENTS.md`: update the `linux/` line, add the `linux-test` command and the rule that layout changes are tested against `deadKeyMap`.

## Verification

- `npm run linux-test` passes, `npm test` and `npx prettier --check .` still pass.
- `install.sh` and `install.sh --uninstall` run against a temporary `XDG_CONFIG_HOME`: files appear and disappear, a foreign `evdev.xml` makes install abort and survives uninstall.
- On the author's machine (KDE Plasma 6.8, Wayland): install, add "Livonian" in System Settings, type the README rows in a Wayland app and an XWayland app.

## Out of scope

- X11 sessions (no `custom` layout hack, no `xkbcomp` autostart).
- Merging into an existing user `evdev.xml`.
- Packaging (deb, Flatpak, AUR) or upstreaming to xkeyboard-config.
