"""
llm.py - LLM 调用封装
===================
- 兼容 OpenAI 接口标准
- 支持流式输出
- 统计 token
- 模型名白名单校验（避免向后端发不被接受的模型名）
"""

import sys
import time
from typing import Iterator, Optional

from openai import OpenAI

from . import config


# Provider → 支持的模型白名单
# 维护规则: 与对应后端实际接受的范围一致; 后端更新时同步修改此处
# - skillai (api.skillai.top): 后端仅接 deepseek-v4 系
# - 其他: 各上游官方模型
SUPPORTED_MODELS = {
    "skillai": [
        "deepseek-v4-flash",
        "deepseek-v4-pro",
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


class ModelNotSupportedError(ValueError):
    """模型名不在 provider 白名单内"""
    pass


def _validate_model(provider_name: str, model: str) -> None:
    """校验 model 是否在 provider 白名单; 不在则抛 ModelNotSupportedError"""
    allowed = SUPPORTED_MODELS.get(provider_name)
    if allowed is None:
        # 未知 provider, 不强制拦截, 交由上游报错
        return
    if model in allowed:
        return
    # 友好提示: 用 difflib 给一个最像的候选
    hint = ""
    try:
        import difflib
        matches = difflib.get_close_matches(model, allowed, n=1, cutoff=0.5)
        if matches:
            hint = f"  你是不是想用: {matches[0]}"
    except Exception:
        pass
    raise ModelNotSupportedError(
        f"Provider {provider_name!r} 不支持模型 {model!r}. "
        f"白名单: {allowed}.{hint}"
    )


# 已知不支持多模态的模型 (image_url content block 会被后端拒绝)
TEXT_ONLY_MODELS = {
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "gpt-4o-mini",
    "gpt-4o",
    "claude-sonnet-4-5",
    "claude-3-5-sonnet",
    "claude-3-haiku",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
}


def _strip_image_blocks(messages: list) -> tuple:
    """移除 messages 中所有非 text 类型的 content block.
    返回 (cleaned_messages, stripped_count).
    仅在当前 model 不支持多模态时调用.
    """
    if not messages:
        return messages, 0
    cleaned = []
    stripped = 0
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    else:
                        # image_url / image / audio 等
                        stripped += 1
                elif isinstance(block, str):
                    text_parts.append(block)
            new_msg = dict(msg)
            new_msg["content"] = "\n".join(p for p in text_parts if p)
            cleaned.append(new_msg)
        else:
            cleaned.append(msg)
    return cleaned, stripped


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

    # 模型名白名单校验: 避免向后端发不被接受的模型名
    _validate_model(provider_name, used_model)

    # 多模态防护: 已知 text-only 模型 → 移除 messages 中的 image_url 等 block
    if used_model in TEXT_ONLY_MODELS:
        messages, stripped = _strip_image_blocks(messages)
        if stripped:
            sys.stderr.write(
                f"[warning] model {used_model!r} 不支持图片, 已从历史消息中移除 {stripped} 个图片块\n"
            )

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
    """列出 provider 支持的模型(白名单来源: SUPPORTED_MODELS)"""
    return list(SUPPORTED_MODELS.get(provider_name, []))