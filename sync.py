import json
import os
import subprocess
import time

from aqt import mw
from . import tracker


# ── helpers ──────────────────────────────────────────────────────────────────

def _addon_dir() -> str:
    """Get the addon directory (which is the git repo)."""
    return os.path.dirname(__file__)


def _get_user_dir(username: str) -> str:
    """Get the user directory path for shared data."""
    addon_dir = _addon_dir()
    user_dir = os.path.join(addon_dir, "User", username.lower().replace(" ", "_"))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def _git(repo: str, *args, timeout: int = 20) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["git", "-C", repo] + list(args),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode == 0, r.stderr.strip()
    except FileNotFoundError:
        return False, "git not found – please install Git"
    except subprocess.TimeoutExpired:
        return False, "git command timed out"
    except Exception as e:
        return False, str(e)


# ── public API ────────────────────────────────────────────────────────────────

def push_my_data() -> tuple[bool, str]:
    """
    1. git pull --rebase
    2. Write / overwrite our own JSON file to User/{username}/
    3. git add + commit + push
    Returns (success, message).
    """
    repo = _addon_dir()
    if not os.path.isdir(repo):
        return False, f"Directory not found: {repo}"

    # Load config from root config.json (gitignored, local only)
    config_path = os.path.join(repo, "config.json")
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
    except Exception as e:
        return False, f"Cannot read config.json: {e}"
    
    name: str = cfg.get("my_name", "").strip()
    if not name:
        return False, "my_name not set in config"

    # Pull first
    ok, err = _git(repo, "pull", "--rebase", "origin", "main")
    if not ok:
        # non-fatal – repo might be offline; we'll still write + try push
        pass

    # Write data to User/{username}/{username}.json
    user_dir = _get_user_dir(name)
    data = {
        "name": name,
        "color": cfg.get("my_color", "#378ADD"),
        "reviews": tracker.get_my_reviews(),
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    safe_name = name.lower().replace(" ", "_")
    file_path = os.path.join(user_dir, f"{safe_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Commit the user file
    relative_path = os.path.relpath(file_path, repo)
    _git(repo, "add", relative_path)
    commit_msg = f"update {name} {time.strftime('%Y-%m-%d %H:%M')}"
    ok, err = _git(repo, "commit", "-m", commit_msg)
    if not ok and "nothing to commit" not in err:
        return False, f"git commit failed: {err}"

    # Push
    ok, err = _git(repo, "push", "origin", "main")
    if not ok:
        return False, f"git push failed: {err}"

    return True, "Synced successfully"


def pull_all_data() -> list[dict]:
    """
    git pull, then read all *.json files in User/{username}/ directories.
    Returns list of friend data dicts.
    """
    repo = _addon_dir()
    if not os.path.isdir(repo):
        return []

    _git(repo, "pull", "--rebase", "origin", "main")

    result = []
    user_dir = os.path.join(repo, "User")
    if not os.path.isdir(user_dir):
        return result

    # Read all user directories
    for username in sorted(os.listdir(user_dir)):
        user_path = os.path.join(user_dir, username)
        if not os.path.isdir(user_path):
            continue
        
        # Read {username}.json from User/{username}/
        for fname in os.listdir(user_path):
            if not fname.endswith(".json") or fname == "config.json":
                continue
            try:
                with open(os.path.join(user_path, fname), encoding="utf-8") as f:
                    obj = json.load(f)
                if "name" in obj and "reviews" in obj:
                    result.append(obj)
            except Exception:
                pass
    return result
