"use strict";
// dlmm_jsonl: chunked readers must return exactly what readFileSync+split did.
const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { forEachRow, readRows, firstRow, CHUNK_BYTES } = require("./dlmm_jsonl.js");

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jsonl-"));
const file = path.join(dir, "rows.jsonl");
const reference = f => fs.readFileSync(f, "utf8").split("\n").filter(Boolean).map(JSON.parse);

// Rows straddle several chunk boundaries, and multi-byte text lands on them.
const rows = [];
let bytes = 0;
for (let i = 0; bytes < 3 * CHUNK_BYTES + 12345; i++) {
  const row = { i, text: (i % 7 ? "x" : "日本語€🚀").repeat(1 + (i % 900)) };
  rows.push(row);
  bytes += Buffer.byteLength(JSON.stringify(row)) + 1;
}
fs.writeFileSync(file, rows.map(r => JSON.stringify(r)).join("\n") + "\n\n");
assert.deepStrictEqual(readRows(file), reference(file));
assert.deepStrictEqual(readRows(file, r => r.i % 100 === 0), reference(file).filter(r => r.i % 100 === 0));
assert.deepStrictEqual(firstRow(file), rows[0]);
let seen = 0;
forEachRow(file, () => seen++);
assert.strictEqual(seen, rows.length);

// No trailing newline: the last row still counts. A torn line throws like JSON.parse.
fs.writeFileSync(file, '{"a":1}\n{"a":2}');
assert.deepStrictEqual(readRows(file), [{ a: 1 }, { a: 2 }]);
fs.writeFileSync(file, '{"a":1}\n{"a":');
assert.throws(() => readRows(file), SyntaxError);

// A first row longer than one chunk is read whole; the rest is never needed.
const long = { big: "y".repeat(CHUNK_BYTES + 10) };
fs.writeFileSync(file, JSON.stringify(long) + "\n" + "{broken");
assert.deepStrictEqual(firstRow(file), long);

// Missing and empty files are empty, never an error.
assert.deepStrictEqual(readRows(path.join(dir, "absent.jsonl")), []);
assert.strictEqual(firstRow(path.join(dir, "absent.jsonl")), null);
fs.writeFileSync(file, "");
assert.strictEqual(firstRow(file), null);
assert.deepStrictEqual(readRows(file), []);

fs.rmSync(dir, { recursive: true, force: true });
console.log("JSONL chunked reader parity checks passed");
