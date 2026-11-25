import shutil
import git
from pathlib import Path

def clone_github_repo(url: str, dest_dir: Path) -> None:
    """Safely clone a GitHub repo. Prevents SSRF by strictly checking the URL."""
    if not url.startswith("https://github.com/"):
        raise ValueError("Only valid https://github.com/ URLs are allowed.")
    
    if dest_dir.exists():
        shutil.rmtree(dest_dir, ignore_errors=True)
    
    # depth=1 means only download the latest code, no history (saves time/space)
    git.Repo.clone_from(url, dest_dir, depth=1)