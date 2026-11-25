import shutil
import uuid
import traceback
import gc
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.security import repo_dir, sanitize_repo_id
from app.ingestion.file_filter import discover_files
from app.ingestion.zip_handler import extract_zip
from app.ingestion.github_fetcher import clone_github_repo
from app.processing.chunker import chunk_file
from app.schemas.repository import RepoInfo, UploadResponse, GithubUrlRequest
from app.vectorstore.indexer import delete_repo, index_chunks

router = APIRouter()

UPLOAD_TMP = Path("_uploads")
MAX_FILES = 100  # Prevent memory crash

def _process_repo_files(repo_id: str, target_dir: Path) -> dict:
    """Shared logic to filter, chunk, and index a repository directory."""
    files = list(discover_files(target_dir))
    if not files:
        raise ValueError("No indexable source files found.")
    
    if len(files) > MAX_FILES:
        raise ValueError(f"Repository too large ({len(files)} files). Max is {MAX_FILES}.")

    all_chunks = []
    for f in files:
        try:
            all_chunks.extend(chunk_file(f, target_dir))
        except Exception as e:
            print(f"Skipping file {f}: {e}")
            continue

    if not all_chunks:
        raise ValueError("No code chunks could be produced from these files.")

    index_chunks(repo_id, all_chunks)
    
    return {
        "repo_id": repo_id,
        "files_indexed": len(files),
        "chunks_indexed": len(all_chunks)
    }

@router.post("/repos/upload")
def upload_repository(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        return JSONResponse(status_code=400, content={"detail": "File must be a .zip"})

    repo_id = f"repo_{uuid.uuid4().hex[:12]}"
    UPLOAD_TMP.mkdir(parents=True, exist_ok=True)
    tmp_zip = UPLOAD_TMP / f"{repo_id}.zip"

    try:
        with open(tmp_zip, "wb") as out:
            shutil.copyfileobj(file.file, out)

        target_dir = repo_dir(repo_id)
        extract_zip(tmp_zip, target_dir)
        return _process_repo_files(repo_id, target_dir)

    except Exception as e:
        print("=== INGESTION ERROR ===")
        traceback.print_exc()
        try:
            delete_repo(repo_id)
            shutil.rmtree(repo_dir(repo_id), ignore_errors=True)
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"detail": str(e)})
    finally:
        if tmp_zip.exists():
            tmp_zip.unlink(missing_ok=True)
        gc.collect()

@router.post("/repos/github")
def upload_github_repository(req: GithubUrlRequest):
    repo_id = f"repo_{uuid.uuid4().hex[:12]}"
    target_dir = repo_dir(repo_id)

    try:
        clone_github_repo(req.url, target_dir)
        return _process_repo_files(repo_id, target_dir)
    except Exception as e:
        print("=== GITHUB CLONE ERROR ===")
        traceback.print_exc()
        try:
            delete_repo(repo_id)
            shutil.rmtree(repo_dir(repo_id), ignore_errors=True)
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"detail": str(e)})
    finally:
        gc.collect()

@router.get("/repos/{repo_id}/info", response_model=RepoInfo)
def get_repo_info(repo_id: str):
    repo_id = sanitize_repo_id(repo_id)
    target = repo_dir(repo_id)
    if not target.exists() or not any(target.iterdir()):
        raise HTTPException(status_code=404, detail="Repository not found")
    files = list(discover_files(target))
    return RepoInfo(repo_id=repo_id, files_indexed=len(files), chunks_indexed=0)

@router.delete("/repos/{repo_id}")
def delete_repository(repo_id: str):
    repo_id = sanitize_repo_id(repo_id)
    removed = delete_repo(repo_id)
    target = repo_dir(repo_id)
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    return {"repo_id": repo_id, "vectors_removed": removed}