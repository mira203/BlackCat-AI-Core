---
title: BlackCat Report Engine
emoji: 🐱
colorFrom: gray
colorTo: indigo
sdk: docker
pinned: false
---

# BlackCat Report Engine

AI-powered cybersecurity vulnerability report generator.

## Setup

1. Add your `GROQ_API_KEY` in Space Settings → Repository secrets
2. Upload `vuln_fixes_expanded.csv` to the root of the repo

## API Endpoint

**POST** `/generate-report/`

```json
{
  "vulnerabilityToAI": [
    {
      "url": "http://example.com/page",
      "alert": "SQL Injection",
      "param": "id",
      "attack": "1' OR '1'='1",
      "risk": "High"
    }
  ]
}
```

Swagger UI available at: `https://<your-space-url>/docs`
