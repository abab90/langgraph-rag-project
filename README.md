# langgraph-rag-project
LangGraph Agentic RAG Workflow with Human in the Loop

                                                 
                                                                      عبدالله خالد الفهد , عبدالاله محمد البشر

## 📝 Workflow Logic & Patterns Used:

* **Router Pattern:** Used to intelligently direct the user query to the appropriate knowledge domain (Support Policy vs. Course Info) based on intent.
* **RAG Pattern:** Applied to retrieve precise, localized knowledge from external documents rather than relying on frozen model weights.
* **Human-in-the-Loop Pattern:** Integrated using LangGraph interrupts to pause execution and request human confirmation before processing sensitive actions like refund approvals.
