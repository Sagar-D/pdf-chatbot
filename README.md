# 📄 PDF Chatbot — Document-Grounded Retrieval-Augmented Generation (RAG)

A **document-grounded RAG chatbot** that answers user queries based strictly on uploaded PDF documents, with a fallback to regular chatbot behavior when no document is provided.

This project demonstrates a production-style RAG pipeline with **hybrid retrieval**, **document grounding guarantees**, **configurable query enrichment**, and **clear separation between backend APIs and demo UI**.

---



## 🚀 Features

- ✔️ Upload **multiple PDF files (up to 5)** per user
- ✔️ Perform **RAG across all uploaded documents**
- ✔️ Strict **document-grounded answering** to prevent hallucinations 
- ✔️ **User-level isolation** using metadata filtering in vector store
- ✔️ **Hybrid retrieval** (Semantic + Keyword search)
- ✔️ **Cross-encoder reranking** for improved relevance
- ✔️ **LangGraph-based orchestration** with conditional routing
- ✔️ Configurable **query enrichment**
- ✔️ Modular backend APIs using FastAPI
- ✔️ Interactive demo UI using Gradio

---



## 📦 Tech Stack

| Category | Tools Used |
|--------|------------|
| Language | Python |
| PDF Parsing | Docling |
| Embeddings | HuggingFace / SentenceTransformers |
| Vector Store | Chroma |
| Retrieval | Hybrid (Similarity Search + BM25) |
| Reranking | Cross-Encoder |
| Orchestration | LangGraph |
| LLM | Gemini / Qwen (via Ollama) |
| Backend APIs | FastAPI |
| Demo UI | Gradio |

---



## 🧠 Application Behavior

The chatbot operates in **two distinct modes**:


### 1️⃣ Document-Grounded Mode (PDF Attached)

- Users can upload **up to 5 PDF files**
- Retrieval is performed **across all uploaded documents**
- The chatbot can answer:
  - questions related to a single document
  - questions requiring context from **multiple documents**

#### Relevance Enforcement
- If **relevant content is found** during retrieval  
  → The system generates an answer using RAG
- If **no relevant content is found**  
  → The system returns a **generic message** indicating that  
    **document-grounded mode is enabled** and no relevant context was found.

 > This prevents hallucinations and ensures answers are **strictly grounded in document content**.

---


### 2️⃣ Regular Chatbot Mode (No PDF Attached)

- If **no PDF is uploaded**, the chatbot behaves like a **standard LLM chatbot**
- Answers are generated using the selected LLM **without retrieval**

### User-Level Data Isolation

- Each document chunk is stored with metadata:
  - `user_id`
  - document identifiers
- All retrieval queries apply **metadata filtering on `user_id` and document_ids**
- This guarantees:
  - no document leakage across users
  - no embedding mixing between users

This design supports **safe multi-user deployments**.

---


## 🧠 How It Works


### 1. PDF Upload & Parsing

- Uploaded PDFs are parsed using **Docling**
- Extracted content is converted into **structured markdown**


### 2. Chunking & Embedding

- Markdown text is split into semantically meaningful chunks
- Each chunk is embedded using **SentenceTransformers**
- Embeddings are stored in **ChromaDB**


### 3. Hybrid Retrieval + Reranking

1. A weighted hybrid retriever is used:
   - **Similarity Search (Embeddings)** → weight `0.6`
   - **BM25 (Keyword Search)** → weight `0.4`

2. Retrieved candidates are then:
   - reranked using a **cross-encoder**
   - filtered based on relevance thresholds

This improves both semantic recall and exact keyword matching.

Retrieval is:
- scoped per user via metadata filtering
- performed across all uploaded documents


### 4. LangGraph-Based Orchestration

The RAG pipeline is orchestrated using **LangGraph**, enabling:

- Conditional routing based on retrieval outcome
- Explicit control over execution flow

#### Routing Logic:
- If relevant context **is found** → route to LLM with retrieved chunks
- If relevant context **is NOT found** → skip LLM and return a grounded error message
- If no documents are attached → route directly to LLM

This avoids unnecessary LLM calls and enforces grounding guarantees.

---



### 🔧 Query Enrichment

Query enrichment can be enabled or disabled based on the interface used:

### REST API
- Controlled via configuration passed in the **request body**

### Gradio UI
- Controlled via a **feature toggle (checkbox)** in the UI

This allows experimentation with:
- Query rewriting
- Context expansion
- Retrieval optimization strategies

---



## 🛠 Installation

> Make sure you have **Python 3.8+** installed.

1. Clone the repository:

```bash
git clone https://github.com/Sagar-D/pdf-chatbot.git
cd pdf-chatbot
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Setup environment variables:

```bash
ENV="dev"
# For Gemini
GOOGLE_API_KEY=<GOOGLE_API_KEY>
# For local LLMs via Ollama
OLLAMA_BASE_URL=http://localhost:11434
```



## ▶️ Running the Project


### 1️⃣ Backend REST APIs (FastAPI)

Start the backend server:

```bash
fastapi run ./pdf_chatbot/main.py
```
Access API documentation (Swagger UI) at: http://0.0.0.0:8000/docs


### 2️⃣ Demo Application (Gradio UI)

Launch the demo UI:

```bash
python3 -m pdf_chatbot.demo  
```
Access the UI at: http://localhost:8080/



## 🎯 Use Cases

- PDF-based question answering systems
- Internal document assistants
- Compliance-aware AI applications
- Experimentation with hybrid retrieval strategies
- Multi-document RAG experimentation
- Learning production-grade RAG system design

Limitations

- Retrieval is intentionally scoped per user
- Cross-user document access is not supported
- Answer quality and Performance depends on:
  - chunking strategy
  - hybrid retrieval weights
  - embedding model quality
  - reranking thresholds
 
🧪 Future Improvements

- **Decouple RAG and non-RAG execution paths:** 
  Separate RAG-specific workflows from general API flows, enabling RAG pipelines to run on GPU-enabled infrastructure while keeping lightweight API operations on CPU-only environments.
- **Asynchronous document ingestion:** 
  Move document parsing, chunking, and embedding to asynchronous/background jobs so users can continue interacting with the system without blocking on ingestion.
- **Persistent vector storage across sessions:** 
  Persist embeddings beyond application restarts to support long-lived user sessions and reuse previously ingested documents.
- **Streaming response generation:** 
  Enable token-level streaming from the LLM to improve perceived latency and user experience during long responses.
- **Observability and tracing for AI workflows:** 
  Add end-to-end tracing, logging, and metrics for RAG pipelines using tools such as LangSmith or OpenTelemetry to improve debuggability and system insight.

🙌 Author

Built by Sagar D as part of hands-on learning in Retrieval-Augmented Generation, LLM systems, and AI engineering.
