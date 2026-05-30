# Image Captioning

> AI-powered image captioning with BLIP Base, FastAPI, and a cinematic editorial UI.

---

## Architecture

```
Browser
  │
  │  multipart/form-data (image + style)
  ▼
FastAPI (backend/main.py)
  │
  ├── routes/caption.py        ← validates request, orchestrates pipeline
  │         │
  │         ├── core/preprocessing.py
  │         │     • decode bytes → PIL Image
  │         │     • EXIF normalise, RGB convert
  │         │     • resize to ≤ 960px (aspect-safe)
  │         │     • reject corrupt / unsupported formats
  │         │
  │         └── core/inference.py
  │               • conditional prompt from style key
  │               • BLIP Base forward pass (3-beam, max 100 tokens)
  │               • post-process + style suffix
  │
  ├── db/crud.py               ← persist caption to SQLite
  │
  └── JSON response → Browser
        { id, caption, style, filename, device, created_at }

Browser
  └── app.js
        • staggered caption fade-in
        • history sidebar refresh
        • copy / download / retry
```

**Technology choices:**

| Concern | Choice | Why |
|---|---|---|
| Model | BLIP Base | Faster CPU inference, lower VRAM, stable deployment. Large adds marginal quality at significant latency cost. |
| Beam search | 3 beams | Empirically better than greedy, meaningfully faster than 5-beam on CPU. |
| Database | SQLite | Zero setup, file-based, sufficient for single-instance deployment. |
| Frontend | Vanilla JS + CSS | No build step, no framework overhead, easy to read and modify. |

---

## Features

| Feature | Detail |
|---|---|
| Caption generation | BLIP Base (`Salesforce/blip-image-captioning-base`) |
| Caption styles | Descriptive · Cinematic · Poetic · Social · Documentary |
| GPU / CPU | Auto-detected at startup, transparent fallback |
| History | SQLite — persists across restarts |
| Download | Per-caption `.txt` export |
| Dark / Light mode | Saved in `localStorage` |
| Responsive | 3-column desktop → stacked mobile |

---

## Project Structure

```
image-captioning/
├── backend/
│   ├── main.py                 # FastAPI app, lifespan, CORS, static serving
│   ├── core/
│   │   ├── config.py           # All tuneable values in one place
│   │   ├── inference.py        # BLIP loading and generation
│   │   └── preprocessing.py   # Image decode, validation, normalisation
│   ├── db/
│   │   ├── database.py         # SQLite init (WAL mode)
│   │   └── crud.py             # Save / fetch / delete captions
│   ├── routes/
│   │   ├── caption.py          # POST /api/caption
│   │   └── history.py          # GET/DELETE /api/history + download
│   └── utils/
│       ├── logger.py           # Structured logging, inference timer decorator
│       └── helpers.py          # Formatting utilities
├── frontend/
│   ├── templates/index.html    # 3-panel editorial layout
│   ├── static/css/style.css    # Design system (CSS custom properties)
│   └── static/js/app.js       # Upload, API calls, UI state, animations
├── run.py                      # Local dev launcher
├── app.py                      # Hugging Face Spaces entry point
├── Dockerfile
└── requirements.txt
```

---

## API Reference

### `POST /api/caption`

Upload an image and receive an AI-generated caption.

**Request** — `multipart/form-data`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `file` | binary | ✓ | — | ≤ 10 MB; JPEG, PNG, WebP, BMP, GIF, TIFF |
| `style` | string | — | `descriptive` | See style options below |

**Style options:** `descriptive` · `cinematic` · `poetic` · `social` · `documentary`

**Response — 200 OK**

```json
{
  "id": 42,
  "caption": "A lone lighthouse stands on a rocky cliff at dusk — shot on 35mm film.",
  "style": "cinematic",
  "filename": "coast.jpg",
  "device": "cpu",
  "created_at": "2024-06-01 14:22:33"
}
```

**Error responses**

| Code | Meaning |
|---|---|
| `400` | Empty file |
| `413` | File exceeds 10 MB |
| `422` | Invalid style or corrupt/unsupported image |
| `503` | Model not yet loaded (retry after startup) |
| `500` | Inference pipeline failure |

---

### `GET /api/history`

Returns recent captions, newest first.

**Query params:** `limit` (1–200, default 50) · `offset` (default 0)

---

### `GET /api/history/{id}/download`

Returns the caption as a `.txt` file attachment.

---

### `DELETE /api/history/{id}`

Deletes a caption record. Returns `{ "deleted": true, "id": 42 }`.

---

### `GET /health`

Liveness check. Returns `{ "status": "ok" }`.

---

## Local Development

```bash
git clone https://github.com/yourname/image-captioning.git
cd image-captioning

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python run.py
# → http://localhost:8000
```

BLIP Base (~450 MB) downloads automatically on first start.

**Environment variables**

| Variable | Default | Purpose |
|---|---|---|
| `DB_PATH` | `image-captioning.db` | SQLite file location |

---

## Deployment

### Render (recommended for CPU)

1. Create a **Web Service** pointing to this repo.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Instance size: **Standard** (≥ 2 GB RAM).
5. Add env var `DB_PATH=/data/image-captioning.db` and attach a **Disk** at `/data`.

### Hugging Face Spaces (CPU or GPU)

1. Create a new Space → **SDK: Docker**.
2. Push this repo — `app.py` at root is the entry point.
3. The included `Dockerfile` handles the rest.
4. For GPU: select a Space with T4 or better; BLIP will auto-use CUDA.

---

## Limitations

These are known constraints, not bugs — documenting them is part of mature engineering.

- **CPU inference latency.** Generation takes 8–20 seconds on a standard 2-core CPU. This is a model constraint. GPU deployment drops this to under 2 seconds.
- **Caption creativity varies by image.** BLIP Base works well on clear, well-lit subjects. Abstract, dark, or complex scenes produce shorter or less specific results.
- **Style conditioning is lightweight.** Styles shape captions via prompt prefixes — the model is not fine-tuned per style. Results are nudged, not guaranteed.
- **English only.** BLIP outputs English. Multilingual captions would require a downstream translation step.
- **Single-instance SQLite.** Suitable for one server. Horizontal scaling would require migrating to Postgres.
- **No authentication.** This is a demo application. Production use would need rate limiting and auth middleware.

---

## Design Notes

Image Captioning is intentionally **restrained**. The design borrows from editorial photography sites and Arc Browser — DM Serif Display, warm amber accent, near-black base. Both dark and light modes are first-class.

The frontend is zero-framework: plain HTML, CSS custom properties, vanilla JS. No build step, no bundler.

---

## Licence

MIT
