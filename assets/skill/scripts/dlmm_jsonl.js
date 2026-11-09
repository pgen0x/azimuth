"use strict";
// Bounded-memory JSONL readers for the executor's journals.
//
// readFileSync(file).split("\n").map(JSON.parse) holds the whole file as one
// string, then every line as a second copy, then every parsed row: three copies
// of a journal that only grows. These read fixed-size chunks and keep only the
// rows a caller asks for.
const fs = require("fs");

const CHUNK_BYTES = 1 << 20;

// Calls visit(row) for every non-empty line, in file order. A malformed line
// throws, exactly like the JSON.parse map it replaces. A missing file is empty.
function forEachRow(file, visit) {
  let fd;
  try { fd = fs.openSync(file, "r"); }
  catch (error) { if (error.code === "ENOENT") return; throw error; }
  try {
    const buffer = Buffer.allocUnsafe(CHUNK_BYTES);
    let carry = Buffer.alloc(0);
    for (;;) {
      const read = fs.readSync(fd, buffer, 0, CHUNK_BYTES, null);
      if (read === 0) break;
      // Split on the last newline byte: it is ASCII, so the bytes before it
      // are complete UTF-8 even when a character straddles two chunks.
      const chunk = Buffer.concat([carry, buffer.subarray(0, read)]);
      const end = chunk.lastIndexOf(10);
      if (end === -1) { carry = chunk; continue; }
      carry = Buffer.from(chunk.subarray(end + 1));
      for (const line of chunk.toString("utf8", 0, end).split("\n")) if (line) visit(JSON.parse(line));
    }
    if (carry.length) visit(JSON.parse(carry.toString("utf8")));
  } finally {
    fs.closeSync(fd);
  }
}

function readRows(file, keep = () => true) {
  const rows = [];
  forEachRow(file, row => { if (keep(row)) rows.push(row); });
  return rows;
}

// The first row only, without reading the rest of the file. null when empty.
function firstRow(file) {
  let fd;
  try { fd = fs.openSync(file, "r"); }
  catch (error) { if (error.code === "ENOENT") return null; throw error; }
  try {
    const buffer = Buffer.allocUnsafe(CHUNK_BYTES);
    const chunks = [];
    for (;;) {
      const read = fs.readSync(fd, buffer, 0, CHUNK_BYTES, null);
      if (read === 0) break;
      const newline = buffer.subarray(0, read).indexOf(10);
      chunks.push(Buffer.from(buffer.subarray(0, newline === -1 ? read : newline)));
      if (newline !== -1) break;
    }
    const line = Buffer.concat(chunks).toString("utf8");
    return line ? JSON.parse(line) : null;
  } finally {
    fs.closeSync(fd);
  }
}

module.exports = { forEachRow, readRows, firstRow, CHUNK_BYTES };
