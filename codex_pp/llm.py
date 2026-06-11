"""
llm.py - LLM 调用封装
===================
- 兼容 OpenAI 接口标准
- 支持流式输出
- 统计 token
"""

import sys
import time
from typing import Iterator, Optional

from openai import OpenAI

from . import config


def make_client(provider_cfg: dict) -> OpenAI:
    """根据 provider 配置创建 OpenAI 客户端"""
    api_key = provider_cfg.get("api_key", "")
    if not api_key:
        raise ValueError("API key 未设置,先用 `codex-pp config set-key <provider> <key>` 设置")

    base_url = provider_cfg.get("base_url", "https://api.openai.com/v1")
    timeout = provider_cfg.get("timeout", 60)

    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
    )


def chat(
    provider_name: str,
    messages: list,
    model: Optional[str] = None,
    stream: bool = True,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    """
    发送对话请求

    Returns:
        {
            "content": "回复内容",
            "model": "gpt-4o-mini",
            "input_tokens": 100,
            "output_tokens": 50,
            "latency": 1.23,
        }
    """
    cfg = config.load_config()
    provider_cfg = config.get_provider_config(cfg, provider_name)

    if not provider_cfg.get("enabled", False):
        raise RuntimeError(f"Provider {provider_name} 未启用")

    client = make_client(provider_cfg)
    used_model = model or provider_cfg.get("default_model", "gpt-4o-mini")

    start = time.time()
    try:
        if stream:
            # 流式输出
            response = client.chat.completions.create(
                model=used_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            content_parts = []
            input_tokens = 0
            output_tokens = 0
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    content_parts.append(delta)
                    print(delta, end="", flush=True)
                if chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens or 0
                    output_tokens = chunk.usage.completion_tokens or 0
            print()
            content = "".join(content_parts)
        else:
            # 非流式
            response = client.chat.completions.create(
                model=used_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
    except Exception as e:
        raise RuntimeError(f"调用失败: {e}")

    latency = time.time() - start

    # 记录用量
    config.record_usage(cfg, used_model, input_tokens, output_tokens)

    return {
        "content": content,
        "model": used_model,
        "provider": provider_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency": latency,
    }


def list_models_for_provider(provider_name: str) -> list:
    """列出 provider 支持的模型(简单映射)"""
    models_map = {
        "skillai": [
            "gpt-4o-mini", "gpt-4o", "claude-sonnet-4-5", "claude-3-5-sonnet",
            "gemini-2.0-flash-exp", "llama-3.3-70b-versatile",
        ],
        "openai": [
            "gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini",
        ],
        "anthropic": [
            "claude-sonnet-4-5", "claude-3-5-sonnet", "claude-3-haiku",
        ],
        "github_models": [
            "gpt-4o-mini", "gpt-4o", "o1-mini",
            "meta-llama-3.3-70b-instruct", "phi-4", "deepseek-r1",
        ],
        "groq": [
            "llama-3.3-70b-versatile", "llama-3.1-8b-instant",
            "mixtral-8x7b-32768", "deepseek-r1-distill-llama-70b",
        ],
        "gemini": [
            "gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro",
        ],
    }
    return models_map.get(provider_name, [])