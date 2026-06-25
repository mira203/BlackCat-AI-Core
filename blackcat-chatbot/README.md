---
title: CyberFixBot API
emoji: 🛡️
colorFrom: red
colorTo: gray
sdk: docker
pinned: false
---

# CyberFixBot — Cybersecurity RAG API

A RAG-powered FastAPI chatbot that answers questions about vulnerability fixes.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Status check |
| GET | `/health` | Health check |
| POST | `/ask` | Ask a vulnerability question |

## Example Request

```bash
curl -X POST https://YOUR-SPACE-URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How to fix SQL Injection?"}'
```

## Environment Variables

Set `GROQ_API_KEY` as a **secret** in your Space settings.
