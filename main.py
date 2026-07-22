# -*- coding: utf-8 -*-
import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.func import entrypoint, task
from langgraph.types import interrupt, Command, RetryPolicy
from langgraph.checkpoint.memory import MemorySaver

# 1. Tracing Configuration (موقف لمنع أخطاء المصادقة محلياً)
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# 2. Gemini API Key Configuration
os.environ["GOOGLE_API_KEY"] = os.getenv(
    "GOOGLE_API_KEY", 
    "AQ.Ab8RN6LvaOpGwYME71RcT788syv6p2WqJmLWQUo8aS7jq6_SlA"
)

# 3. Local Knowledge Base & Vector Embeddings
doc1_content = "Support Policy: Refund is allowed within 14 days of purchase if overall usage is below 10%."
doc2_content = "Course Info: AI Engineering course requires basic Python skills and linear algebra knowledge."

splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
docs = splitter.split_documents([
    Document(page_content=doc1_content, metadata={"category": "support"}),
    Document(page_content=doc2_content, metadata={"category": "course"})
])

embeddings = FastEmbedEmbeddings()
vector_store = FAISS.from_documents(docs, embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 1})

# Initialize Real LLM (Gemini 1.5 Flash)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# 4. Router Schema
class RouteQuery(BaseModel):
    destination: Literal["support", "course", "general"] = Field(
        ..., description="Route query destination."
    )

# 5. Tasks with Real LLM Calls, RetryPolicy, and Graceful Fallback
@task(retry_policy=RetryPolicy(max_attempts=3))
def route_query_task(user_query: str) -> str:
    """Uses REAL LLM to classify user intent for routing with keyword fallback."""
    try:
        structured_llm = llm.with_structured_output(RouteQuery)
        res = structured_llm.invoke(f"Classify the following query: '{user_query}'")
        return res.destination
    except Exception:
        # Fallback Strategy: Keyword matching if LLM structured output invocation fails
        query_lower = user_query.lower()
        if any(k in query_lower for k in ["refund", "policy", "money", "support"]):
            return "support"
        return "course"

@task(retry_policy=RetryPolicy(max_attempts=3))
def retrieve_docs(user_query: str) -> str:
    """Retrieves context from FAISS Vector Store."""
    results = retriever.invoke(user_query)
    if results:
        return results[0].page_content
    return "No relevant context found."

@task(retry_policy=RetryPolicy(max_attempts=3))
def generate_final_response(user_query: str, context: str) -> str:
    """Uses REAL LLM to generate dynamic answer based on retrieved context."""
    try:
        prompt = f"Context from Knowledge Base:\n{context}\n\nUser Question: {user_query}\nAnswer professionally based on the context:"
        response = llm.invoke(prompt)
        return response.content
    except Exception:
        return f"Based on retrieved context:\n{context}"

# 6. Main Workflow Execution
@entrypoint(checkpointer=MemorySaver())
def main_workflow(inputs: dict):
    user_query = inputs.get("query", "")
    
    # Step 1: Real LLM Routing
    route = route_query_task(user_query).result()
    
    # Step 2: Vector RAG Retrieval
    if route in ["support", "course"]:
        retrieved_context = retrieve_docs(user_query).result()
    else:
        retrieved_context = "No external context needed."
        
    # Step 3: Human-in-the-Loop Interrupt
    if route == "support" or "refund" in user_query.lower():
        human_approval = interrupt({
            "question": f"Refund query detected ('{user_query}'). Approve request? (type 'yes' or 'no')"
        })
        if str(human_approval).strip().lower() != "yes":
            return "Operation cancelled by human supervisor."

    # Step 4: Real LLM Response Generation
    final_answer = generate_final_response(user_query, retrieved_context).result()
    return final_answer


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "session_demo_1"}}
    query = "What are the refund policy conditions?"
    
    print("\n--- [1] First Pass: Running Workflow (Triggers HITL Interrupt) ---")
    for chunk in main_workflow.stream({"query": query}, config=config):
        print(chunk)
        
    print("\n--- [2] Second Pass: Resuming Workflow with Supervisor Approval ---")
    for chunk in main_workflow.stream(Command(resume="yes"), config=config):
        print(chunk)
