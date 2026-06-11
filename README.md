# codex-pp

> 国产化 AI 编程 CLI - 多模型 + 国内直连 + Skill 联动
>
> 差异化版本(不抄 OpenAI Codex CLI),解决中文用户痛点

[![MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

---

## 这是什么?

`codex-pp` 是一个**国产化**的 AI 编程 CLI,差异化点:

| 特性 | 官方 Codex CLI | codex-pp |
|------|----------------|----------|
| 多模型 | ❌(只 OpenAI)| ✓ Claude / GPT / Gemini / Llama |
| 国内直连 | ❌ | ✓ |
| Skill 系统 | ❌ | ✓ 兼容 ai-agent-skills |
| 持久化记忆 | ❌ | ✓ SQLite 跨会话 |
| 中文 UI | 部分 | ✓ 优先 |
| 用量统计 | ❌ | ✓ |

## 5 分钟上手

```bash
pip install -e .

# 设置 API key(任选一个)
codex-pp config set-key github_models "ghp_xxx"
codex-pp config set-key groq "gsk_xxx"
codex-pp config set-key skillai "sk-xxx"

# 设置默认
codex-pp config set-default github_models

# 开聊
codex-pp ask "用Python写个快排"
codex-pp chat
```

## 命令速查

| 命令 | 功能 |
|------|------|
| `codex-pp ask "问题"` | 单次提问 |
| `codex-pp chat` | 进入对话模式 |
| `codex-pp models` | 列出所有可用模型 |
| `codex-pp config set-key <provider> <key>` | 设置 API key |
| `codex-pp config set-default <provider>` | 改默认 provider |
| `codex-pp config list` | 查看配置 |
| `codex-pp stats` | 用量统计 |
| `codex-pp skill list` | 列出 11 个 skills |
| `codex-pp skill install <name>` | 安装 skill |
| `codex-pp memory list` | 持久化记忆 |
| `codex-pp memory set <key> <val>` | 存记忆项 |

## 支持的 Provider

| Provider | 免费 | 国内直连 | 速度 |
|----------|------|----------|------|
| `github_models` | ✓ | ✗ | 中 |
| `groq` | ✓ | ✗ | **极快** |
| `gemini` | ✓ | ✗ | 快 |
| `skillai` | ✗ (付费便宜) | ✓ | 快 |
| `openai` | ✗ | ✗ | 中 |
| `anthropic` | ✗ | ✗ | 中 |

## Skill 联动

```bash
# 列 11 个可用 skills
codex-pp skill list

# 装一个
codex-pp skill install token-saver

# 装到 ~/.codex-pp/skills/
```

完整 skill 库: [ai-agent-skills](https://github.com/fast118/ai-agent-skills)

## 持久化记忆

`codex-pp` 自动保存对话历史到 SQLite,跨会话保持:

```bash
# 查记忆
codex-pp memory list

# 设一个跨会话偏好
codex-pp memory set "user_name" "fast118"

# 启动新会话时自动加载上下文
codex-pp chat --session my-project
```

数据存:`~/.codex-pp/memory.db`

## 国内直连(可选)

撞墙或想省钱,可以配 [api.skillai.top](https://api.skillai.top):

```bash
codex-pp config set-key skillai "sk-你的key"
codex-pp config set-default skillai
```

## 架构

```
~/.codex-pp/
├── config.json      # provider + key 配置
├── memory.db        # 持久化记忆(SQLite)
├── skills/          # 装好的 skills
│ ├── token-saver/
│ ├── api-fallback/
│ └── ...
└── ai-agent-skills/ # 仓库 clone(本地)
```

## 测试情况

| 轮 | 测什么 | 状态 |
|----|--------|------|
| R1 | 多模型切换 | ✓(github_models + groq 通过)|
| R2 | 国内直连 | ✓ 端点发现 + 修复 URL |
| R3 | Skill 集成 | ✓(11 个 skills 可装)|
| R4 | 持久化记忆 | ✓(SQLite 工作)|
| R5 | 中文 UI + 用量统计 | ✓ |

## License

MIT

## 相关项目

- [ai-agent-skills](https://github.com/fast118/ai-agent-skills) - 11 个跨工具 skills
- [free-ai-router](https://github.com/fast118/free-ai-router) - 另一个 AI 工具
- [api.skillai.top](https://api.skillai.top) - 国内直连 API