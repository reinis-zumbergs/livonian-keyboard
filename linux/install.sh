#!/usr/bin/env bash
# Installs the Livonian keyboard layout for the current user, no root needed.
# libxkbcommon (Wayland compositors) and libxkbregistry (keyboard settings)
# read ~/.config/xkb before the system XKB files.
#
# Usage: linux/install.sh [--uninstall]

set -euo pipefail

SOURCE="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
TARGET="${XDG_CONFIG_HOME:-$HOME/.config}/xkb"
FILES=(symbols/liv rules/evdev.xml)
# Our files contain this marker; files without it belong to someone else
MARKER="livonian-keyboard"

usage() {
	echo "Usage: $0 [--uninstall]" >&2
	exit 2
}

install_layout() {
	local file conflict=0
	# Check every target before writing anything
	for file in "${FILES[@]}"; do
		if [[ -e "$TARGET/$file" ]] && ! grep -qF "$MARKER" "$TARGET/$file"; then
			conflict=1
			echo "$TARGET/$file exists and wasn't installed by this script, leaving it alone." >&2
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

	for file in "${FILES[@]}"; do
		install -D -m 644 "$SOURCE/$file" "$TARGET/$file"
	done

	cat <<EOF
Livonian keyboard layout installed in $TARGET.
KDE Plasma: System Settings > Keyboard > Layouts > Add, then pick "Livonian".
GNOME: add ('xkb', 'liv') to your input sources, e.g.
  gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('xkb', 'liv')]"
  (list your current ones with: gsettings get org.gnome.desktop.input-sources sources)
If the layout doesn't show up, log out and back in. Works in Wayland sessions only.
EOF
}

uninstall_layout() {
	local file dir
	for file in "${FILES[@]}"; do
		if [[ ! -e "$TARGET/$file" ]]; then
			continue
		elif grep -qF "$MARKER" "$TARGET/$file"; then
			rm "$TARGET/$file"
		else
			echo "$TARGET/$file wasn't installed by this script, leaving it alone." >&2
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

case "${1-}" in
"") install_layout ;;
--uninstall) uninstall_layout ;;
*) usage ;;
esac
