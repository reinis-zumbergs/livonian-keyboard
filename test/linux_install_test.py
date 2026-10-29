#!/usr/bin/env python3
# Tests linux/install.sh against temporary home and config directories.
# Run: python3 -I test/linux_install_test.py

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "linux" / "install.sh"
FILES = ["symbols/liv", "rules/evdev.xml"]


class InstallTest(unittest.TestCase):
	def setUp(self):
		tmp = tempfile.TemporaryDirectory()
		self.addCleanup(tmp.cleanup)
		self.home = Path(tmp.name) / "home"
		self.config = Path(tmp.name) / "config dir"
		self.home.mkdir()
		self.config.mkdir()
		self.target = self.config / "xkb"

	def run_script(self, *args, xdg=True):
		env = {"PATH": os.environ["PATH"], "HOME": str(self.home)}
		if xdg:
			env["XDG_CONFIG_HOME"] = str(self.config)
		return subprocess.run(["bash", str(SCRIPT), *args], env=env, capture_output=True, text=True)

	def write_target(self, name, text):
		path = self.target / name
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(text)
		return path

	def assert_installed(self, target):
		for name in FILES:
			self.assertEqual((target / name).read_bytes(), (REPO / "linux" / name).read_bytes(), name)

	def test_install_copies_files(self):
		result = self.run_script()
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assert_installed(self.target)
		self.assertIn("Livonian", result.stdout)
		self.assertIn("gsettings", result.stdout)

	def test_install_replaces_own_files(self):
		self.write_target("symbols/liv", "// livonian-keyboard\nold\n")
		self.write_target("rules/evdev.xml", "<!-- livonian-keyboard -->\n")
		result = self.run_script()
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assert_installed(self.target)

	def test_install_aborts_on_foreign_evdev_xml(self):
		foreign = self.write_target("rules/evdev.xml", "<xkbConfigRegistry/>\n")
		result = self.run_script()
		self.assertEqual(result.returncode, 1)
		self.assertIn("<name>liv</name>", result.stderr)
		# Running the script again would still find the file foreign, so
		# the message says how to finish by hand
		self.assertIn(f'cp "{REPO / "linux/symbols/liv"}" "{self.target / "symbols/liv"}"', result.stderr)
		self.assertNotIn("run the script again", result.stderr)
		self.assertEqual(foreign.read_text(), "<xkbConfigRegistry/>\n")
		self.assertFalse((self.target / "symbols/liv").exists())

	def test_install_aborts_on_foreign_symbols(self):
		foreign = self.write_target("symbols/liv", 'xkb_symbols "basic" {};\n')
		self.assertEqual(self.run_script().returncode, 1)
		self.assertEqual(foreign.read_text(), 'xkb_symbols "basic" {};\n')
		self.assertFalse((self.target / "rules/evdev.xml").exists())

	def test_uninstall_removes_own_files_only(self):
		self.run_script()
		custom = self.write_target("symbols/custom", 'xkb_symbols "basic" {};\n')
		self.assertEqual(self.run_script("--uninstall").returncode, 0)
		for name in FILES:
			self.assertFalse((self.target / name).exists(), name)
		self.assertFalse((self.target / "rules").exists())
		self.assertTrue(custom.exists())

	def test_uninstall_leaves_foreign_files(self):
		foreign = self.write_target("rules/evdev.xml", "<xkbConfigRegistry/>\n")
		self.assertEqual(self.run_script("--uninstall").returncode, 0)
		self.assertEqual(foreign.read_text(), "<xkbConfigRegistry/>\n")

	def test_uninstall_twice_is_noop(self):
		self.run_script()
		self.run_script("--uninstall")
		self.assertEqual(self.run_script("--uninstall").returncode, 0)
		self.assertFalse(self.target.exists())

	def test_default_target_is_home_config(self):
		result = self.run_script(xdg=False)
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assert_installed(self.home / ".config" / "xkb")

	def test_unknown_argument(self):
		result = self.run_script("--frobnicate")
		self.assertEqual(result.returncode, 2)
		self.assertIn("Usage", result.stderr)


if __name__ == "__main__":
	unittest.main()
