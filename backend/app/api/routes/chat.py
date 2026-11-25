from fastapi import APIRouter, HTTPException

from app.core.security import repo_dir, sanitize_repo_id
from app.rag.pipeline import answer_question
from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        repo_id = sanitize_repo_id(req.repo_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not repo_dir(repo_id).exists():
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        result = answer_question(repo_id, req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG failed: {e}")

    return ChatResponse(**result)