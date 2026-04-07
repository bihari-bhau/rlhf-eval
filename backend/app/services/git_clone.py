import re
import shutil
import subprocess
from pathlib import Path

from app.config import settings


def parse_github_url(url: str) -> str:
    url = url.strip().rstrip("/")
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url, re.I)
    if not m:
        raise ValueError("URL must look like https://github.com/owner/repo")
    owner, name = m.group(1), m.group(2)
    return f"{owner}/{name}"


def clone_or_update(full_name: str, github_url: str) -> str:
    base = Path(settings.clone_base_dir)
    base.mkdir(parents=True, exist_ok=True)
    target = base / full_name.replace("/", "__")
    if target.exists():
        subprocess.run(
            ["git", "-C", str(target), "fetch", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(target), "pull", "--ff-only"],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        subprocess.run(
            ["git", "clone", "--depth", "1", github_url, str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
    return str(target.resolve())


def remove_local_clone(local_path: str | None) -> None:
    if not local_path:
        return
    p = Path(local_path)
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
