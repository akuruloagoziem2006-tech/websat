const VERSION = 1;
const OP_OK = 0x80;
const OP = { HISTORY: 0x04, PREDICTIONS: 0x05, DUE_SOON: 0x06, COMPARE: 0x07 };
const WINDOW_SCALE_DAYS = 90;
const STATUS_COLOR = {
  open: "var(--open)",
  confirmed: "var(--confirmed)",
  contradicted: "var(--contradicted)",
  inconclusive: "var(--inconclusive)",
};
const dec = new TextDecoder();

function encodeFrame(opcode, payload = new Uint8Array(0)) {
  const buf = new Uint8Array(6 + payload.length);
  const view = new DataView(buf.buffer);
  view.setUint8(0, VERSION);
  view.setUint8(1, opcode);
  view.setUint32(2, payload.length);
  buf.set(payload, 6);
  return buf;
}

function decodeFrame(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (view.getUint8(0) !== VERSION) throw new Error("unsupported protocol version");
  return { opcode: view.getUint8(1), payload: bytes.subarray(6, 6 + view.getUint32(2)) };
}

class Reader {
  constructor(bytes) {
    this.bytes = bytes;
    this.view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    this.pos = 0;
  }
  u16() { const v = this.view.getUint16(this.pos); this.pos += 2; return v; }
  u32() { const v = this.view.getUint32(this.pos); this.pos += 4; return v; }
  str() {
    const n = this.u16();
    const s = dec.decode(this.bytes.subarray(this.pos, this.pos + n));
    this.pos += n;
    return s;
  }
}

async function call(opcode, limit) {
  const res = await fetch("/bin", {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream" },
    body: encodeFrame(opcode, new Uint8Array([0, limit])),
  });
  const { opcode: op, payload } = decodeFrame(new Uint8Array(await res.arrayBuffer()));
  const reader = new Reader(payload);
  if (op !== OP_OK) throw new Error(reader.str());
  return reader;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function showError(container, err) {
  container.className = "error";
  container.textContent = `Could not load this page: ${err.message}. Refresh to try again.`;
}
