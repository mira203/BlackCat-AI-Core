# BlackCat-AI-Core

> The AI backbone of **BlackCat** — an AI-powered cybersecurity platform built as a graduation project.  
> This repository contains the three deployed AI modules that power the platform.

---

## Project Overview

**BlackCat** is an end-to-end cybersecurity platform that combines machine learning, RAG (Retrieval-Augmented Generation), and static APK analysis to help security teams detect threats and generate professional vulnerability reports.

This repo (`BlackCat-AI-Core`) holds all three AI services, each deployed independently on **Hugging Face Spaces** via Docker.

---

## Modules:

### 1. CyberFixBot — RAG Vulnerability Chatbot (`app.py`)

A conversational RAG-powered chatbot that answers questions about vulnerability remediation using a curated cybersecurity knowledge base.

**What it does:**
- Accepts a natural language question about a vulnerability (e.g. *"How to fix SQL Injection?"*)
- Retrieves the most relevant fix documentation from a vectorstore
- Returns a structured 5-step remediation guide: Summary → Root Cause → Fix Steps → Code Example → Prevention Tips
- Maintains conversation history across turns (sliding window of 10 messages)

**Tech Stack:**

| Component | Tool |
|---|---|
| API Framework | FastAPI |
| LLM | LLaMA 3.1 8B (via Groq API) |
| Embeddings | FastEmbed |
| Vector Store | ChromaDB (MMR retrieval) |
| RAG Chain | LangChain `ConversationalRetrievalChain` |
| Memory | `ConversationBufferWindowMemory` (k=10) |
| Deployment | Hugging Face Spaces (Docker) |

**API Endpoints:**

```
GET  /         → Status check
GET  /health   → Health check
POST /ask      → Ask a vulnerability question
```

**Example Request:**
```bash
curl -X POST https://YOUR-SPACE-URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How to fix XSS vulnerability?"}'
```

**Example Response:**
```json
{
  "answer": "## Step 1: Vulnerability Summary\n...",
  "sources_count": 5,
  "question": "How to fix XSS vulnerability?"
}
```

---

### 2. BlackCat Report Generator — AI Report Engine (`BlackCat_Report_Generator.py`)

Automatically generates professional penetration testing reports from raw vulnerability scan data (e.g. output from OWASP ZAP).

**What it does:**
- Accepts a list of vulnerabilities (URL, alert type, parameter, attack payload, risk level)
- Retrieves similar known vulnerabilities from the knowledge base for context
- Generates a structured professional report per vulnerability using a strict prompt template
- Returns all reports as a single JSON response

**Tech Stack:**

| Component | Tool |
|---|---|
| API Framework | FastAPI |
| LLM | LLaMA 3.1 8B (via Groq API) |
| Embeddings | FastEmbed |
| Vector Store | ChromaDB |
| RAG Chain | LangChain LCEL (`RunnablePassthrough`) |
| Deployment | Hugging Face Spaces (Docker) |

**API Endpoint:**

```
POST /generate-report/
```

**Example Request:**
```json
{
  "vulnerabilityToAI": [
    {
      "url": "http://example.com/login",
      "alert": "SQL Injection",
      "param": "id",
      "attack": "1' OR '1'='1",
      "risk": "High"
    }
  ]
}
```

**Example Response:**
```json
{
  "status": "success",
  "total_reports": 1,
  "data": [
    {
      "alert": "SQL Injection",
      "url": "http://example.com/login",
      "ai_report": "**Title:** SQL Injection in `id`\n\n**Summary:** ..."
    }
  ]
}
```

---

### 3. Malware Detection API — Android APK Analyzer (`app.py` / Malware module)

A hybrid static analysis engine that classifies Android APK files as **Clean** or **Infected**, identifies the specific malware family, and assigns a risk level.

**What it does:**
- Accepts an APK file upload
- Extracts static features from the manifest and DEX bytecode using **Androguard**
- Runs the features through a trained **Random Forest** classifier (Drebin-215 feature set, ~96% accuracy, F1 = 0.96)
- Applies a modern heuristic rule layer on top of ML to catch threats that post-date the training data (e.g. droppers using `REQUEST_INSTALL_PACKAGES`)
- Returns verdict, threat type, risk level, and detected indicators

**Hybrid Detection Logic:**
```
Infected = ML model flags it  OR  Heuristic layer flags it
Clean    = Both layers agree it is benign
```

**Threat Categories Detected:**
`Spyware` · `Trojan-SMS` · `Ransomware` · `Rootkit` · `Adware` · `Trojan-Dropper` · `Banking Trojan`

**Tech Stack:**

| Component | Tool |
|---|---|
| API Framework | FastAPI |
| APK Parsing | Androguard 4.x |
| ML Model | Random Forest (scikit-learn 1.6.1) |
| Feature Engineering | Drebin-215 static feature set |
| Model Improvements | SMOTE · GridSearchCV · CalibratedClassifierCV |
| Deployment | Hugging Face Spaces (Docker) |

**API Endpoint:**

```
POST /predict   → Upload APK file (multipart/form-data, field: apk_file)
```

**Example (curl):**
```bash
curl -X POST "https://mirao-malware-detection.hf.space/predict" \
     -F "apk_file=@YourApp.apk"
```

**Example Response — Infected:**
```json
{
  "status": "Infected",
  "filename": "YourApp.apk",
  "threat_type": "Trojan-Dropper",
  "risk_level": "Critical",
  "detection_source": "Heuristic (modern manifest analysis)",
  "analysis": {
    "summary": "APK requests permissions associated with silent app installation and boot persistence.",
    "detected_indicators": ["REQUEST_INSTALL_PACKAGES", "RECEIVE_BOOT_COMPLETED", "QUERY_ALL_PACKAGES"],
    "recommendation": "CRITICAL: Do NOT install."
  }
}
```

**Self-test:**
```bash
python selftest.py path/to/Clean.apk path/to/Infected.apk
```

---

## Repository Structure

```
BlackCat-AI-Core/
│
├── CyberFixBot/                        # RAG Chatbot module
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── vuln_fixes_expanded.csv         # Knowledge base
│   └── README.md
│
├── ReportGenerator/                    # Report generation module
│   ├── BlackCat_Report_Generator.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── vuln_fixes_expanded.csv
│   └── README.md
│
├── MalwareDetection/                   # APK analysis module
│   ├── app.py
│   ├── selftest.py
│   ├── random_forest_malware_model.joblib
│   ├── features-categories.csv
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
└── README.md                           # ← You are here
```

---

## Deployment

All three modules are deployed as independent **Docker-based Hugging Face Spaces**.

Each Space requires the following environment variable set as a **Repository Secret**:

```
GROQ_API_KEY=your_groq_api_key_here
```
*(Not needed for the Malware Detection module)*

Interactive API docs (Swagger UI) are available at:
```
https://mirao-blackcat-report-generator.hf.space/docs
https://mirao-blackcat-chatbot.hf.space/docs
https://mirao-malware-detection.hf.space/docs
```

---

## Local Setup

```bash
# Clone the repo
git clone https://github.com/mira203/BlackCat-AI-Core.git
cd BlackCat-AI-Core

# Pick a module, e.g. CyberFixBot
cd CyberFixBot

# Install dependencies
pip install -r requirements.txt

# Set your API key
export GROQ_API_KEY=your_key_here

# Run the server
uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## Built By

**Mira Osama Foukeh** — AI Lead, BlackCat Project  
Computer Science Graduate · Modern Academy for Science and Technology · 2026  
Specialization: AI/ML Engineering · NLP · RAG Pipelines · Cybersecurity AI

---

## License

This project was developed as a graduation project. All rights reserved.
