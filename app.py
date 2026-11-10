from pathlib import Path
from flask import send_from_directory
from api.index import app

PUBLIC = Path(__file__).parent / "public"

@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")

@app.get("/predictions.html")
def predictions():
    return send_from_directory(PUBLIC, "predictions.html")

@app.get("/due.html")
def due():
    return send_from_directory(PUBLIC, "due.html")

@app.get("/compare.html")
def compare():
    return send_from_directory(PUBLIC, "compare.html")

@app.get("/render.js")
def render_js():
    return send_from_directory(PUBLIC, "render.js")
