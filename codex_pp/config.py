"""
config.py - 配置管理
==================
- 从 ~/.codex-pp/config.json 读取
- 支持多 provider 配置
- 中转 API 一键配置
"""

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".codex-pp"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "version": "0.1.0",
    "language": "zh",
    "default_provider": "skillai",
    "providers": {
        "skillai": {
            "name": "SkillAI (国内直连)",
            "base_url": "https://api.skillai.top",  # 注意:不带 /v1
            "api_key": "",
            "default_model": "gpt-4o-mini",
            "enabled": True,
        },
        "openai": {
            "name": "OpenAI 官方",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "default_model": "gpt-4o-mini",
            "enabled": False,
        },
        "anthropic": {
            "name": "Anthropic 官方",
            "base_url": "https://api.anthropic.com/v1",
            "api_key": "",
            "default_model": "claude-sonnet-4-5",
            "enabled": False,
        },
        "github_models": {
            "name": "GitHub Models (免费)",
            "base_url": "https://models.inference.ai.azure.com",
            "api_key": "",
            "default_model": "gpt-4o-mini",
            "enabled": False,
        },
        "groq": {
            "name": "Groq (超快推理,免费)",
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": "",
            "default_model": "llama-3.3-70b-versatile",
            "enabled": False,
        },
        "gemini": {
            "name": "Google Gemini (免费层)",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "api_key": "",
            "default_model": "gemini-2.0-flash-exp",
            "enabled": False,
        },
    },
    "current_model": {},
    "usage_stats": {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_requests": 0,
        "by_model": {},
    },
}


def ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """加载配置,不存在则创建默认配置"""
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 合并缺失字段(升级时)
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
    # 合并缺失 providers
    for pname, pcfg in DEFAULT_CONFIG["providers"].items():
        if pname not in cfg.get("providers", {}):
            cfg.setdefault("providers", {})[pname] = pcfg

    return cfg


def save_config(cfg: dict):
    """保存配置"""
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_provider_config(cfg: dict, provider_name: str = None) -> dict:
    """获取指定 provider 配置"""
    if provider_name is None:
        provider_name = cfg.get("default_provider", "skillai")
    return cfg["providers"].get(provider_name, {})


def set_api_key(provider_name: str, api_key: str):
    """设置 provider 的 API key"""
    cfg = load_config()
    if provider_name not in cfg["providers"]:
        raise ValueError(f"未知 provider: {provider_name}")
    cfg["providers"][provider_name]["api_key"] = api_key
    cfg["providers"][provider_name]["enabled"] = bool(api_key)
    save_config(cfg)


def enable_provider(provider_name: str, enabled: bool = True):
    """启用 / 禁用 provider"""
    cfg = load_config()
    if provider_name not in cfg["providers"]:
        raise ValueError(f"未知 provider: {provider_name}")
    cfg["providers"][provider_name]["enabled"] = enabled
    save_config(cfg)


def set_default_provider(provider_name: str):
    """设置默认 provider"""
    cfg = load_config()
    if provider_name not in cfg["providers"]:
        raise ValueError(f"未知 provider: {provider_name}")
    cfg["default_provider"] = provider_name
    save_config(cfg)


def record_usage(cfg: dict, model: str, input_tokens: int, output_tokens: int):
    """记录用量"""
    cfg["usage_stats"]["total_input_tokens"] += input_tokens
    cfg["usage_stats"]["total_output_tokens"] += output_tokens
    cfg["usage_stats"]["total_requests"] += 1
    if model not in cfg["usage_stats"]["by_model"]:
        cfg["usage_stats"]["by_model"][model] = {
            "input": 0, "output": 0, "requests": 0
        }
    cfg["usage_stats"]["by_model"][model]["input"] += input_tokens
    cfg["usage_stats"]["by_model"][model]["output"] += output_tokens
    cfg["usage_stats"]["by_model"][model]["requests"] += 1
    save_config(cfg)


def get_usage_stats() -> dict:
    """获取用量统计"""
    return load_config()["usage_stats"]


def mask_key(key: str) -> str:
    """遮蔽 API key 中间部分"""
    if not key or len(key) < 12:
        return "****"
    return f"{key[:4]}...{key[-4:]} (长度: {len(key)})"