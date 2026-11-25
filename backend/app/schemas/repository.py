from pydantic import BaseModel

class UploadResponse(BaseModel):
    repo_id: str
    files_indexed: int
    chunks_indexed: int

class RepoInfo(BaseModel):
    repo_id: str
    files_indexed: int
    chunks_indexed: int

class GithubUrlRequest(BaseModel):
    url: str