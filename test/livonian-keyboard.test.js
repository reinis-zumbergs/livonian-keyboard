const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const SOURCE = fs.readFileSync(
	path.join(__dirname, "../bookmarklet/livonian-keyboard.js"),
	"utf8",
);

let dom;

// Load a page with the given body and activate the keyboard on it
function activate(body) {
	dom = new JSDOM(
		`<!doctype html><html><head></head><body>${body}</body></html>`,
		{
			runScripts: "outside-only",
		},
	);
	dom.window.console.info = () => {};
	dom.window.eval(SOURCE);
	return dom.window.document;
}

// Dispatch keydown events for each key and return the events
function press(target, ...keys) {
	const KeyboardEvent = target.ownerDocument.defaultView.KeyboardEvent;
	return keys.map((key) => {
		const event = new KeyboardEvent("keydown", {
			key,
			bubbles: true,
			cancelable: true,
		});
		target.dispatchEvent(event);
		return event;
	});
}

function focusedInput(doc, html = '<input type="text">') {
	doc.body.innerHTML = html;
	const input = doc.body.firstElementChild;
	input.focus();
	return input;
}

afterEach(() => {
	dom.window.close();
});

describe("dead keys", () => {
	test.each([
		["'", "q", "ä"],
		["'", "Q", "Ä"],
		["'", "m", "õ"],
		["`", "q", "ǟ"],
		["`", "P", "Ǭ"],
	])("%s followed by %s outputs %s", (deadKey, key, expected) => {
		const input = focusedInput(activate(""));

		const [deadKeyEvent, keyEvent] = press(input, deadKey, key);

		expect(deadKeyEvent.defaultPrevented).toBe(true);
		expect(keyEvent.defaultPrevented).toBe(true);
		expect(input.value).toBe(expected);
	});

	test("inserts the character at the cursor, replacing the selection", () => {
		const input = focusedInput(activate(""));
		input.value = "abXYcd";
		input.setSelectionRange(2, 4);

		press(input, "'", "a");

		expect(input.value).toBe("abācd");
		expect(input.selectionStart).toBe(3);
		expect(input.selectionEnd).toBe(3);
	});

	test("passes through an unmapped key after a dead key", () => {
		const input = focusedInput(activate(""));

		const [, keyEvent] = press(input, "'", "f");

		expect(keyEvent.defaultPrevented).toBe(false);
		expect(input.value).toBe("");
	});

	test("clears the dead key after the next key", () => {
		const input = focusedInput(activate(""));

		const [, , keyEvent] = press(input, "'", "f", "a");

		expect(keyEvent.defaultPrevented).toBe(false);
		expect(input.value).toBe("");
	});

	test("ignores non-printable keys", () => {
		const input = focusedInput(activate(""));

		const [, shiftEvent] = press(input, "'", "Shift", "A");

		expect(shiftEvent.defaultPrevented).toBe(false);
		expect(input.value).toBe("Ā");
	});

	test("passes through other keys", () => {
		const input = focusedInput(activate(""));

		const [event] = press(input, "a");

		expect(event.defaultPrevented).toBe(false);
	});

	test("uses insertText command for contenteditable elements", () => {
		const doc = activate("");
		const editable = focusedInput(doc, '<div contenteditable="true"></div>');
		doc.execCommand = jest.fn();

		press(editable, "'", "s");

		expect(doc.execCommand).toHaveBeenCalledWith("insertText", false, "š");
	});
});

describe("activation", () => {
	test("adds the indicator style once when activated twice", () => {
		const doc = activate("");

		dom.window.eval(SOURCE);

		expect(doc.head.querySelectorAll("style")).toHaveLength(1);
		expect(doc.documentElement.dataset.livonianKeyboard).toBe("active");
	});

	test("handles each key once when activated twice", () => {
		const doc = activate("");
		delete dom.window.livonianKeyboardActive;
		dom.window.eval(SOURCE);
		const input = focusedInput(doc);

		press(input, "'", "a");

		expect(input.value).toBe("ā");
	});
});

describe("iframes", () => {
	test("works in an iframe present at activation", () => {
		const doc = activate("<iframe></iframe>");
		const iframeDocument = doc.querySelector("iframe").contentDocument;
		const input = focusedInput(iframeDocument);

		press(input, "'", "z");

		expect(input.value).toBe("ž");
		expect(iframeDocument.head.querySelectorAll("style")).toHaveLength(1);
	});

	test("works in an iframe added after activation", async () => {
		const doc = activate("");
		const iframe = doc.createElement("iframe");
		doc.body.appendChild(iframe);

		await new Promise((resolve) => setTimeout(resolve, 600));
		const input = focusedInput(iframe.contentDocument);
		press(input, "`", "x");

		expect(input.value).toBe("ȫ");
	});

	test("uses insertText command of the iframe document", () => {
		const doc = activate("<iframe></iframe>");
		const iframeDocument = doc.querySelector("iframe").contentDocument;
		const editable = focusedInput(
			iframeDocument,
			'<div contenteditable="true"></div>',
		);
		doc.execCommand = jest.fn();
		iframeDocument.execCommand = jest.fn();

		press(editable, "'", "c");

		expect(iframeDocument.execCommand).toHaveBeenCalledWith(
			"insertText",
			false,
			"č",
		);
		expect(doc.execCommand).not.toHaveBeenCalled();
	});
});
