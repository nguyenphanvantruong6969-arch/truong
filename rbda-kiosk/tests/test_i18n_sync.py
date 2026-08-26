import json
import os
import shutil
import subprocess

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_EXTRACT_SCRIPT = """
const fs = require("fs");
const src = fs.readFileSync(process.argv[1], "utf8");
const start = src.indexOf("const ERROR_MESSAGES = {");
if (start === -1) { console.error("ERROR_MESSAGES not found"); process.exit(1); }
const braceStart = src.indexOf("{", start);
let depth = 0, i = braceStart;
for (; i < src.length; i++) {
  if (src[i] === "{") depth++;
  else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
}
const obj = eval("(" + src.slice(braceStart, i) + ")");
process.stdout.write(JSON.stringify(obj));
"""


def _extract_js_error_messages():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available in this environment")
    result = subprocess.run(
        [node, "-e", _EXTRACT_SCRIPT, "--", os.path.join(BASE_DIR, "i18n.js")],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


_EXTRACT_UI_STRINGS_SCRIPT = """
const fs = require("fs");
const src = fs.readFileSync(process.argv[1], "utf8");
const start = src.indexOf("const UI_STRINGS = {");
if (start === -1) { console.error("UI_STRINGS not found"); process.exit(1); }
const braceStart = src.indexOf("{", start);
let depth = 0, i = braceStart;
for (; i < src.length; i++) {
  if (src[i] === "{") depth++;
  else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
}
const obj = eval("(" + src.slice(braceStart, i) + ")");
process.stdout.write(JSON.stringify({ vi: Object.keys(obj.vi), en: Object.keys(obj.en) }));
"""


def test_ui_strings_vi_and_en_have_identical_keys():
    """UI_STRINGS.vi and UI_STRINGS.en in i18n.js must cover exactly the
    same set of keys — otherwise switching language would silently fall
    back to Vietnamese (or the raw key) for anything missing on one side."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available in this environment")
    result = subprocess.run(
        [node, "-e", _EXTRACT_UI_STRINGS_SCRIPT, "--", os.path.join(BASE_DIR, "i18n.js")],
        capture_output=True, text=True, check=True,
    )
    keys = json.loads(result.stdout)
    vi_keys, en_keys = set(keys["vi"]), set(keys["en"])
    assert vi_keys == en_keys, (
        f"vi-only keys: {vi_keys - en_keys}; en-only keys: {en_keys - vi_keys}"
    )


def test_every_data_i18n_attribute_in_html_has_a_ui_strings_entry():
    """Every data-i18n / data-i18n-html / data-i18n-placeholder key
    referenced in index.html must exist in UI_STRINGS — otherwise that
    element would silently render the raw key string instead of text."""
    import re

    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available in this environment")

    html = open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8").read()
    keys_used = set(re.findall(r'data-i18n(?:-html|-placeholder)?="([a-zA-Z0-9_]+)"', html))
    assert keys_used, "sanity check: should have found data-i18n attributes in index.html"

    result = subprocess.run(
        [node, "-e", _EXTRACT_UI_STRINGS_SCRIPT, "--", os.path.join(BASE_DIR, "i18n.js")],
        capture_output=True, text=True, check=True,
    )
    keys = json.loads(result.stdout)
    vi_keys = set(keys["vi"])

    missing = keys_used - vi_keys
    assert not missing, f"index.html uses i18n keys missing from UI_STRINGS: {missing}"


def test_js_error_catalog_matches_python_error_catalog():
    """i18n.js's ERROR_MESSAGES must be a byte-for-byte mirror of
    i18n_errors.py's MESSAGES — api.py only emits codes, so if the two
    catalogs drift, the UI silently falls back to showing a raw code
    instead of translated text."""
    from i18n_errors import MESSAGES as py_messages

    js_messages = _extract_js_error_messages()

    py_keys = set(py_messages.keys())
    js_keys = set(js_messages.keys())
    assert py_keys == js_keys, (
        f"Python-only codes: {py_keys - js_keys}; JS-only codes: {js_keys - py_keys}"
    )

    mismatches = []
    for code in py_keys:
        for lang in ("vi", "en"):
            if py_messages[code].get(lang) != js_messages[code].get(lang):
                mismatches.append((code, lang))
    assert not mismatches, f"text differs between i18n_errors.py and i18n.js: {mismatches}"
