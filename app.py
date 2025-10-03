from flask import Flask, request, jsonify, Response
import os, time, base64, hashlib, requests, json
from dotenv import load_dotenv

load_dotenv()

APPID  = os.getenv("IFLYTEK_APPID")
APIKEY = os.getenv("IFLYTEK_APIKEY")
TOKEN  = os.getenv("PLUGIN_TOKEN")
HOST   = os.getenv("HOST", "0.0.0.0")
PORT   = int(os.getenv("PORT", "8000"))
MAX_AUDIO_BYTES = int(os.getenv("MAX_AUDIO_BYTES", "0"))  # 0 = unlimited

if not APPID or not APIKEY:
    print("[WARN] IFLYTEK_APPID or IFLYTEK_APIKEY not set. Remember to configure .env")

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

def unauthorized():
    return jsonify({"error": "Unauthorized"}), 401

@app.post("/iflytek/ise")
def ise_proxy():
    # Simple token check
    incoming = request.headers.get("X-Plugin-Key") or request.headers.get("X-Token")
    if not TOKEN or incoming != TOKEN:
        return unauthorized()

    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    audio = data.get("audio")
    text  = data.get("text")
    language = data.get("language", "en_us")
    category = data.get("category", "read_sentence")

    if not audio or not text:
        return jsonify({"error": "Missing 'audio' (base64) or 'text'"}), 400

    if MAX_AUDIO_BYTES and len(audio.encode()) > MAX_AUDIO_BYTES:
        return jsonify({"error": "audio too large"}), 413

    # Build iFlytek headers
    param = {
        "aue": "raw",
        "language": language,
        "category": category,
        "result_level": "complete"
    }
    x_param = base64.b64encode(json.dumps(param).encode()).decode()
    x_cur_time = str(int(time.time()))
    x_checksum = hashlib.md5((APIKEY + x_cur_time + x_param).encode()).hexdigest()

    headers = {
        "X-Appid": APPID,
        "X-CurTime": x_cur_time,
        "X-Param": x_param,
        "X-CheckSum": x_checksum,
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
    }

    # Form-encoded body for iFlytek
    payload = {
        "audio": audio,
        "text": text
    }

    try:
        r = requests.post(
            "https://api.xfyun.cn/v1/service/v2/ise",
            headers=headers,
            data=payload,
            timeout=60
        )
    except requests.RequestException as e:
        return jsonify({"error": "Upstream request failed", "detail": str(e)}), 502

    # Transparently pass through text/JSON/XML
    content_type = r.headers.get("Content-Type", "text/plain")
    return Response(r.content, status=r.status_code, content_type=content_type)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
