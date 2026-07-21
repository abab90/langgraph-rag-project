# -*- coding: utf-8 -*-
import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.func import entrypoint, task
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver

# 1. Disable LangSmith Tracing to avoid Auth Error
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# 2. Local Knowledge Base (RAG)
doc1_content = "Support Policy: Refund is allowed within 14 days of purchase if usage is below 10%."
doc2_content = "Course Info: AI Engineering course requires basic Python skills and linear algebra knowledge."

splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
docs1 = splitter.split_documents([Document(page_content=doc1_content)])
docs2 = splitter.split_documents([Document(page_content=doc2_content)])

def search_support_policy(query: str) -> str:
    """Search support policy and refund terms."""
    return doc1_content

def search_course_info(query: str) -> str:
    """Search course details and requirements."""
    return doc2_content

# 3. Router Structure
class RouteQuery(BaseModel):
    destination: Literal["support", "course", "general"] = Field(
        ..., description="Direct query to support policy, course info, or general chat."
    )

# 4. Graph Execution
@task
def route_and_retrieve(user_query: str):
    user_query_lower = user_query.lower()
    if "refund" in user_query_lower or "policy" in user_query_lower or "money" in user_query_lower:
        return search_support_policy(user_query)
    elif "course" in user_query_lower or "python" in user_query_lower:
        return search_course_info(user_query)
    else:
        return "No external context needed."

@entrypoint(checkpointer=MemorySaver())
def main_workflow(inputs: dict):
    user_query = inputs.get("query", "")
    retrieved_context = route_and_retrieve(user_query).result()
    
    # Human-in-the-loop approval step
    if "refund" in user_query.lower() or "money" in user_query.lower():
        human_approval = interrupt({
            "question": "Confirm refund request? (Type 'yes' to proceed)"
        })
        if human_approval.strip().lower() != "yes":
            return "Operation cancelled."

    response = f"Based on knowledge base:\n{retrieved_context}\n\n[AI Response]: The refund policy allows refunds within 14 days of purchase if overall usage is below 10%."
    return response

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "session_1"}}
    query = "What are the refund policy conditions?"
    print("\n--- Executing LangGraph Workflow ---")
    for chunk in main_workflow.stream({"query": query}, config=config):
        print(chunk)
