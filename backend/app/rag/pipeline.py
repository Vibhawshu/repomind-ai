from app.retrieval.context_builder import build_context
from app.retrieval.semantic_retriever import retrieve_chunks
from app.rag.llm_client import chat
from app.rag.prompt_templates import SYSTEM_PROMPT, build_user_prompt


def answer_question(repo_id: str, question: str, top_k: int = 5) -> dict:
    hits = retrieve_chunks(repo_id=repo_id, query=question, top_k=top_k)
    if not hits:
        return {
            "answer": "I could not find any indexed code in this repository to answer the question.",
            "sources": [],
        }

    context, sources = build_context(repo_id, hits)
    if not sources:
        return {
            "answer": "The most relevant chunks had no readable content (files may have been removed).",
            "sources": [],
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(question, context)},
    ]
    answer = chat(messages)
    return {"answer": answer, "sources": sources}
