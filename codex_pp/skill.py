"""
skill.py - Skill 管理
===================
对接 ai-agent-skills 仓库

用法:
  codex-pp skill list              # 列出可用 skills
  codex-pp skill install <name>    # 安装 skill 到 ~/.codex-pp/skills/
  codex-pp skill show <name>       # 显示 skill 详情
  codex-pp skill remove <name>     # 删除 skill
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

SKILLS_DIR = Path.home() / ".codex-pp" / "skills"
REPO_DIR = Path.home() / ".codex-pp" / "ai-agent-skills"
REPO_URL = "https://github.com/fast1188/ai-agent-skills.git"

# 已知的 skills 列表(避免 clone 整个仓库)
KNOWN_SKILLS = {
    "claude-code/api-fallback": {
        "name": "api-fallback",
        "desc": "撞限速时弹窗推荐 fallback 方案",
        "category": "claude-code",
    },
    "claude-code/chinese-dev-helper": {
        "name": "chinese-dev-helper",
        "desc": "中文开发助手,40+ 术语对照",
        "category": "claude-code",
    },
    "codex/codex-starter": {
        "name": "codex-starter",
        "desc": "OpenAI Codex CLI 5 分钟上手套装",
        "category": "codex",
    },
    "cursor/cursor-rules-pack": {
        "name": "cursor-rules-pack",
        "desc": "Cursor .cursorrules 配置包",
        "category": "cursor",
    },
    "openclaw/openclaw-deploy": {
        "name": "openclaw-deploy",
        "desc": "OpenClaw 一键远程部署",
        "category": "openclaw",
    },
    "hermes/hermes-tutorial": {
        "name": "hermes-tutorial",
        "desc": "Hermes Agent 中文教程",
        "category": "hermes",
    },
    "shared/agent-rules": {
        "name": "agent-rules",
        "desc": "跨 AI 工具统一开发规范",
        "category": "shared",
    },
    "shared/token-saver": {
        "name": "token-saver",
        "desc": "prompt 压缩,省 30-70% token",
        "category": "shared",
    },
    "shared/multi-agent-install": {
        "name": "multi-agent-install",
        "desc": "一键装 5 个 AI 工具",
        "category": "shared",
    },
    "shared/vscode-extension-pack": {
        "name": "vscode-extension-pack",
        "desc": "VSCode AI 扩展集合包",
        "category": "shared",
    },
    "shared/model-benchmark": {
        "name": "model-benchmark",
        "desc": "免费 AI 模型跑分对比",
        "category": "shared",
    },
}


def ensure_dirs():
    """确保目录存在"""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    REPO_DIR.parent.mkdir(parents=True, exist_ok=True)


def ensure_repo() -> bool:
    """确保 ai-agent-skills 仓库已 clone"""
    if (REPO_DIR / ".git").exists():
        return True

    print(f"克隆 ai-agent-skills 仓库到 {REPO_DIR} ...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(REPO_DIR)],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"克隆失败: {e.stderr.decode('utf-8', errors='ignore')[:200]}")
        return False


def list_skills() -> list:
    """列出所有已知 skills"""
    return [
        {
            "key": k,
            **v,
            "installed": (SKILLS_DIR / v["name"]).exists(),
        }
        for k, v in KNOWN_SKILLS.items()
    ]


def install_skill(skill_name: str) -> bool:
    """安装一个 skill"""
    # 找到 skill
    skill_info = None
    skill_path = None
    for k, v in KNOWN_SKILLS.items():
        if v["name"] == skill_name or k.endswith(skill_name):
            skill_info = v
            skill_path = k
            break

    if not skill_info:
        print(f"未知 skill: {skill_name}")
        print("用 `codex-pp skill list` 查看可用 skills")
        return False

    # 确保仓库已 clone
    if not ensure_repo():
        return False

    source = REPO_DIR / skill_path
    if not source.exists():
        print(f"仓库里没找到: {skill_path}")
        return False

    # 复制到本地 skills 目录
    dest = SKILLS_DIR / skill_info["name"]
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)

    print(f"[OK] 已安装: {skill_info['name']}")
    print(f"  路径: {dest}")
    print(f"  描述: {skill_info['desc']}")

    # 如果有 install.bat/install.sh,提示运行
    if (dest / "install.bat").exists():
        print(f"  提示: 跑 {dest}/install.bat 完成安装")
    elif (dest / "install.sh").exists():
        print(f"  提示: 跑 {dest}/install.sh 完成安装")

    return True


def show_skill(skill_name: str) -> Optional[dict]:
    """显示 skill 详情"""
    for k, v in KNOWN_SKILLS.items():
        if v["name"] == skill_name or k.endswith(skill_name):
            installed = (SKILLS_DIR / v["name"]).exists()
            skill_md = REPO_DIR / k / "SKILL.md" if (REPO_DIR / k / "SKILL.md").exists() else None
            return {
                "key": k,
                **v,
                "installed": installed,
                "skill_md": skill_md,
            }
    return None


def remove_skill(skill_name: str) -> bool:
    """删除一个 skill"""
    dest = SKILLS_DIR / skill_name
    if not dest.exists():
        print(f"未安装: {skill_name}")
        return False
    shutil.rmtree(dest)
    print(f"[OK] 已删除: {skill_name}")
    return True