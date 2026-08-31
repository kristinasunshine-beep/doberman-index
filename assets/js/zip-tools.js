(function (global) {
  "use strict";

  const encoder = new TextEncoder();
  const decoder = new TextDecoder("utf-8");
  const crcTable = new Uint32Array(256);

  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    crcTable[n] = c >>> 0;
  }

  function crc32(bytes) {
    let crc = 0xffffffff;
    for (let i = 0; i < bytes.length; i += 1) crc = crcTable[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
    return (crc ^ 0xffffffff) >>> 0;
  }

  function u16(value) {
    return new Uint8Array([value & 0xff, (value >>> 8) & 0xff]);
  }

  function u32(value) {
    return new Uint8Array([
      value & 0xff,
      (value >>> 8) & 0xff,
      (value >>> 16) & 0xff,
      (value >>> 24) & 0xff,
    ]);
  }

  function concat(parts) {
    const size = parts.reduce((sum, part) => sum + part.length, 0);
    const result = new Uint8Array(size);
    let offset = 0;
    parts.forEach((part) => {
      result.set(part, offset);
      offset += part.length;
    });
    return result;
  }

  function dosDateTime(dateValue) {
    const date = dateValue instanceof Date ? dateValue : new Date();
    const year = Math.max(1980, date.getFullYear());
    return {
      time: (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2),
      date: ((year - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate(),
    };
  }

  async function toBytes(value) {
    if (value instanceof Uint8Array) return value;
    if (value instanceof ArrayBuffer) return new Uint8Array(value);
    if (value instanceof Blob) return new Uint8Array(await value.arrayBuffer());
    return encoder.encode(String(value));
  }

  function safeName(name) {
    const normalized = String(name).replace(/\\/g, "/").replace(/^\/+/, "");
    if (!normalized || normalized.split("/").some((part) => part === "..")) {
      throw new Error("Unsafe file name in package.");
    }
    return normalized;
  }

  async function create(entries) {
    if (!Array.isArray(entries) || entries.length === 0) throw new Error("The package has no files.");
    if (entries.length > 65535) throw new Error("The package contains too many files.");

    const localParts = [];
    const centralParts = [];
    let offset = 0;

    for (const entry of entries) {
      const nameBytes = encoder.encode(safeName(entry.name));
      const data = await toBytes(entry.data);
      const crc = crc32(data);
      const stamp = dosDateTime(entry.lastModified ? new Date(entry.lastModified) : new Date());
      const localHeader = concat([
        u32(0x04034b50), u16(20), u16(0x0800), u16(0), u16(stamp.time), u16(stamp.date),
        u32(crc), u32(data.length), u32(data.length), u16(nameBytes.length), u16(0), nameBytes,
      ]);
      localParts.push(localHeader, data);

      centralParts.push(concat([
        u32(0x02014b50), u16(20), u16(20), u16(0x0800), u16(0), u16(stamp.time), u16(stamp.date),
        u32(crc), u32(data.length), u32(data.length), u16(nameBytes.length), u16(0), u16(0), u16(0),
        u16(0), u32(0), u32(offset), nameBytes,
      ]));
      offset += localHeader.length + data.length;
    }

    const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);
    const end = concat([
      u32(0x06054b50), u16(0), u16(0), u16(entries.length), u16(entries.length),
      u32(centralSize), u32(offset), u16(0),
    ]);
    return new Blob([...localParts, ...centralParts, end], { type: "application/zip" });
  }

  function findEnd(bytes) {
    const minimum = Math.max(0, bytes.length - 65557);
    for (let i = bytes.length - 22; i >= minimum; i -= 1) {
      if (bytes[i] === 0x50 && bytes[i + 1] === 0x4b && bytes[i + 2] === 0x05 && bytes[i + 3] === 0x06) return i;
    }
    return -1;
  }

  async function inflateRaw(bytes) {
    if (typeof DecompressionStream === "undefined") {
      throw new Error("This compressed package needs a newer version of Chrome or Edge.");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  async function read(source) {
    const bytes = await toBytes(source);
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const endOffset = findEnd(bytes);
    if (endOffset < 0) throw new Error("This is not a readable ZIP package.");
    const count = view.getUint16(endOffset + 10, true);
    let cursor = view.getUint32(endOffset + 16, true);
    const result = new Map();

    for (let index = 0; index < count; index += 1) {
      if (view.getUint32(cursor, true) !== 0x02014b50) throw new Error("The ZIP directory is damaged.");
      const method = view.getUint16(cursor + 10, true);
      const compressedSize = view.getUint32(cursor + 20, true);
      const uncompressedSize = view.getUint32(cursor + 24, true);
      const nameLength = view.getUint16(cursor + 28, true);
      const extraLength = view.getUint16(cursor + 30, true);
      const commentLength = view.getUint16(cursor + 32, true);
      const localOffset = view.getUint32(cursor + 42, true);
      const name = safeName(decoder.decode(bytes.slice(cursor + 46, cursor + 46 + nameLength)));
      if (view.getUint32(localOffset, true) !== 0x04034b50) throw new Error("A ZIP file entry is damaged.");
      const localNameLength = view.getUint16(localOffset + 26, true);
      const localExtraLength = view.getUint16(localOffset + 28, true);
      const dataStart = localOffset + 30 + localNameLength + localExtraLength;
      const compressed = bytes.slice(dataStart, dataStart + compressedSize);
      let data;
      if (method === 0) data = compressed;
      else if (method === 8) data = await inflateRaw(compressed);
      else throw new Error(`Unsupported ZIP compression method (${method}).`);
      if (data.length !== uncompressedSize) throw new Error(`File size check failed for ${name}.`);
      result.set(name, { name, data, size: data.length });
      cursor += 46 + nameLength + extraLength + commentLength;
    }
    return result;
  }

  global.DIZip = { create, read };
})(window);
