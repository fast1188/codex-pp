"""cost.py - token 成本估算 v0.1 (v0.5.0 新增)

用法:
    py -m codex_pp.cost <model> <prompt_tokens> <completion_tokens>
    # 或从 cli: codex-pp cost deepseek-chat 1000 500

价格数据 (单位: USD / 1M tokens, 2026-06-21):
- 来源: 各 provider 官方公开价格
- 大致参考, 实际按账号计费
"""
import sys
from typing import Optional

# 价格表 (USD per 1M tokens): (in, out)
PRICING = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "o1-mini": (3.00, 12.00),
    # Anthropic
    "claude-sonnet-4": (3.00, 15.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
    # Google
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    # DeepSeek
    "deepseek-chat": (0.14, 0.28),
    "deepseek-reasoner": (0.55, 2.19),
    # MiniMax (包月, 单价仅供参考)
    "MiniMax-M3": (1.0, 3.0),
    "MiniMax-M2.7": (0.8, 2.4),
    "MiniMax-M2.7-highspeed": (0.8, 2.4),
}


def estimate(model: str, prompt_tokens: int, completion_tokens: int) -> Optional[dict]:
    """算给定 model + tokens 的 USD 费用

    返回 None 如果 model 不在价格表里
    """
    pricing = PRICING.get(model)
    if not pricing:
        return None
    in_price, out_price = pricing
    cost_in = (prompt_tokens / 1_000_000) * in_price
    cost_out = (completion_tokens / 1_000_000) * out_price
    total = cost_in + cost_out
    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "input_price_per_m": in_price,
        "output_price_per_m": out_price,
        "cost_input": cost_in,
        "cost_output": cost_out,
        "cost_total": total,
    }


def list_known_models() -> list:
    """返回所有已知 model + 价格"""
    return [
        {"model": m, "in": p[0], "out": p[1]}
        for m, p in PRICING.items()
    ]


def main():
    """CLI 入口 (codex-pp cost)"""
    if len(sys.argv) < 4:
        print("用法: codex-pp cost <model> <prompt_tokens> <completion_tokens>")
        print("      codex-pp cost --list   列出所有已知 model 价格")
        print()
        print("例: codex-pp cost deepseek-chat 1000 500")
        sys.exit(1)

    if sys.argv[1] == "--list":
        print(f"{'MODEL':<25} {'IN $/M':<10} {'OUT $/M':<10}")
        print("-" * 50)
        for m in PRICING:
            in_p, out_p = PRICING[m]
            print(f"{m:<25} ${in_p:<9.3f} ${out_p:<9.3f}")
        sys.exit(0)

    model = sys.argv[1]
    try:
        pt = int(sys.argv[2])
        ct = int(sys.argv[3])
    except ValueError:
        print(f"✗ tokens 必须是数字, 得到: {sys.argv[2]} / {sys.argv[3]}")
        sys.exit(1)

    r = estimate(model, pt, ct)
    if r is None:
        print(f"✗ 未知 model: {model}")
        print(f"  用 'codex-pp cost --list' 查看已知 model")
        sys.exit(1)

    print(f"Model: {r['model']}")
    print(f"Tokens: in={r['prompt_tokens']}  out={r['completion_tokens']}  total={r['prompt_tokens']+r['completion_tokens']}")
    print(f"Price:  in=${r['input_price_per_m']}/M  out=${r['output_price_per_m']}/M")
    print(f"Cost:   in=${r['cost_input']:.6f}  out=${r['cost_output']:.6f}")
    print(f"        TOTAL=${r['cost_total']:.6f}")


if __name__ == "__main__":
    main()
