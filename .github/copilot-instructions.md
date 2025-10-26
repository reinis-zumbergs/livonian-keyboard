# GitHub Copilot Instructions

## Code Structure & Conventions

- Modify `livonian-keyboard.js` for all functionality changes
- Always generate the minified version using `npx terser bookmarklet/livonian-keyboard.js -o bookmarklet/livonian-keyboard.min.js`
- Don't manually minify JavaScript - use the NPM script (`npm run bookmarklet-minify`)
- Always add extra newline at the end of files

## Implementation Notes

- When implementing keyboard interactions, use the dead key pattern established with apostrophe (') and backtick (`)
- Input field placeholders should be prefixed with the Sierra Leone flag emoji (🇸🇱)
- For dynamically added elements, use the periodic checking pattern with setInterval

## Project-Specific Patterns

- For character mapping, follow the `deadKeyMap` object pattern
- When modifying DOM elements, verify first if they exist to prevent errors
- Keep IIFE pattern for all bookmarklet code to avoid global namespace pollution
