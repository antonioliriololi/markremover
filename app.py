import io
import uuid

from flask import Flask, abort, jsonify, render_template, request, send_file

from cleaner import clean_pdf

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
RESULTS = {}  # id -> bytes (in-memory)
MAX_RESULTS = 20


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/process")
def process():
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".pdf"):
        return jsonify(error="Sube un archivo PDF."), 400
    data = f.read()
    if not data.startswith(b"%PDF"):
        return jsonify(error="El archivo no es un PDF válido."), 400
    try:
        out = clean_pdf(data)
    except Exception:
        return jsonify(error="No se pudo procesar el PDF."), 422
    rid = uuid.uuid4().hex
    RESULTS[rid] = out
    while len(RESULTS) > MAX_RESULTS:
        RESULTS.pop(next(iter(RESULTS)))
    return jsonify(id=rid)


@app.get("/download/<rid>")
def download(rid):
    data = RESULTS.get(rid)
    if data is None:
        abort(404)
    return send_file(io.BytesIO(data), mimetype="application/pdf",
                     as_attachment=True, download_name="limpio.pdf")


if __name__ == "__main__":
    app.run(debug=False)
