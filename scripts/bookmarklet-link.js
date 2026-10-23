// Replace the bookmarklet link in BOOKMARKLET.md with the minified script,
// so the link always installs the current version.
const fs = require("fs");
const path = require("path");

const MINIFIED = path.join(
	__dirname,
	"../bookmarklet/livonian-keyboard.min.js",
);
const PAGE = path.join(__dirname, "../bookmarklet/BOOKMARKLET.md");
const LINK = /^(\[Activate Livonian Keyboard Layout\]\(javascript:).*\)$/m;

const code = fs.readFileSync(MINIFIED, "utf8").trim();
const page = fs.readFileSync(PAGE, "utf8");

if (!LINK.test(page)) {
	console.error(`Bookmarklet link not found in ${PAGE}`);
	process.exit(1);
}

// Use a replacer function, so "$" in the code isn't read as a pattern
fs.writeFileSync(
	PAGE,
	page.replace(LINK, (match, prefix) => `${prefix}${code})`),
);
