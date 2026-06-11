"""
extras.py - 代码片段 + 历史命令
==================================
v0.4.0 新功能
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any

DATA_DIR = Path.home() / ".codex-pp" / "extras"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SNIPPETS_FILE = DATA_DIR / "snippets.json"
HISTORY_FILE = DATA_DIR / "history.json"

MAX_HISTORY = 200


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, data: Any):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ============== Snippets ==============

def add_snippet(name: str, content: str, tags: str = "", language: str = "python") -> Dict[str, Any]:
    """添加代码片段"""
    snippets = _load_json(SNIPPETS_FILE, [])
    snippet = {
        "id": int(time.time() * 1000),
        "name": name,
        "content": content,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "language": language,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "used": 0,
    }
    snippets.append(snippet)
    _save_json(SNIPPETS_FILE, snippets)
    return snippet


def list_snippets(tag: str = None, language: str = None, search: str = None) -> List[Dict[str, Any]]:
    """列出片段"""
    snippets = _load_json(SNIPPETS_FILE, [])
    if tag:
        snippets = [s for s in snippets if tag in s.get("tags", [])]
    if language:
        snippets = [s for s in snippets if s.get("language") == language]
    if search:
        q = search.lower()
        snippets = [s for s in snippets if q in s["name"].lower() or q in s["content"].lower()]
    return snippets


def get_snippet(snippet_id: int) -> Dict[str, Any] | None:
    """获取片段(并增加使用计数)"""
    snippets = _load_json(SNIPPETS_FILE, [])
    for s in snippets:
        if s["id"] == snippet_id:
            s["used"] = s.get("used", 0) + 1
            _save_json(SNIPPETS_FILE, snippets)
            return s
    return None


def delete_snippet(snippet_id: int) -> bool:
    """删除片段"""
    snippets = _load_json(SNIPPETS_FILE, [])
    new = [s for s in snippets if s["id"] != snippet_id]
    if len(new) == len(snippets):
        return False
    _save_json(SNIPPETS_FILE, new)
    return True


# ============== History ==============

def add_history(command: str, provider: str = "", model: str = "", exit_code: int = 0):
    """记录历史命令"""
    history = _load_json(HISTORY_FILE, [])
    history.append({
        "ts": time.time(),
        "ts_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "command": command[:200],  # 截断
        "provider": provider,
        "model": model,
        "exit_code": exit_code,
    })
    # 只保留最近 N 条
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    _save_json(HISTORY_FILE, history)


def get_history(limit: int = 20, provider: str = None, search: str = None) -> List[Dict[str, Any]]:
    """获取历史"""
    history = _load_json(HISTORY_FILE, [])
    if provider:
        history = [h for h in history if h.get("provider") == provider]
    if search:
        q = search.lower()
        history = [h for h in history if q in h["command"].lower()]
    return list(reversed(history))[:limit]


def clear_history():
    """清空历史"""
    _save_json(HISTORY_FILE, [])


# ============== Shell 补全 (bash) ==============

COMPLETION_SCRIPT = """# codex-pp shell completion for bash
# 添加到 ~/.bashrc:  source <(codex-pp completion bash)

_codex_pp_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="chat ask models config stats skill memory snippet history version help"

    case "${prev}" in
        codex-pp)
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            return 0
            ;;
        ask|chat)
            COMPREPLY=( $(compgen -W "--provider --model --system" -- ${cur}) )
            return 0
            ;;
        config)
            COMPREPLY=( $(compgen -W "set-key set-default enable disable list path lang export import" -- ${cur}) )
            return 0
            ;;
        skill)
            COMPREPLY=( $(compgen -W "list install show remove" -- ${cur}) )
            return 0
            ;;
        memory)
            COMPREPLY=( $(compgen -W "list set get delete" -- ${cur}) )
            return 0
            ;;
        snippet)
            COMPREPLY=( $(compgen -W "list show add delete search" -- ${cur}) )
            return 0
            ;;
        history)
            COMPREPLY=( $(compgen -W "--limit --provider --search --clear" -- ${cur}) )
            return 0
            ;;
        *)
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            return 0
            ;;
    esac
}
complete -F _codex_pp_completion codex-pp
"""


def get_completion_script(shell: str = "bash") -> str:
    """获取补全脚本"""
    if shell == "bash":
        return COMPLETION_SCRIPT
    return f"# {shell} 补全暂未实现"