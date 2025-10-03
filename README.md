# iFlytek ISE Proxy (Python/Flask)

A minimal and secure HTTP proxy for **iFlytek Intelligent Speech Evaluation (ISE)**.
Your platform calls this proxy with simple JSON; the proxy computes iFlytek's
dynamic headers (`X-CurTime`, `X-Param`, `X-CheckSum`) and forwards the request
to iFlytek's HTTP ISE endpoint, returning the raw response.

> Why a proxy? Many no-code/low-code platforms can only set *static* headers.
> iFlytek needs a per-request signature, so we calculate it server-side here.

---

## Endpoints

- `POST /iflytek/ise`  
  Body (JSON):
  ```json
  {
    "audio": "<base64 audio>", 
    "text": "evaluation text",
    "language": "en_us",           // or "zh_cn"
    "category": "read_sentence"    // e.g., read_sentence, read_word, read_chapter...
  }
  ```
  Headers:
  - `X-Plugin-Key: <your internal token>` (server checks this)

- `GET /health` → health check

The proxy forwards to `https://api.xfyun.cn/v1/service/v2/ise`.

---

## Quick Start (local)

1. **Create .env**
   ```bash
   cp .env.example .env
   # Edit .env to fill:
   # IFLYTEK_APPID=
   # IFLYTEK_APIKEY=
   # PLUGIN_TOKEN=some-strong-secret
   ```

2. **Install deps & run**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   flask --app app.py run --port 8000
   ```

3. **Test**
   ```bash
   curl -X POST "http://127.0.0.1:8000/iflytek/ise" \
     -H "Content-Type: application/json" \
     -H "X-Plugin-Key: $(grep PLUGIN_TOKEN .env | cut -d= -f2)" \
     -d @tests/sample_request.json
   ```

> Tip: Use `scripts/encode_wav_to_base64.py` to generate base64 from a mono 16 kHz PCM WAV.

---

## Deploy

### Render.com / Railway.app / Fly.io (or any VM)

- Set env vars: `IFLYTEK_APPID`, `IFLYTEK_APIKEY`, `PLUGIN_TOKEN`
- Start command: `gunicorn -c gunicorn.conf.py app:app`

### Docker
```bash
docker build -t iflytek-ise-proxy .
docker run -p 8000:8000 \
  -e IFLYTEK_APPID=xxx -e IFLYTEK_APIKEY=yyy -e PLUGIN_TOKEN=zzz \
  iflytek-ise-proxy
```

You will get: `http://localhost:8000/iflytek/ise`

---

## Platform Form Fill (your no-code platform)

- **URL**: `https://<your-host>/iflytek/ise`
- **Headers**:
  - `Content-Type: application/json`
  - `X-Plugin-Key: <PLUGIN_TOKEN>`
- **Body (JSON)**: see request schema above.

> Do NOT put iFlytek's `AppID/APIKey` in the platform. Keep them only in this server.

---

## Security Notes

- The proxy checks `X-Plugin-Key`. Change it often and keep it secret.
- Optionally restrict by IP/CIDR or add simple rate limiting.
- Validate payload sizes; large audio can be rejected (see `MAX_AUDIO_BYTES`).

---

## Troubleshooting

- **401 Unauthorized**: missing or wrong `X-Plugin-Key`.
- **`invalid checksum` or `param error`**: verify timestamp/param computation;
  ensure `language/category` match your content; confirm audio base64 and format.
- **Timeout**: try with a very short audio first; increase upstream timeout if needed.

---

## License

MIT
