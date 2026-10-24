import os
import struct
import sys
from pathlib import Path

from flask import Flask, request, Response, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from codec import *
from news import fetch_headlines
from db import init_schema, record_headlines, list_analyses, list_predictions
from pipeline import run_analysis
from cycle import daily_cycle

app = Flask(__name__)
_schema_ready = False

@app.before_request
def ensure_schema():
    global _schema_ready
    if not _schema_ready:
        init_schema()
        _schema_ready = True

def reply(opcode, payload=b"", status=200):
    return Response(encode_frame(opcode, payload),
                    mimetype="application/octet-stream", status=status)

@app.post("/bin")
def bin_endpoint():
    opcode, payload = decode_frame(request.get_data())

    if opcode == OP_FETCH_NEWS:
        items = fetch_headlines()
        record_headlines(items)
        body = struct.pack(">H", len(items))
        for title, link in items:
            body += pack_str(title) + pack_str(link)
        return reply(OP_OK, body)

    if opcode == OP_ASK_MODEL:
        (count,) = struct.unpack_from(">H", payload, 0)
        offset = 2
        headlines = []
        for _ in range(count):
            title, offset = unpack_str(payload, offset)
            headlines.append(title)
        try:
            _, text = run_analysis(headlines)
        except Exception as e:
            return reply(OP_ERROR, pack_str(str(e))[:65535], status=502)
        return reply(OP_OK, pack_str(text))

    if opcode == OP_HISTORY:
        limit = struct.unpack_from(">H", payload, 0)[0] if payload else 10
        rows = list_analyses(limit)
        body = struct.pack(">H", len(rows))
        for row_id, created_at, analysis in rows:
            body += struct.pack(">I", row_id) + pack_str(created_at) + pack_str(analysis[:4000])
        return reply(OP_OK, body)

    if opcode == OP_PREDICTIONS:
        limit = struct.unpack_from(">H", payload, 0)[0] if payload else 30
        rows = list_predictions(limit)
        body = struct.pack(">H", len(rows))
        for pid, aid, trend, forecast, conf, days, status, evidence in rows:
            body += (struct.pack(">II", pid, aid or 0)
                     + pack_str(trend or "") + pack_str(forecast or "")
                     + pack_str(conf or "") + struct.pack(">H", days or 0)
                     + pack_str(status) + pack_str(evidence[:1000]))
        return reply(OP_OK, body)

    return reply(OP_ERROR, pack_str("unknown opcode"), status=400)

@app.get("/api/cron")
def cron():
    secret = os.environ.get("CRON_SECRET", "")
    if not secret or request.headers.get("Authorization") != f"Bearer {secret}":
        return jsonify(error="unauthorized"), 401
    try:
        return jsonify(daily_cycle())
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(port=5000)
