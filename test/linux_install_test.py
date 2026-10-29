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
		# Stand-ins for system commands, so the developer's desktop settings
		# can't affect the result
		self.bin = Path(tmp.name) / "bin"
		self.bin.mkdir()
		self.fake_command("gsettings", "echo \"@a(ss) []\"")

	def run_script(self, *args, xdg=True, **extra_env):
		env = {"PATH": f"{self.bin}:{os.environ['PATH']}", "HOME": str(self.home), **extra_env}
		if xdg:
			env["XDG_CONFIG_HOME"] = str(self.config)
		return subprocess.run(["bash", str(SCRIPT), *args], env=env, capture_output=True, text=True)

	def fake_command(self, name, body):
		path = self.bin / name
		path.write_text(f"#!/bin/sh\n{body}\n")
		path.chmod(0o755)

	# Adds a layout of the user's own to the installed registry file
	def add_own_layout(self):
		path = self.target / "rules/evdev.xml"
		text = path.read_text().replace(
			"\t</layoutList>",
			"\t\t<layout><configItem><name>mine</name><description>Mine</description></configItem></layout>\n\t</layoutList>",
		)
		path.write_text(text)
		return text

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
		self.assertNotIn("2.37", result.stderr)

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

	def test_install_warns_on_old_xkeyboard_config(self):
		# Before 2.37 the system pc symbols don't map <LVL5>, which the
		# backtick latch needs
		root = Path(self.home) / "xkb-root"
		(root / "symbols").mkdir(parents=True)
		(root / "symbols/pc").write_text('xkb_symbols "pc105" {\n\tkey <LVL3> {[ISO_Level3_Shift]};\n};\n')
		result = self.run_script(XKB_CONFIG_ROOT=str(root))
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assert_installed(self.target)
		self.assertIn("2.37", result.stderr)

	def test_install_keeps_edited_evdev_xml(self):
		self.run_script()
		edited = self.add_own_layout()
		self.assertEqual(self.run_script().returncode, 1)
		self.assertEqual((self.target / "rules/evdev.xml").read_text(), edited)

	def test_uninstall_keeps_edited_evdev_xml(self):
		self.run_script()
		edited = self.add_own_layout()
		self.assertEqual(self.run_script("--uninstall").returncode, 0)
		self.assertEqual((self.target / "rules/evdev.xml").read_text(), edited)

	def test_uninstall_refuses_while_in_kde_layouts(self):
		self.run_script()
		(self.config / "kxkbrc").write_text("[Layout]\nLayoutList=lv,liv\nUse=true\n")
		result = self.run_script("--uninstall")
		self.assertEqual(result.returncode, 1)
		self.assertIn("Remove Livonian", result.stderr)
		self.assert_installed(self.target)

	def test_uninstall_refuses_while_in_gnome_sources(self):
		self.run_script()
		self.fake_command("gsettings", "echo \"[('xkb', 'us'), ('xkb', 'liv+linguistic')]\"")
		result = self.run_script("--uninstall")
		self.assertEqual(result.returncode, 1)
		self.assertIn("Remove Livonian", result.stderr)
		self.assert_installed(self.target)

	def test_uninstall_ignores_other_layouts_named_like_liv(self):
		self.run_script()
		(self.config / "kxkbrc").write_text("[Layout]\nLayoutList=lv,olive\n")
		self.fake_command("gsettings", "echo \"[('xkb', 'lv'), ('xkb', 'liver')]\"")
		self.assertEqual(self.run_script("--uninstall").returncode, 0)
		self.assertFalse((self.target / "symbols/liv").exists())

	def test_refuses_to_run_as_root(self):
		self.fake_command("id", "echo 0")
		result = self.run_script()
		self.assertEqual(result.returncode, 1)
		self.assertIn("without sudo", result.stderr)
		self.assertFalse(self.target.exists())

	def test_install_into_new_config_dir_asks_to_log_out_first(self):
		# The compositor only searches ~/.config/xkb if it existed at login
		result = self.run_script()
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertIn("Log out and back in before adding", result.stdout)

	def test_install_into_existing_config_dir_needs_no_new_login(self):
		self.write_target("symbols/custom", 'xkb_symbols "basic" {};\n')
		result = self.run_script()
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertNotIn("Log out and back in before adding", result.stdout)


if __name__ == "__main__":
	unittest.main()
