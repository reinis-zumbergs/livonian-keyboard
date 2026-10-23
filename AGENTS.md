# Agent Instructions

Livonian keyboard layout: apostrophe (`'`) and backtick (`` ` ``) are dead keys that add diacritics to the next letter. It ships as a bookmarklet, a Chrome extension built from the same script, and an XKB layout for Linux.

## Layout

- `bookmarklet/livonian-keyboard.js`: the keyboard logic. Make all functionality changes here.
- `bookmarklet/livonian-keyboard.min.js`: generated, don't edit.
- `bookmarklet/BOOKMARKLET.md`: the bookmarklet install page, served on GitHub Pages. Its `javascript:` link is generated from the minified script, don't edit it by hand.
- `chrome-extension/`: Manifest V3 extension. `scripts/content.js` is a gitignored copy of the minified script.
- `linux/`: XKB rules and the `lv` symbols file with the Livonian variant.
- `test/livonian-keyboard.test.js`: Jest tests, running the source script in jsdom.

## Commands

Use the Node version from `.nvmrc`. In non-interactive shells load nvm first: `source ~/.nvm/nvm.sh && nvm use`.

- `npm test`: run the Jest tests
- `npm run bookmarklet-minify`: regenerate the minified script
- `npm run bookmarklet-link`: regenerate the link in `BOOKMARKLET.md` from the minified script
- `npm run prettier`: format everything
- `npm run chrome-extension-all`: copy the script into the extension and package it as a zip

The Husky pre-commit hook runs Prettier and, when `livonian-keyboard.js` is staged, regenerates and stages the minified script and the bookmarklet link. CI (`.github/workflows/ci.yml`) checks formatting, runs the tests and fails if the generated files are stale.

## Conventions

- Prettier with tabs. End every file with a newline.
- Keep the bookmarklet code in a single IIFE, so it doesn't leak globals into the page.
- Add new characters to the `deadKeyMap` object, with uppercase variants, and update the layout tables in `README.md` to match.
- Check that DOM elements exist before modifying them.
- Bind the keydown handler in the capturing phase, so pages that stop propagation (e.g. Gmail) can't block it.
- Mark attached documents with the `data-livonian-keyboard` attribute, not a JS property, so separate script instances (the extension runs in every frame) see the mark.
- Find dynamically added iframes with the periodic `setInterval` check. Cross-origin iframes are skipped.
- Supported inputs get the Sierra Leone flag emoji (🇸🇱) as a background image.

## Testing

Add or update Jest tests for behaviour changes. For manual testing, run the bookmarklet code on `bookmarklet/test-inputs.html`.
