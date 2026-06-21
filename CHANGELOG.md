# Changelog

所有 v0.x 版本的变更记录。日期格式 YYYY-MM-DD。

## v0.5.0 (2026-06-21) — Day 14 A 档

### ✨ 新增
- **`cost` 命令 + `cost.py` 模块** — token 成本估算
  - `codex-pp cost <model> <prompt_tokens> <completion_tokens>` 算 USD
  - `codex-pp cost --list` 列出所有已知 model + 价格
  - 内置 18 个 model 价格表 (OpenAI / Anthropic / Google / DeepSeek / MiniMax)
- 版本号: `__init__.py` 0.1.0 → 0.5.0, `cli.py` 0.4.0 → 0.5.0 (对齐)

### 🧪 测试
- 新增 `tests/test_cost.py` 6 个 unittest 全过
  - test_known_model: deepseek-chat 价格对算
  - test_zero_tokens: 0 token = 0 费用
  - test_unknown_model: 未知 model 返回 None
  - test_calculation_deepseek: deepseek-reasoner 价格
  - test_gpt4o: gpt-4o 价格
  - test_list_known_models: 价格表完整性

## v0.4.1 (2026-06-15)

- trending.py 修复 + A3 边界测试

## v0.4.0 (2026-06-14) — Day 1

- `snippet` 子命令 (list/add/show/delete/search)
- `history` 命令
- `completion` 命令 (生成 shell 补全脚本)

## v0.3.0 (2026-06-12)

- 国际化 zh/en
- config import/export

## v0.2.0 (2026-06-11)

- 演示模式 (`codex-pp demo`)
- PR 模板

## v0.1.0 (2026-06-11)

- 初版: 6 个 provider (Claude / GPT / Gemini / Llama / Mistral / Cohere)
- 9 个核心子命令 (chat / ask / models / config / stats / skill / memory / version / demo)
