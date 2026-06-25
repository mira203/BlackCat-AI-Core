import os
import json
import time
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set!")

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Pydantic Models
class VulnerabilityItem(BaseModel):
    url: str
    alert: str
    param: str
    attack: str
    risk: str

class VulnerabilityRequest(BaseModel):
    vulnerabilityToAI: List[VulnerabilityItem]

# Vector Store & LLM Setup 
print("Loading vector store...")
loader = CSVLoader("vuln_fixes_expanded.csv")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
splits = splitter.split_documents(docs)

embedding = FastEmbedEmbeddings()
vectorstore = Chroma.from_documents(splits, embedding=embedding)
retriever = vectorstore.as_retriever()

llm = ChatOpenAI(
    model="llama-3.1-8b-instant",
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=os.environ["GROQ_API_KEY"],
    temperature=0.1,
    max_tokens=800
)

prompt = PromptTemplate.from_template("""
You are a senior cybersecurity report writer. Your job is to write clean, professional, and concise vulnerability reports.

**Strict Rules:**
- Output ONLY the report
- Follow the exact structure and formatting below
- Do NOT add any extra sections (no Reasoning, no Recommendations table, no extra explanations)
- Do NOT invent information
- Use professional but clear language
- Keep Summary short (3-5 sentences max)
- Use the exact payload from scan data

**Scan Data:**
{input}

**Report Format (Follow Exactly):**

**Title:**
[Alert type] in `[affected endpoint/param]`

**Summary:**
A short professional summary here...

**Affected Endpoint:**
- *URL:* [url]
- *Method:* [GET/POST/etc]

**Vulnerable Parameter:**
`[param]`

## Steps to Reproduce

1. Send a request to:
   http
   [HTTP request]


2. Insert the following payload into the parameter [param]:

   txt
   [payload]


3. Forward the request.

4. Observe the response and confirm the vulnerability.

**Impact:**
- [Impact point 1]
- [Impact point 2]
- [Impact point 3]

**Severity:**
[risk]

Now generate the report using the scan data above.
""")

chain = (
    {
        "context": retriever | (lambda docs: "\n\n".join(doc.page_content for doc in docs)),
        "input": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# FastAPI App 
app = FastAPI(
    title="BlackCat Report Engine",
    description="AI-powered vulnerability report generator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "BlackCat Report Engine is running on HuggingFace Spaces"}

@app.post("/generate-report/")
async def generate_report_endpoint(request: VulnerabilityRequest):
    """
    Receives JSON body:
    {
        "vulnerabilityToAI": [ { ...vuln fields... }, ... ]
    }
    Returns a JSON containing the AI generated reports.
    """
    vulnerabilities = request.vulnerabilityToAI
    print(f"Received {len(vulnerabilities)} vulnerabilities.")

    all_reports = []
    for i, vuln in enumerate(vulnerabilities):
        print(f"Processing vulnerability {i + 1}/{len(vulnerabilities)}: {vuln.alert}")

        vuln_text = (
            f"Alert      : {vuln.alert}\n"
            f"URL        : {vuln.url}\n"
            f"Parameter  : {vuln.param}\n"
            f"Attack     : {vuln.attack}\n"
            f"Risk Level : {vuln.risk}\n"
        )

        report_content = chain.invoke(vuln_text)

        all_reports.append({
            "alert": vuln.alert,
            "url": vuln.url,
            "ai_report": report_content
        })

        time.sleep(1)  # Protection from Groq Rate Limit

    print("Done! Returning JSON response.")

    return {
        "status": "success",
        "total_reports": len(all_reports),
        "data": all_reports
    }
