# Livonian Keyboard Layout

This Livonian keyboard layout is an expansion of the widely used Latvian (apostrophe) keyboard layout. With this layout apostrophe and backtick become dead keys for entering diacritics.

Livonian is meant to be your only keyboard layout. It was designed together with the University of Latvia Livonian Institute and Valts Ernštreits to add to the Latvian layout without replacing anything in it. Every Latvian letter types the same way as before, and the Livonian letters come on top. So Latvian speakers feel at home in it straight away, and there's nothing to switch between. You don't need to keep Latvian next to it.

## Layout

### Key output without dead key

    qwertyuiop
    asdfghjkl
    zxcvbnm

### Key output after apostrophe

_Dash means that the key is not modified_

    äüēŗţȳūīōǫ
    āšḑ-ģ-ȯķļ
    žöč--ņõ

### Key output after backtick

_Dash means that the key is not modified_

    ǟǖ-------ǭ
    ------ȱ--
    -ȫ----ȭ

### Table

_Dash means that the output is not modified_

| Key | Output | After apostrophe | After backtick |
| --- | ------ | ---------------- | -------------- |
| `   |        | `                | `              |
| '   |        | '                | '              |
| q   | q      | ä                | ǟ              |
| w   | w      | ü                | ǖ              |
| e   | e      | ē                | -              |
| r   | r      | ŗ                | -              |
| t   | t      | ţ                | -              |
| y   | y      | ȳ                | -              |
| u   | u      | ū                | -              |
| i   | i      | ī                | -              |
| o   | o      | ō                | -              |
| p   | p      | ǫ                | ǭ              |
| a   | a      | ā                | -              |
| s   | s      | š                | -              |
| d   | d      | ḑ                | -              |
| f   | f      | -                | -              |
| g   | g      | ģ                | -              |
| h   | h      | -                | -              |
| j   | j      | ȯ                | ȱ              |
| k   | k      | ķ                | -              |
| l   | l      | ļ                | -              |
| z   | z      | ž                | -              |
| x   | x      | ö                | ȫ              |
| c   | c      | č                | -              |
| v   | v      | -                | -              |
| b   | b      | -                | -              |
| n   | n      | ņ                | -              |
| m   | m      | õ                | ȭ              |

## Bookmarklet

Bookmarklet is an easy, no-installation method of temporarily enabling the Livonian keyboard layout on (almost) any website. Use it with the standard US keyboard layout as your system layout: it conflicts with system layouts that already have dead keys, such as Latvian (apostrophe). For instructions, see the [bookmarklet page](https://reinis-zumbergs.github.io/livonian-keyboard/bookmarklet/BOOKMARKLET.html).

## Chrome extension

The Chrome extension enables the Livonian keyboard layout on all websites. Like the bookmarklet, it needs the standard US keyboard layout as your system layout. It is not yet published in the Chrome Web Store. To install it from source:

1. Run `npm install` and `npm run chrome-extension-prepare`.
2. Open `chrome://extensions`, enable "Developer mode" and click "Load unpacked".
3. Select the `chrome-extension` directory.

To package the extension into `livonian-keyboard-chrome-extension.zip` for the Chrome Web Store, run `npm run chrome-extension-all`.

## Linux

The Linux layout is an XKB keyboard layout called "Livonian" (`liv`). It installs for your user only, without root and without changing the system's keyboard files. It works in Wayland sessions (KDE Plasma, GNOME and other desktops whose compositor uses libxkbcommon), in both Wayland and X11 apps. It's tested with KDE Plasma 6.6 and 6.8.

X11 sessions aren't supported: adding Livonian to your layouts in an X11 session makes all your layouts stop working, and only the system's default one is left. To recover, log in to the Wayland session (in KDE: "Plasma (Wayland)"), where all your layouts work, or remove Livonian from your layouts. The install script warns when your desktop runs an X11 session. Plasma 6.8 no longer has an X11 session, so this only applies to Plasma 6.7 and older, and to other desktops that still offer one.

The backtick dead key needs xkeyboard-config (the `xkb-data` package) 2.37 or newer, e.g. Ubuntu 24.04 or Debian 13. On older systems, such as Ubuntu 22.04 or Debian 12, only the apostrophe dead key works, and the install script warns about it.

To install it, run this as your own user, without `sudo`:

    linux/install.sh

This copies `linux/symbols/liv` to `~/.config/xkb/symbols/liv` and `linux/rules/evdev.xml` to `~/.config/xkb/rules/evdev.xml` (or under `$XDG_CONFIG_HOME` if it's set). You can also copy the two files there by hand. Then add the layout:

- KDE Plasma: System Settings > Keyboard > Layouts > Add, then pick "Livonian".
- GNOME: Settings may not list it, so set it with `gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'liv')]"`. If you also write in other languages, list your current input sources first (`gsettings get org.gnome.desktop.input-sources sources`) and keep those in the list.

Livonian replaces Latvian in your layout list, so you can remove Latvian once Livonian is added. With "Livonian", the apostrophe types the Latvian letters as in Latvian (apostrophe) and AltGr types them as in Latvian (QWERTY). "Livonian (linguistic)" types them with the apostrophe only. Keep your other layouts only if you write in other languages, e.g. Russian.

If `~/.config/xkb` didn't exist before, restart your computer before adding the layout: the desktop only looks there if the folder existed when your session started. Restart rather than log out, because logging straight back in can hang the desktop's start-up. If you're in an X11 session, choose the Wayland session on the login screen: it starts the session type you used last. Without the restart, it fails to load the layouts that include Livonian and keeps your previous ones. If you already have your own `~/.config/xkb/rules/evdev.xml`, the script leaves it alone and prints what to add to it.

To uninstall, first remove Livonian from your keyboard layouts (KDE System Settings or GNOME input sources), then run `linux/install.sh --uninstall`. Otherwise your desktop can't load your layouts at the next login and falls back to a default one, so the script refuses while Livonian is still in your layouts. It removes only the files it installed.

If you used the older Livonian layout that replaced the system's keyboard files in `/usr/share/X11/xkb` (the Latvian variants "Livonian (apostrophe+tilde)" and "Livonian Linguistic ApXTd"), move to this one: the next `xkb-data` update overwrites those files, and the old variants disappear. In a Wayland session, install this layout, add "Livonian" (or "Livonian (linguistic)" in place of "Livonian Linguistic ApXTd"), and remove the old variants from your layouts. Then restore the system files with `sudo apt install --reinstall xkb-data` (on other distributions, reinstall `xkeyboard-config`). Remove the old variants first: a layout list that names a variant that no longer exists doesn't load at all, the other layouts in it included. "Livonian (apostrophe+tilde)" never fully worked in Wayland sessions, so "Livonian" replaces it.

Apostrophe and backtick work as in the tables above. Unlike the bookmarklet, an apostrophe before a digit or punctuation key types that key's AltGr symbol (e.g. `'1` types `¹`), because AltGr and the apostrophe share the same key level.

The "Livonian (linguistic)" variant has no Latvian AltGr letters. Instead, apostrophe before the number row and punctuation keys types typographic symbols (superscripts, fractions, guillemets, dashes), and Shift+Space types a no-break space.

Some fonts lack the rarer Livonian letters. Hack, KDE's default monospace font, has no ǟ Ǟ ȭ Ȭ, so code editors and terminals take them from another font, where Ǟ and Ȭ may look as if they had no macron (cut off by the line height). The text itself is correct.

## Development

The keyboard logic lives in `bookmarklet/livonian-keyboard.js`. The minified version and the link on the bookmarklet page are generated on commit. Run the tests with `npm test`, and test manually with `bookmarklet/test-inputs.html`. The Linux layout lives in `linux/symbols/liv`. `npm run linux-test` checks it against the bookmarklet with the system libxkbcommon, and tests the install script.

## TODO

- Publish Chrome extension in the Chrome Web Store
- Firefox extension
- Microsoft Edge extension
- Safari extension

## License

This project is licensed under the MIT License.
