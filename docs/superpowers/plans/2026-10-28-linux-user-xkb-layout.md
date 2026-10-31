# Livonian per-user XKB layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "overwrite the system XKB files" Linux layout with a `liv` layout that a user installs into `~/.config/xkb` without root, tested against the bookmarklet's `deadKeyMap`.

**Architecture:** `linux/` mirrors the `~/.config/xkb` tree: `symbols/liv` (sections `basic` and `linguistic`) and a minimal `rules/evdev.xml` registry. `linux/install.sh` copies them into place. Two stdlib Python tests drive the system libxkbcommon/libxkbregistry through ctypes (layout behaviour, registry) and run `install.sh` against temporary directories.

**Tech Stack:** XKB symbols, libxkbcommon 1.6 / libxkbregistry (ctypes), Python 3 stdlib `unittest`, bash, npm scripts, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-28-linux-user-xkb-layout-design.md`

## Global Constraints

- No root, no writes outside `${XDG_CONFIG_HOME:-$HOME/.config}/xkb`. Wayland sessions only; X11 is out of scope.
- Layout `liv`, shortDescription `liv`, description `Livonian`, language `liv`; variant `linguistic`, description `Livonian (linguistic)`.
- Markers: first line of `linux/symbols/liv` is `// livonian-keyboard`; `linux/rules/evdev.xml` contains `<!-- livonian-keyboard -->`. The installer only overwrites or removes files containing `livonian-keyboard`.
- `deadKeyMap` in `bookmarklet/livonian-keyboard.js` is the source of truth. Tests parse it; never copy its tables into tests.
- Letter keys: explicit `EIGHT_LEVEL_ALPHABETIC`; `<AC11>`, `<TLDE>`, `<SPCE>`: explicit `EIGHT_LEVEL`. No `modifier_map` on `<TLDE>` (or any latch key): `pc` already maps `<LVL5>` to Mod3, and a modmap on TLDE stops latches from clearing (spec, "Findings").
- Python: stdlib only, run with `python3 -I`. Tabs for indentation in every new file (Prettier with tabs; Python files too, to match the repo). End every file with a newline.
- npm needs nvm in non-interactive shells: `source ~/.nvm/nvm.sh && nvm use && npm ...`.
- Commit subjects start with `Linux: `, body explains why, and end with the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. The pre-commit hook runs Prettier through lint-staged.

## Review Focus

1. **Livonian as the second layout** next to `us` or `lv` (layout index 1): both dead keys must work after switching. Test: `test_second_layout` (Task 1).
2. **A dead key followed by a dead key or Space, then a letter**: the latch must be gone, so the letter is plain (`` ` `` `` ` `` `q` → `` `q ``, `'` `` ` `` `q` → `` `q ``). Test: `test_dead_key_combinations` (Task 1).
3. **Caps Lock on**: `'` `q` → `Ä`, `` ` `` `q` → `Ǟ`, and an unmapped letter after a latch stays uppercase (`` ` `` `f` → `F`). Tests: `test_dead_key_map_entries`, `test_unmapped_letters_pass_through` (Task 1).
4. **An existing `~/.config/xkb` with the user's own files, or an older install of ours**: never overwrite or delete foreign files, check everything before writing anything, replace our own older files. Tests: `test_install_aborts_on_foreign_*`, `test_install_replaces_own_files`, `test_uninstall_leaves_foreign_files` (Task 3).
5. **`XDG_CONFIG_HOME` unset or containing a space.** Tests: `test_default_target_is_home_config`, and every install test uses a config dir named `config dir` (Task 3).

---

### Task 1: Layout test harness and the default `liv` layout

**Files:**

- Create: `test/linux_layout_test.py`
- Create: `linux/symbols/liv`
- Modify: `package.json` (`scripts`)
- Modify: `.github/workflows/ci.yml`

**Interfaces:**

- Produces, in `test/linux_layout_test.py`:
  - `REPO: Path` (repo root), `XKB_DIR = REPO / "linux"`, `SYSTEM_XKB_DIR = "/usr/share/X11/xkb"`
  - `VARIANTS: list[str] = [""]` (Task 2 makes it `["", "linguistic"]`)
  - `LETTER_KEYS: dict[str, str]`: `"q" → "AD01"` … `"p" → "AD10"`, `"a" → "AC01"` … `"l" → "AC09"`, `"z" → "AB01"` … `"m" → "AB07"`
  - `DEAD_KEYS = {"'": "AC11", "`": "TLDE"}`
  - `compile_keymap(layout: str, variant: str = "") -> int`: keymap pointer, cached (`functools.cache`); fails the test with `keymap for {layout}({variant}) did not compile` when libxkbcommon returns NULL
  - `type_keys(keymap: int, *strokes: str | tuple[str, ...], layout_index: int = 0) -> str`
  - `dead_key_map() -> dict[str, dict[str, str]]`: `{"'": {"q": "ä", …, "Q": "Ä", …}, "`": {…}}`
  - `class LayoutTest(unittest.TestCase)`, file ends with `unittest.main()`

- [ ] **Step 1: Write the harness and the failing tests**

ctypes bindings (pointers are `c_void_p`, keycodes `c_uint32`):

```python
xkb = ctypes.CDLL("libxkbcommon.so.0")

class RuleNames(ctypes.Structure):
	_fields_ = [(f, ctypes.c_char_p) for f in ("rules", "model", "layout", "variant", "options")]

XKB_CONTEXT_NO_DEFAULT_INCLUDES = 1  # keeps the developer's ~/.config/xkb out of the test
XKB_KEY_UP, XKB_KEY_DOWN = 0, 1
XKB_KEYCODE_INVALID = 0xFFFFFFFF
# xkb_context_new(c_int) -> c_void_p
# xkb_context_include_path_append(c_void_p, c_char_p) -> c_int
# xkb_keymap_new_from_names(c_void_p, POINTER(RuleNames), c_int) -> c_void_p
# xkb_keymap_key_by_name(c_void_p, c_char_p) -> c_uint32
# xkb_state_new(c_void_p) -> c_void_p;  xkb_state_unref(c_void_p)
# xkb_state_update_key(c_void_p, c_uint32, c_int) -> c_int
# xkb_state_update_mask(c_void_p, c_uint32, c_uint32, c_uint32, c_uint32, c_uint32, c_uint32) -> c_int
# xkb_state_key_get_utf8(c_void_p, c_uint32, c_char_p, c_size_t) -> c_int
```

`compile_keymap`: new context with `XKB_CONTEXT_NO_DEFAULT_INCLUDES`, include paths `XKB_DIR` then `SYSTEM_XKB_DIR`, names `evdev` / `pc105` / layout / variant / no options. Until Task 2 deletes it, the old `linux/symbols/lv` shadows the system `lv` here, so `include "lv(basic)"` and the `lv,liv` test use the repo copy; that's expected and doesn't change the letter keys.

`type_keys` must read each key's text from the state **before** pressing it, the way Wayland clients do (reading after the press makes a latch key report its own level 3):

```python
def type_keys(keymap, *strokes, layout_index=0):
	state = xkb.xkb_state_new(keymap)
	if layout_index:
		xkb.xkb_state_update_mask(state, 0, 0, 0, 0, 0, layout_index)
	text = ""
	for stroke in strokes:
		*held, key = stroke if isinstance(stroke, tuple) else (stroke,)
		held, key = [keycode(keymap, k) for k in held], keycode(keymap, key)
		for k in held:
			xkb.xkb_state_update_key(state, k, XKB_KEY_DOWN)
		text += utf8(state, key)
		xkb.xkb_state_update_key(state, key, XKB_KEY_DOWN)
		xkb.xkb_state_update_key(state, key, XKB_KEY_UP)
		for k in reversed(held):
			xkb.xkb_state_update_key(state, k, XKB_KEY_UP)
	xkb.xkb_state_unref(state)
	return text
```

(`keycode` asserts the name resolves, i.e. isn't `XKB_KEYCODE_INVALID`.) `dead_key_map` reads the `"'": { … }` and ``"`": { … }`` blocks of the bookmarklet source with a regex and collects `letter: "char"` pairs.

Tests. Each loops `for variant in VARIANTS:` inside `self.subTest(variant=variant)`, with `km = compile_keymap("liv", variant)`:

```python
def test_dead_key_map_is_parsed(self):
	self.assertGreaterEqual(sum(len(m) for m in dead_key_map().values()), 40)

def test_plain_letters(self):
	# for letter, key in LETTER_KEYS.items():
	self.assertEqual(type_keys(km, key), letter)
	self.assertEqual(type_keys(km, ("LFSH", key)), letter.upper())
	self.assertEqual(type_keys(km, "CAPS", key), letter.upper())

def test_dead_key_map_entries(self):
	# for dead, mapping in dead_key_map().items(): for char_key, expected in mapping.items():
	# key = LETTER_KEYS[char_key.lower()], latch = DEAD_KEYS[dead]
	# lowercase entries:
	self.assertEqual(type_keys(km, latch, key), expected)
	# uppercase entries, both ways:
	self.assertEqual(type_keys(km, latch, ("LFSH", key)), expected)
	self.assertEqual(type_keys(km, "CAPS", latch, key), expected)

def test_unmapped_letters_pass_through(self):
	# for dead, latch; for letter, key in LETTER_KEYS.items() if letter not in dead_key_map()[dead]:
	self.assertEqual(type_keys(km, latch, key), letter)
	self.assertEqual(type_keys(km, latch, ("LFSH", key)), letter.upper())
	self.assertEqual(type_keys(km, "CAPS", latch, key), letter.upper())

def test_dead_key_combinations(self):
	cases = {
		("AC11", "AC11"): "'", ("TLDE", "TLDE"): "`",
		("AC11", "SPCE"): "'", ("TLDE", "SPCE"): "`",
		("AC11", "TLDE"): "`", ("TLDE", "AC11"): "'",
	}
	# for keys, expected in cases.items():
	self.assertEqual(type_keys(km, *keys, "AD01"), expected + "q")

def test_latch_cleared_after_one_key(self):
	self.assertEqual(type_keys(km, "AC11", "AD01", "AD01"), "äq")
	self.assertEqual(type_keys(km, "TLDE", "AD01", "AD01"), "ǟq")

def test_second_layout(self):
	# for first in ("us", "lv"): km = compile_keymap(f"{first},liv", f",{variant}")
	self.assertEqual(type_keys(km, "AD01", layout_index=1), "q")
	self.assertEqual(type_keys(km, "AC11", "AD01", layout_index=1), "ä")
	self.assertEqual(type_keys(km, "TLDE", "AB02", layout_index=1), "ȫ")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -I test/linux_layout_test.py`
Expected: `test_dead_key_map_is_parsed` passes; the others FAIL with `keymap for liv() did not compile`.

- [ ] **Step 3: Write `linux/symbols/liv` with the `basic` section**

- Line 1 `// livonian-keyboard`, then a short header: what the file is, that `linux/install.sh` installs it into `~/.config/xkb/symbols/`, and the repo URL `https://github.com/reinis-zumbergs/livonian-keyboard`.
- `default partial alphanumeric_keys modifier_keys xkb_symbols "basic"`, `include "lv(basic)"`, `name[Group1] = "Livonian";`
- `key.type[Group1] = "EIGHT_LEVEL";` then:
  - `<AC11>`: `[ISO_Level3_Latch, quotedbl, apostrophe, quotedbl, apostrophe, quotedbl]`
  - `<TLDE>`: `[ISO_Level5_Latch, asciitilde, grave, acute, grave, asciitilde]`
  - `<SPCE>`: `[space, space, apostrophe, quotedbl, grave, asciitilde]` (level 2 is a plain space, not the old `nobreakspace`, so text typed with Shift held doesn't pick up no-break spaces)
- `key.type[Group1] = "EIGHT_LEVEL_ALPHABETIC";` then all 26 letter keys, each `[letter, LETTER, ' lower, ' upper, ` lower, ` upper]` taken from `deadKeyMap`, with the plain letter (lower/upper) wherever the map has no entry. Named keysyms where XKB has one (`emacron`, `scaron`, …), `Uxxxx` with a trailing `// ä Ä ǟ Ǟ` comment otherwise, as the old `lv` file does.
- No `modifier_map` anywhere in the section.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -I test/linux_layout_test.py`
Expected: `OK`, 7 tests.

- [ ] **Step 5: Add the npm script and the CI step**

`package.json` scripts, after `"test"`: `"linux-test": "python3 -I test/linux_layout_test.py"`.
`.github/workflows/ci.yml`, after `npm test`:

```yaml
- name: Install XKB libraries for the Linux layout tests
  run: sudo apt-get update && sudo apt-get install -y libxkbcommon0 xkb-data
- run: npm run linux-test
```

Run: `source ~/.nvm/nvm.sh && nvm use && npm run linux-test && npm test && npx prettier --check .`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add test/linux_layout_test.py linux/symbols/liv package.json .github/workflows/ci.yml
git commit -m "Linux: Add the liv layout and test it against deadKeyMap" -m "..." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Linguistic variant, registry, and removal of the system-file copies

**Files:**

- Modify: `linux/symbols/liv` (add `linguistic`)
- Create: `linux/rules/evdev.xml`
- Delete: `linux/symbols/lv`, `linux/rules/base.lst`, `linux/rules/base.xml`, `linux/rules/evdev.lst`, `linux/rules/evdev.xml` (the old full copy; replaced by the new minimal file), `linux/.gitignore`
- Modify: `test/linux_layout_test.py`
- Modify: `.github/workflows/ci.yml` (apt package list)

**Interfaces:**

- Consumes: `compile_keymap`, `type_keys`, `VARIANTS`, `XKB_DIR`, `SYSTEM_XKB_DIR` from Task 1.
- Produces: `liv_registry() -> dict[str, dict]` in the test file, keyed by variant (`""` for the layout itself), values `{"brief": str | None, "description": str, "languages": list[str]}`; `linux/rules/evdev.xml` with the marker (Task 3's installer relies on it).

- [ ] **Step 1: Extend the tests**

Set `VARIANTS = ["", "linguistic"]`. Add ctypes bindings for `libxkbregistry.so.0`:

```python
# RXKB_CONTEXT_NO_DEFAULT_INCLUDES = 1
# rxkb_context_new(c_int) -> c_void_p;  rxkb_context_unref(c_void_p)
# rxkb_context_include_path_append(c_void_p, c_char_p) -> c_bool
# rxkb_context_parse(c_void_p, c_char_p) -> c_bool          # ruleset "evdev"
# rxkb_layout_first(c_void_p) -> c_void_p;  rxkb_layout_next(c_void_p) -> c_void_p
# rxkb_layout_get_name / _get_variant / _get_brief / _get_description(c_void_p) -> c_char_p   (variant is NULL for the layout itself)
# rxkb_layout_get_iso639_first(c_void_p) -> c_void_p;  rxkb_iso639_code_next(c_void_p) -> c_void_p
# rxkb_iso639_code_get_code(c_void_p) -> c_char_p
```

`liv_registry()` parses with include paths `XKB_DIR` then `SYSTEM_XKB_DIR` (the same way KDE's keyboard settings do, DTD validation included) and keeps the entries named `liv`.

```python
def test_registry_lists_liv(self):
	registry = liv_registry()
	self.assertEqual(registry[""]["brief"], "liv")
	self.assertEqual(registry[""]["description"], "Livonian")
	self.assertEqual(registry[""]["languages"], ["liv"])
	self.assertEqual(registry["linguistic"]["description"], "Livonian (linguistic)")

def test_registry_matches_tested_variants(self):
	self.assertEqual(sorted(liv_registry()), sorted(VARIANTS))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -I test/linux_layout_test.py`
Expected: FAIL: `keymap for liv(linguistic) did not compile`, and both registry tests fail (`KeyError: ''`).

- [ ] **Step 3: Port the linguistic section**

Copy `livlinguapxtd` from `git show HEAD:linux/symbols/lv | sed -n 212,315p` into `linux/symbols/liv` after `basic`, with a one-line comment above it saying what the variant adds. Then:

- section name `"linguistic"`, `name[Group1] = "Livonian (linguistic)";`
- delete `modifier_map Mod3 { <TLDE> };`
- move `<AC11>` under `EIGHT_LEVEL` as `[ISO_Level3_Latch, quotedbl, apostrophe, quotedbl, apostrophe, quotedbl]`
- give all 26 letter keys six symbols: fill levels 5/6 with the plain letter where there's no backtick character
- drop commented-out dead code (`//key <TLDE> …`, `//modifier_map Mod5 …`, `//key <SPCE> …`)

- [ ] **Step 4: Create `linux/rules/evdev.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xkbConfigRegistry SYSTEM "xkb.dtd">
<!-- livonian-keyboard -->
<xkbConfigRegistry version="1.1">
	<layoutList>
		<layout>
			<configItem>
				<name>liv</name>
				<shortDescription>liv</shortDescription>
				<description>Livonian</description>
				<languageList>
					<iso639Id>liv</iso639Id>
				</languageList>
			</configItem>
			<variantList>
				<variant>
					<configItem>
						<name>linguistic</name>
						<description>Livonian (linguistic)</description>
					</configItem>
				</variant>
			</variantList>
		</layout>
	</layoutList>
</xkbConfigRegistry>
```

- [ ] **Step 5: Delete the old files**

Run: `git rm linux/symbols/lv linux/rules/base.lst linux/rules/base.xml linux/rules/evdev.lst linux/.gitignore` (the old `linux/rules/evdev.xml` was overwritten in Step 4).
Expected: `git status` shows only these deletions plus the Task 2 changes.

- [ ] **Step 6: Run the tests to verify they pass**

Add `libxkbregistry0` to the apt line in `.github/workflows/ci.yml`.
Run: `python3 -I test/linux_layout_test.py`
Expected: `OK`, 9 tests.

- [ ] **Step 7: Commit**

```bash
git add -A linux test/linux_layout_test.py .github/workflows/ci.yml
git commit -m "Linux: Add the linguistic variant and a user-level registry" -m "..." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Installer, its tests, and docs

**Files:**

- Create: `linux/install.sh` (mode 755)
- Create: `test/linux_install_test.py`
- Modify: `package.json` (`linux-test`)
- Modify: `README.md` (new "Linux" section after "Chrome extension")
- Modify: `AGENTS.md`

**Interfaces:**

- Consumes: the two marker files from Tasks 1–2.
- Produces: `linux/install.sh [--uninstall]`: exit 0 success, 1 a foreign file is in the way, 2 bad usage (usage text on stderr). Target `${XDG_CONFIG_HOME:-$HOME/.config}/xkb`. Files `symbols/liv`, `rules/evdev.xml`.

- [ ] **Step 1: Write the failing tests**

In `setUp`, a `tempfile.TemporaryDirectory` with `home/` and `config dir/` (with the space). Method `run_script(self, *args, xdg=True) -> subprocess.CompletedProcess` (not `run`: `unittest.TestCase.run` already exists) runs `bash linux/install.sh *args` with `env = {"PATH": os.environ["PATH"], "HOME": home}`, plus `XDG_CONFIG_HOME = config dir` when `xdg`, `capture_output=True, text=True`. `self.target = config_dir / "xkb"`. `FILES = ["symbols/liv", "rules/evdev.xml"]`.

```python
def test_install_copies_files(self):
	result = self.run_script()
	self.assertEqual(result.returncode, 0)
	# for f in FILES: target file bytes == (REPO / "linux" / f) bytes
	self.assertIn("Livonian", result.stdout)
	self.assertIn("gsettings", result.stdout)

def test_install_replaces_own_files(self):
	# write "// livonian-keyboard\nold\n" to target symbols/liv and "<!-- livonian-keyboard -->\n" to target rules/evdev.xml
	self.assertEqual(self.run_script().returncode, 0)
	# both targets now equal the repo files

def test_install_aborts_on_foreign_evdev_xml(self):
	# write "<xkbConfigRegistry/>\n" to target rules/evdev.xml
	result = self.run_script()
	self.assertEqual(result.returncode, 1)
	self.assertIn("<name>liv</name>", result.stderr)  # the <layout> block to add by hand
	# foreign file unchanged; target symbols/liv does not exist

def test_install_aborts_on_foreign_symbols(self):
	# write "xkb_symbols \"basic\" {};\n" to target symbols/liv
	self.assertEqual(self.run_script().returncode, 1)
	# foreign file unchanged; target rules/evdev.xml does not exist

def test_uninstall_removes_own_files_only(self):
	self.run_script()
	# write target symbols/custom (foreign)
	self.assertEqual(self.run_script("--uninstall").returncode, 0)
	# symbols/liv and rules/evdev.xml gone, rules/ dir gone, symbols/custom still there

def test_uninstall_leaves_foreign_files(self):
	# write foreign target rules/evdev.xml
	self.assertEqual(self.run_script("--uninstall").returncode, 0)
	# foreign file unchanged

def test_uninstall_twice_is_noop(self):
	self.run_script()
	self.run_script("--uninstall")
	self.assertEqual(self.run_script("--uninstall").returncode, 0)
	self.assertFalse(self.target.exists())

def test_default_target_is_home_config(self):
	self.assertEqual(self.run_script(xdg=False).returncode, 0)
	# home/.config/xkb/symbols/liv exists

def test_unknown_argument(self):
	result = self.run_script("--frobnicate")
	self.assertEqual(result.returncode, 2)
	self.assertIn("Usage", result.stderr)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -I test/linux_install_test.py`
Expected: FAIL, `bash: linux/install.sh: No such file or directory` (non-zero return codes).

- [ ] **Step 3: Write `linux/install.sh`**

`#!/usr/bin/env bash`, `set -euo pipefail`, source dir from `$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")`, quote every path.

- Install: check **every** target first. A target that exists and fails `grep -qF livonian-keyboard` is a conflict: name it on stderr; for `rules/evdev.xml` also print the source's `<layout>…</layout>` block (`sed -n '/<layout>/,/<\/layout>/p'`) with "add this inside the <layoutList> of that file". Any conflict → exit 1 before writing anything. Otherwise `install -D -m 644` each file and print to stdout:

```
Livonian keyboard layout installed in <target>.
KDE Plasma: System Settings > Keyboard > Layouts > Add, then pick "Livonian".
GNOME: add ('xkb', 'liv') to your input sources, e.g.
  gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('xkb', 'liv')]"
  (list your current ones with: gsettings get org.gnome.desktop.input-sources sources)
If the layout doesn't show up, log out and back in. Works in Wayland sessions only.
```

- `--uninstall`: remove each target that contains the marker; for a foreign one, say on stderr that it's left alone. Then `rmdir` `rules`, `symbols` and the `xkb` dir if they exist and are empty.
- Anything else: usage on stderr, exit 2.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -I test/linux_install_test.py`
Expected: `OK`, 9 tests.

- [ ] **Step 5: Wire up and document**

- `package.json`: `"linux-test": "python3 -I test/linux_layout_test.py && python3 -I test/linux_install_test.py"`.
- `README.md` "Linux" section: install with `linux/install.sh` (no root; writes `~/.config/xkb/symbols/liv` and `~/.config/xkb/rules/evdev.xml`), then add "Livonian" in KDE settings or with `gsettings` on GNOME; manual install = copy those two files; uninstall with `linux/install.sh --uninstall`; Wayland only, X11 sessions aren't supported; the "Livonian (linguistic)" variant; the known difference: in the default layout `'` + a digit or punctuation types the Latvian AltGr symbol (e.g. `'1` → `¹`), because AltGr and the apostrophe share level 3. Add `npm run linux-test` to "Development".
- `AGENTS.md`: `linux/` bullet → "`symbols/liv` (layout `liv`, variants `basic` and `linguistic`) and `rules/evdev.xml`, mirroring `~/.config/xkb`; `install.sh` installs them per user"; test bullets for both Python tests; command `npm run linux-test`; conventions: "Keep `linux/symbols/liv` in step with `deadKeyMap`; `npm run linux-test` checks it", "Keys redefined after an `include` need an explicit `key.type`", "No `modifier_map` on the latch keys: it stops latches from clearing".

Run: `source ~/.nvm/nvm.sh && nvm use && npm run linux-test && npm test && npx prettier --check .`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add linux/install.sh test/linux_install_test.py package.json README.md AGENTS.md
git commit -m "Linux: Add a per-user installer" -m "..." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Check it on the real desktop

No code. Needs the author at the keyboard (KDE Plasma 6.8, Wayland).

- [ ] **Step 1: Install for real**

Run: `linux/install.sh`
Expected: exit 0, files in `~/.config/xkb/`.

- [ ] **Step 2: Check the registry with default include paths, as KDE sees it**

Run: a `python3 -I -c` one-liner with the Task 2 libxkbregistry bindings, `rxkb_context_new(0)`, `rxkb_context_parse(ctx, b"evdev")`, printing the `liv` entries.
Expected: `liv Livonian` and `liv linguistic Livonian (linguistic)`.

- [ ] **Step 3: Author checks by hand**

System Settings → Keyboard → Layouts → Add → "Livonian" (and the linguistic variant). Type the README rows (`'` + each letter, `` ` `` + q w p j x m, with Shift and Caps Lock) in a Wayland app (Kate) and an XWayland app (`QT_QPA_PLATFORM=xcb kwrite`). Switch between the first layout and Livonian.
Expected: output matches the README tables in both apps.
