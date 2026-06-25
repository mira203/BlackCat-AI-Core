import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferWindowMemory

#  Load & index documents (runs once at startup)
print("Loading CSV data...")
loader = CSVLoader("vuln_fixes_expanded.csv")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ",", " "]
)
splits = splitter.split_documents(docs)
print(f"Total chunks: {len(splits)}")

print("Building vector store...")
embedding = FastEmbedEmbeddings()
vectorstore = Chroma.from_documents(
    splits,
    embedding=embedding,
    collection_name="vuln_fixes_db"
)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.7}
)
print("Vector store ready.")

#  LLM  (Groq via OpenAI-compatible API)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

llm = ChatOpenAI(
    model="llama-3.1-8b-instant",
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=GROQ_API_KEY,
    temperature=0.1,
    max_tokens=2000
)

#  RAG chain
system_template = """You are CyberFixBot, an expert Cybersecurity Assistant specialized in vulnerability remediation.

Use the following retrieved context to answer the question.
If the answer is not in the context, say: "I don't have specific data on this vulnerability, but generally..."

Context:
{context}

Always structure your response as:
## Step 1: Vulnerability Summary
## Step 2: Root Cause
## Step 3: Fix / Remediation Steps
## Step 4: Code Example (if available)
## Step 5: Prevention Tips
"""

qa_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}")
])

memory = ConversationBufferWindowMemory(
    k=10,
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

retrieval_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True,
    verbose=False,
    combine_docs_chain_kwargs={"prompt": qa_prompt}
)

#  FastAPI app
app = FastAPI(
    title="CyberFixBot API",
    description="RAG-powered Cybersecurity Vulnerability Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources_count: int
    question: str


@app.get("/")
def root():
    return {"status": "running", "bot": "CyberFixBot", "version": "1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        response = retrieval_chain.invoke({"question": request.question})
        return QueryResponse(
            answer=response["answer"],
            sources_count=len(response["source_documents"]),
            question=request.question
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")
