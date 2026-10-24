import struct

VERSION = 1
HEADER = struct.Struct(">BBI")  # version, opcode, payload length

OP_FETCH_NEWS = 0x01
OP_ASK_MODEL = 0x02
OP_PREDICT = 0x03
OP_OK = 0x80
OP_ERROR = 0x81

def pack_str(s: str) -> bytes:
    data = s.encode("utf-8")
    return struct.pack(">H", len(data)) + data

def unpack_str(buf: bytes, offset: int = 0):
    (n,) = struct.unpack_from(">H", buf, offset)
    start = offset + 2
    return buf[start:start + n].decode("utf-8"), start + n

def encode_frame(opcode: int, payload: bytes = b"") -> bytes:
    return HEADER.pack(VERSION, opcode, len(payload)) + payload

def decode_frame(data: bytes):
    version, opcode, length = HEADER.unpack_from(data, 0)
    if version != VERSION:
        raise ValueError(f"unsupported version {version}")
    payload = data[HEADER.size:HEADER.size + length]
    if len(payload) != length:
        raise ValueError("truncated frame")
    return opcode, payload
OP_HISTORY = 0x04
OP_PREDICTIONS = 0x05
