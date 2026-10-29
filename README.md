# Livonian Keyboard Layout

This Livonian keyboard layout is an expansion of the widely used Latvian (apostrophe) keyboard layout. With this layout apostrophe and backtick become dead keys for entering diacritics. The layout is designed to be used with the standard US keyboard layout.

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

Bookmarklet is an easy, no-installation method of temporarily enabling the Livonian keyboard layout on (almost) any website. For instructions, see the [bookmarklet page](https://reinis-zumbergs.github.io/livonian-keyboard/bookmarklet/BOOKMARKLET.html).

## Chrome extension

The Chrome extension enables the Livonian keyboard layout on all websites. It is not yet published in the Chrome Web Store. To install it from source:

1. Run `npm install` and `npm run chrome-extension-prepare`.
2. Open `chrome://extensions`, enable "Developer mode" and click "Load unpacked".
3. Select the `chrome-extension` directory.

To package the extension into `livonian-keyboard-chrome-extension.zip` for the Chrome Web Store, run `npm run chrome-extension-all`.

## Linux

The Linux layout is an XKB keyboard layout called "Livonian" (`liv`). It installs for your user only, without root and without changing the system's keyboard files. It works in Wayland sessions (KDE Plasma, GNOME and other desktops whose compositor uses libxkbcommon), in both Wayland and X11 apps. X11 sessions aren't supported.

The backtick dead key needs xkeyboard-config (the `xkb-data` package) 2.37 or newer, e.g. Ubuntu 24.04 or Debian 13. On older systems, such as Ubuntu 22.04 or Debian 12, only the apostrophe dead key works, and the install script warns about it.

To install it, run this as your own user, without `sudo`:

    linux/install.sh

This copies `linux/symbols/liv` to `~/.config/xkb/symbols/liv` and `linux/rules/evdev.xml` to `~/.config/xkb/rules/evdev.xml` (or under `$XDG_CONFIG_HOME` if it's set). You can also copy the two files there by hand. Then add the layout:

- KDE Plasma: System Settings > Keyboard > Layouts > Add, then pick "Livonian".
- GNOME: Settings may not list it, so add it to your input sources with `gsettings`, keeping your current ones (`gsettings get org.gnome.desktop.input-sources sources` lists them), e.g. `gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('xkb', 'liv')]"`.

If the layout doesn't show up, log out and back in. If you already have your own `~/.config/xkb/rules/evdev.xml`, the script leaves it alone and prints what to add to it.

To uninstall, first remove Livonian from your keyboard layouts (KDE System Settings or GNOME input sources), then run `linux/install.sh --uninstall`. Otherwise your desktop can't load your layouts at the next login and falls back to a default one, so the script refuses while Livonian is still in your layouts. It removes only the files it installed.

The layout is based on the Latvian (QWERTY) layout, so AltGr types the Latvian letters as usual. Apostrophe and backtick work as in the tables above. Unlike the bookmarklet, an apostrophe before a digit or punctuation key types that key's AltGr symbol (e.g. `'1` types `¹`), because AltGr and the apostrophe share the same key level.

The "Livonian (linguistic)" variant has no Latvian AltGr letters. Instead, apostrophe before the number row and punctuation keys types typographic symbols (superscripts, fractions, guillemets, dashes), and Shift+Space types a no-break space.

## Development

The keyboard logic lives in `bookmarklet/livonian-keyboard.js`. The minified version and the link on the bookmarklet page are generated on commit. Run the tests with `npm test`, and test manually with `bookmarklet/test-inputs.html`. The Linux layout lives in `linux/symbols/liv`. `npm run linux-test` checks it against the bookmarklet with the system libxkbcommon, and tests the install script.

## TODO

- Publish Chrome extension in the Chrome Web Store
- Firefox extension
- Microsoft Edge extension
- Safari extension

## License

This project is licensed under the MIT License.
