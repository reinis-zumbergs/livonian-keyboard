// This code should be loaded via a bookmarklet.
// It will activate the Livonian keyboard on the current page.
(function () {
	// Check if the event handler is already added
	if (window.livonianKeyboardActive) {
		console.info("Livonian keyboard is already active");
		return;
	}

	const deadKeyMap = {
		"'": {
			q: "ä",
			w: "ü",
			e: "ē",
			r: "ŗ",
			t: "ţ",
			y: "ȳ",
			u: "ū",
			i: "ī",
			o: "ō",
			p: "ǫ",
			a: "ā",
			s: "š",
			d: "ḑ",
			g: "ģ",
			j: "ȯ",
			k: "ķ",
			l: "ļ",
			z: "ž",
			x: "ö",
			c: "č",
			n: "ņ",
			m: "õ",
			Q: "Ä",
			W: "Ü",
			E: "Ē",
			R: "Ŗ",
			T: "Ţ",
			Y: "Ȳ",
			U: "Ū",
			I: "Ī",
			O: "Ō",
			P: "Ǫ",
			A: "Ā",
			S: "Š",
			D: "Ḑ",
			G: "Ģ",
			J: "Ȯ",
			K: "Ķ",
			L: "Ļ",
			Z: "Ž",
			X: "Ö",
			C: "Č",
			N: "Ņ",
			M: "Õ",
		},
		"`": {
			q: "ǟ",
			w: "ǖ",
			j: "ȱ",
			x: "ȫ",
			m: "ȭ",
			p: "ǭ",
			Q: "Ǟ",
			W: "Ǖ",
			J: "Ȱ",
			X: "Ȫ",
			M: "Ȭ",
			P: "Ǭ",
		},
	};

	let activeDeadKey = null;

	document.addEventListener("keydown", function (event) {
		// console.log('pressing', event.key);
		// Ignore keydown events that are not printable characters
		if (event.key.length !== 1) {
			// console.log('Ignore non-printable key', event.key);
			return;
		}

		if (activeDeadKey) {
			// console.log('Active dead key', activeDeadKey);
			if (deadKeyMap[activeDeadKey][event.key] !== undefined) {
				const modifiedChar = deadKeyMap[activeDeadKey][event.key];
				// console.log('Output mapped character', modifiedChar)
				insertCharacter(modifiedChar);
				// console.log('Prevent default', event.key);
				event.preventDefault();
			} else {
				// console.log('No mapping. Passing through', event.key);
			}

			// console.log('Clear active dead key');
			activeDeadKey = null;

			return;
		}

		if (deadKeyMap[event.key] !== undefined) {
			// console.log('Set active dead key', event.key);
			activeDeadKey = event.key;
			event.preventDefault();
		} else {
			// console.log('Not a dead key. Passing through', event.key);
		}
	});

	function insertCharacter(char) {
		const activeElement = document.activeElement;
		if (activeElement && activeElement.value !== undefined) {
			const start = activeElement.selectionStart;
			const end = activeElement.selectionEnd;
			activeElement.value =
				activeElement.value.substring(0, start) +
				char +
				activeElement.value.substring(end);
			activeElement.setSelectionRange(start + 1, start + 1);
		} else {
			document.execCommand("insertText", false, char);
		}
	}

	// Add Sierra Leone flag emoji to various input element backgrounds
	const CSS = `
		input[type="text"], input:not([type]),
		input[type="search"], input[type="url"],
		textarea, [contenteditable="true"] {
			background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="30" height="20"><text x="0" y="16">🇸🇱</text></svg>');
			background-repeat: no-repeat;
			background-position: right top;
		}
	`;
	const style = document.createElement("style");
	style.appendChild(document.createTextNode(CSS));
	document.head.appendChild(style);

	window.livonianKeyboardActive = true;

	console.info("Livonian keyboard activated");
})();
