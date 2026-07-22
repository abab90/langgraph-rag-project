# langgraph-rag-project

LangGraph Agentic RAG Workflow with Human in the Loop

## Prepared By:
* **عبدالله خالد الفهد**
* **عبدالإله محمد البشر**

---

## Track & Pattern Classification

* **Official Track Assigned:** **Track C (Routing between domain knowledge sources)**.
* **Workflow Pattern:** **Agentic RAG with Human-in-the-Loop (HITL) Interrupts**.
* **RAG Architecture Choice:** **Agentic RAG (Router-Based Retrieval)**.
  * *Justification:* We selected an Agentic/Router RAG pattern (Track C) over a naive 2-step retrieval pipeline because executing vector search blindly across all user queries introduces noise and unnecessary embedding lookups. By using an LLM-driven router, the system selectively routes queries either to domain-specific knowledge bases (Support Policy vs. Course Info) or skips external retrieval entirely when unnecessary.

---

## Rubric Write-Up & Architectural Patterns Used

1. **LLM Router Pattern:** Replaced static intent matching with structured LLM output classification using **Google Gemini (`gemini-1.5-flash`)**. The LLM dynamically determines the target domain (`support`, `course`, or `general`).
2. **Vector RAG Pipeline:** Integrated a local FAISS vector store with **FastEmbed Embeddings** (`FastEmbedEmbeddings`). Chunks generated via `RecursiveCharacterTextSplitter` are embedded and retrieved dynamically through similarity search top-k matching.
3. **Human-in-the-Loop (HITL):** Implemented state persistence and human verification using `langgraph.types.interrupt` and `Command(resume="yes")`. The graph pauses execution upon identifying sensitive operations (e.g., refund queries) and resumes seamlessly upon supervisor authorization via `MemorySaver`.
4. **Resilience & Error Handling Strategies:**
   * **Task Retry Policy:** Decorated external tasks with `RetryPolicy(max_attempts=3)` to automatically recover from transient network or API rate-limit errors.
   * **Fallback Routing Mechanism:** Integrated a keyword-based fallback inside the routing task's exception handler to guarantee deterministic destination handling if structured LLM output invocation fails.
5. **Observability:** Prepared and structured for LangSmith tracing (`LANGCHAIN_TRACING_V2`) to enable execution graph logging, monitoring state transitions across tasks, and verifying human-in-the-loop state interrupts.

---

## Execution & Tracing Summary

* **Observed Execution Flow:** 
  1. The workflow initiates with query classification via `route_query_task`, resolving the intent to `support`.
  2. `retrieve_docs` fetches the relevant document chunk from FAISS (`Support Policy: Refund is allowed within 14 days...`).
  3. The execution encounters the `interrupt` node, persisting state in `MemorySaver` and waiting for human intervention.
  4. Upon issuing `Command(resume="yes")`, execution resumes at `generate_final_response`, where Gemini 1.5 Flash synthesizes the final professional response based on retrieved context.
