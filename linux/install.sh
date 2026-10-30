#!/usr/bin/env bash
# Installs the Livonian keyboard layout for the current user, no root needed.
# libxkbcommon (Wayland compositors) and libxkbregistry (keyboard settings)
# read ~/.config/xkb before the system XKB files.
#
# Usage: linux/install.sh [--uninstall]

set -euo pipefail

SOURCE="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
TARGET="$CONFIG/xkb"
FILES=(symbols/liv rules/evdev.xml)
MARKER="livonian-keyboard"

usage() {
	echo "Usage: $0 [--uninstall]" >&2
	exit 2
}

# Our files carry the marker. A registry file with more layouts than ours has
# the user's own additions, so it isn't ours to replace or remove.
is_ours() {
	grep -qF "$MARKER" "$1" && (($(grep -c '<layout>' "$1") <= 1))
}

# Prints where Livonian is still among the user's keyboard layouts
configured_in() {
	local sources
	if [[ -f "$CONFIG/kxkbrc" ]] && grep -Eq '^LayoutList=(.*,)?liv(,|$)' "$CONFIG/kxkbrc"; then
		echo "  KDE Plasma: System Settings > Keyboard > Layouts"
	fi
	if command -v gsettings >/dev/null; then
		sources="$(gsettings get org.gnome.desktop.input-sources sources 2>/dev/null || true)"
		if grep -Eq "'liv(\+[^']*)?'" <<<"$sources"; then
			echo "  GNOME: Settings > Keyboard > Input Sources"
		fi
	fi
}

install_layout() {
	local file conflict=0
	# Check every target before writing anything
	for file in "${FILES[@]}"; do
		if [[ -e "$TARGET/$file" ]] && ! is_ours "$TARGET/$file"; then
			conflict=1
			echo "$TARGET/$file isn't the file this script installed, leaving it alone." >&2
			if [[ "$file" == rules/evdev.xml ]]; then
				echo "To install by hand, add this inside the <layoutList> of that file:" >&2
				sed -n '/<layout>/,/<\/layout>/p' "$SOURCE/$file" >&2
				echo "and copy the symbols file:" >&2
				echo "  mkdir -p \"$TARGET/symbols\" && cp \"$SOURCE/symbols/liv\" \"$TARGET/symbols/liv\"" >&2
			fi
		fi
	done
	if ((conflict)); then
		exit 1
	fi

	# Compositors only search ~/.config/xkb if it existed when the session
	# started, so a new directory needs a new session. A restart, because
	# logging straight back in can reuse the old, half-closed user session
	# and hang the desktop's start-up.
	local new_dir=0
	if [[ ! -d "$TARGET" ]]; then
		new_dir=1
	fi
	for file in "${FILES[@]}"; do
		install -D -m 644 "$SOURCE/$file" "$TARGET/$file"
	done

	# The backtick latch needs the <LVL5> mapping that the system pc symbols
	# got in xkeyboard-config 2.37. libxkbcommon reads them from here.
	local pc="${XKB_CONFIG_ROOT:-/usr/share/X11/xkb}/symbols/pc"
	if [[ -f "$pc" ]] && ! grep -qF '<LVL5>' "$pc"; then
		echo "Warning: your xkeyboard-config (xkb-data) is older than 2.37, so the backtick dead key won't work. The apostrophe dead key does." >&2
	fi

	echo "Livonian keyboard layout installed in $TARGET."
	if ((new_dir)); then
		echo "Restart your computer before adding the layout: your desktop only looks in $TARGET if it existed when your session started."
	fi
	cat <<EOF
KDE Plasma: System Settings > Keyboard > Layouts > Add, then pick "Livonian".
GNOME: add ('xkb', 'liv') to your input sources, e.g.
  gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('xkb', 'liv')]"
  (list your current ones with: gsettings get org.gnome.desktop.input-sources sources)
Works in Wayland sessions only.
EOF
}

uninstall_layout() {
	local file dir places
	# Without its files the desktop can't build a keymap that lists Livonian,
	# and falls back to a default layout, dropping all of the user's layouts
	places="$(configured_in)"
	if [[ -n "$places" ]]; then
		echo "Remove Livonian from your keyboard layouts first, then run this again:" >&2
		echo "$places" >&2
		exit 1
	fi

	for file in "${FILES[@]}"; do
		if [[ ! -e "$TARGET/$file" ]]; then
			continue
		elif is_ours "$TARGET/$file"; then
			rm "$TARGET/$file"
		else
			echo "$TARGET/$file isn't the file this script installed, leaving it alone." >&2
		fi
	done
	# Remove the directories only if nothing else is in them
	for dir in "$TARGET/rules" "$TARGET/symbols" "$TARGET"; do
		if [[ -d "$dir" ]]; then
			rmdir --ignore-fail-on-non-empty "$dir"
		fi
	done
	echo "Livonian keyboard layout removed from $TARGET."
}

if (($# > 1)); then
	usage
fi

if [[ "$(id -u)" == 0 ]]; then
	echo "Run this as your own user, without sudo: it installs the layout into your home directory." >&2
	exit 1
fi

case "${1-}" in
"") install_layout ;;
--uninstall) uninstall_layout ;;
*) usage ;;
esac
