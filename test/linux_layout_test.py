#!/usr/bin/env python3
# Tests the XKB layout in linux/ with the system libxkbcommon, against the
# bookmarklet's deadKeyMap. Run: python3 -I test/linux_layout_test.py

import ctypes
import functools
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
XKB_DIR = REPO / "linux"
SYSTEM_XKB_DIR = "/usr/share/X11/xkb"
VARIANTS = [""]

LETTER_KEYS = {
	letter: f"{row}{i + 1:02d}"
	for row, letters in (("AD", "qwertyuiop"), ("AC", "asdfghjkl"), ("AB", "zxcvbnm"))
	for i, letter in enumerate(letters)
}
DEAD_KEYS = {"'": "AC11", "`": "TLDE"}

xkb = ctypes.CDLL("libxkbcommon.so.0")


class RuleNames(ctypes.Structure):
	_fields_ = [(f, ctypes.c_char_p) for f in ("rules", "model", "layout", "variant", "options")]


XKB_CONTEXT_NO_DEFAULT_INCLUDES = 1  # keeps the developer's ~/.config/xkb out of the test
XKB_KEY_UP, XKB_KEY_DOWN = 0, 1
XKB_KEYCODE_INVALID = 0xFFFFFFFF

xkb.xkb_context_new.argtypes = [ctypes.c_int]
xkb.xkb_context_new.restype = ctypes.c_void_p
xkb.xkb_context_include_path_append.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
xkb.xkb_context_include_path_append.restype = ctypes.c_int
xkb.xkb_keymap_new_from_names.argtypes = [ctypes.c_void_p, ctypes.POINTER(RuleNames), ctypes.c_int]
xkb.xkb_keymap_new_from_names.restype = ctypes.c_void_p
xkb.xkb_keymap_key_by_name.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
xkb.xkb_keymap_key_by_name.restype = ctypes.c_uint32
xkb.xkb_state_new.argtypes = [ctypes.c_void_p]
xkb.xkb_state_new.restype = ctypes.c_void_p
xkb.xkb_state_unref.argtypes = [ctypes.c_void_p]
xkb.xkb_state_unref.restype = None
xkb.xkb_state_update_key.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int]
xkb.xkb_state_update_key.restype = ctypes.c_int
xkb.xkb_state_update_mask.argtypes = [ctypes.c_void_p] + [ctypes.c_uint32] * 6
xkb.xkb_state_update_mask.restype = ctypes.c_int
xkb.xkb_state_key_get_utf8.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_size_t]
xkb.xkb_state_key_get_utf8.restype = ctypes.c_int


@functools.cache
def compile_keymap(layout, variant=""):
	context = xkb.xkb_context_new(XKB_CONTEXT_NO_DEFAULT_INCLUDES)
	for path in (XKB_DIR, SYSTEM_XKB_DIR):
		xkb.xkb_context_include_path_append(context, str(path).encode())
	names = RuleNames(b"evdev", b"pc105", layout.encode(), variant.encode(), None)
	keymap = xkb.xkb_keymap_new_from_names(context, ctypes.byref(names), 0)
	if not keymap:
		raise AssertionError(f"keymap for {layout}({variant}) did not compile")
	return keymap


def keycode(keymap, name):
	code = xkb.xkb_keymap_key_by_name(keymap, name.encode())
	assert code != XKB_KEYCODE_INVALID, f"no key named {name}"
	return code


def utf8(state, key):
	buffer = ctypes.create_string_buffer(16)
	xkb.xkb_state_key_get_utf8(state, key, buffer, len(buffer))
	return buffer.value.decode()


# Types the strokes and returns the text. A stroke is a key name, or a tuple
# of key names whose last key is pressed while the others are held.
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
		# Read the text before the press, as Wayland clients do. After the
		# press a latch key would report its own level 3.
		text += utf8(state, key)
		xkb.xkb_state_update_key(state, key, XKB_KEY_DOWN)
		xkb.xkb_state_update_key(state, key, XKB_KEY_UP)
		for k in reversed(held):
			xkb.xkb_state_update_key(state, k, XKB_KEY_UP)
	xkb.xkb_state_unref(state)
	return text


@functools.cache
def dead_key_map():
	source = (REPO / "bookmarklet" / "livonian-keyboard.js").read_text()
	result = {}
	for dead in DEAD_KEYS:
		block = re.search(r'"' + re.escape(dead) + r'":\s*\{(.*?)\}', source, re.S)
		result[dead] = dict(re.findall(r'(\w):\s*"(.)"', block.group(1))) if block else {}
	return result


class LayoutTest(unittest.TestCase):
	def test_dead_key_map_is_parsed(self):
		self.assertGreaterEqual(sum(len(m) for m in dead_key_map().values()), 40)

	def test_plain_letters(self):
		for variant in VARIANTS:
			with self.subTest(variant=variant):
				km = compile_keymap("liv", variant)
				for letter, key in LETTER_KEYS.items():
					self.assertEqual(type_keys(km, key), letter)
					self.assertEqual(type_keys(km, ("LFSH", key)), letter.upper())
					self.assertEqual(type_keys(km, "CAPS", key), letter.upper())

	def test_dead_key_map_entries(self):
		for variant in VARIANTS:
			with self.subTest(variant=variant):
				km = compile_keymap("liv", variant)
				for dead, mapping in dead_key_map().items():
					latch = DEAD_KEYS[dead]
					for char_key, expected in mapping.items():
						key = LETTER_KEYS[char_key.lower()]
						if char_key.islower():
							self.assertEqual(type_keys(km, latch, key), expected, f"{dead}{char_key}")
						else:
							self.assertEqual(type_keys(km, latch, ("LFSH", key)), expected, f"{dead} Shift+{char_key}")
							self.assertEqual(type_keys(km, "CAPS", latch, key), expected, f"Caps {dead}{char_key}")

	def test_unmapped_letters_pass_through(self):
		for variant in VARIANTS:
			with self.subTest(variant=variant):
				km = compile_keymap("liv", variant)
				for dead, latch in DEAD_KEYS.items():
					for letter, key in LETTER_KEYS.items():
						if letter in dead_key_map()[dead]:
							continue
						self.assertEqual(type_keys(km, latch, key), letter, f"{dead}{letter}")
						self.assertEqual(type_keys(km, latch, ("LFSH", key)), letter.upper(), f"{dead} Shift+{letter}")
						self.assertEqual(type_keys(km, "CAPS", latch, key), letter.upper(), f"Caps {dead}{letter}")

	def test_dead_key_combinations(self):
		cases = {
			("AC11", "AC11"): "'",
			("TLDE", "TLDE"): "`",
			("AC11", "SPCE"): "'",
			("TLDE", "SPCE"): "`",
			("AC11", "TLDE"): "`",
			("TLDE", "AC11"): "'",
		}
		for variant in VARIANTS:
			with self.subTest(variant=variant):
				km = compile_keymap("liv", variant)
				for keys, expected in cases.items():
					self.assertEqual(type_keys(km, *keys, "AD01"), expected + "q", keys)

	def test_latch_cleared_after_one_key(self):
		for variant in VARIANTS:
			with self.subTest(variant=variant):
				km = compile_keymap("liv", variant)
				self.assertEqual(type_keys(km, "AC11", "AD01", "AD01"), "äq")
				self.assertEqual(type_keys(km, "TLDE", "AD01", "AD01"), "ǟq")

	def test_second_layout(self):
		for variant in VARIANTS:
			for first in ("us", "lv"):
				with self.subTest(variant=variant, first=first):
					km = compile_keymap(f"{first},liv", f",{variant}")
					self.assertEqual(type_keys(km, "AD01", layout_index=1), "q")
					self.assertEqual(type_keys(km, "AC11", "AD01", layout_index=1), "ä")
					self.assertEqual(type_keys(km, "TLDE", "AB02", layout_index=1), "ȫ")


if __name__ == "__main__":
	unittest.main()
