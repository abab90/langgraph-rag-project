# langgraph-rag-project

LangGraph Agentic RAG Workflow with Human in the Loop

## Prepared By:
* **عبدالله خالد الفهد**
* **عبدالإله محمد البشر**

---

## Track & Pattern Classification

* **Track Chosen:** Agentic Workflows & Multi-Pattern Systems.
* **Workflow Pattern:** **Agentic RAG with Human-in-the-Loop (HITL) Interrupts**.
* **RAG Architecture Choice:** **Agentic RAG (Router-Based Retrieval)**.
  * *Justification:* We selected an Agentic/Router RAG pattern instead of a naive 2-Step pipeline because direct similarity retrieval on all queries introduces noise and unnecessary embedding calls. Using an LLM-driven router ensures vector database queries are executed strictly when domain context (e.g., support or course policy) is needed.

---

## Rubric Write-Up & Architectural Patterns Used

1. **LLM Router Pattern:** Replaced naive string matching with an LLM structured output classification using **Google Gemini (`gemini-1.5-flash`)**. The LLM dynamically determines the query destination (`support`, `course`, or `general`).
2. **Vector RAG Pipeline:** Integrated FAISS vector store with **FastEmbed Embeddings** (`FastEmbedEmbeddings`). Document chunks are retrieved via vector similarity search top-k retrieval rather than hardcoded string returns.
3. **Human-in-the-Loop (HITL):** Built an end-to-end interrupt and resume workflow using `langgraph.types.interrupt` and `Command(resume="yes")` to pause execution for human verification on sensitive refund operations.
4. **Resilience & Error Handling:** Implemented `RetryPolicy(max_attempts=3)` decorators on external LLM and vector store tasks to automatically retry transient network failures, alongside a fallback loopback mechanism for invalid routing states.
5. **Observability:** Enabled LangSmith tracing configuration (`LANGCHAIN_TRACING_V2=true`) to monitor state transitions, routing decisions, latency bottlenecks, and vector retrieval relevance.

---

## LangSmith Trace Insights

* **Observation:** During execution tracing, the LLM Router task completed classification in ~350ms, while vector retrieval took ~120ms. The trace clearly indicated state suspension at the `interrupt` node, preserving full context in `MemorySaver` until the `Command(resume="yes")` event re-instantiated execution to generate the final dynamic LLM output.
