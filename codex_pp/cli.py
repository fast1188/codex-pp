"""
cli.py - 命令行界面
==================
中文化的 CLI 入口
"""

import sys
import argparse

# 兼容两种运行方式:
# - 作为包运行: `py -m codex_pp.cli` (相对 import)
# - 作为脚本运行: `codex++.exe` (PyInstaller onefile, 需要绝对 import)
try:
    from . import config, llm, skill, memory, extras, i18n, cost
    from .ui import (
        cprint, print_banner, print_error, print_warning, print_success,
        print_info, print_table, format_tokens, format_latency,
        Spinner, print_assistant_header,
    )
except ImportError:
    from codex_pp import config, llm, skill, memory, extras, i18n, cost
    from codex_pp.ui import (
        cprint, print_banner, print_error, print_warning, print_success,
        print_info, print_table, format_tokens, format_latency,
        Spinner, print_assistant_header,
    )

__version__ = "0.5.0"


def tr(key, **kwargs):
    """翻译快捷方式"""
    return i18n.t(key, **kwargs)


def cmd_chat(args):
    """进入对话模式"""
    cfg = config.load_config()
    provider = args.provider or cfg.get("default_provider", "skillai")
    provider_cfg = config.get_provider_config(cfg, provider)

    if not provider_cfg.get("enabled", False) or not provider_cfg.get("api_key"):
        print_error(f"Provider {provider} 未启用或未设置 key")
        print_info("先用 `codex-pp config set-key {provider} <your-key>` 设置")
        return 1

    model = args.model or provider_cfg.get("default_model")
    session_id = args.session or "default"

    # 加载历史记忆
    history = memory.get_conversation(session_id, limit=20)
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    # 加入系统提示:你之前对话
    if history:
        memory_summary = f"你之前跟用户有过 {len(history)} 轮对话。最近 3 轮:\n"
        for h in history[-6:]:
            role_cn = "用户" if h["role"] == "user" else "你"
            memory_summary += f"  {role_cn}: {h['content'][:80]}\n"
        messages.append({"role": "system", "content": memory_summary})

    print_banner()
    print_info(f"Provider: {provider} | Model: {model} | Session: {session_id}")
    print_info("输入 'quit' / 'exit' 退出, 'switch' 切模型, 'clear' 清空, 'memory' 查记忆")
    print()

    while True:
        try:
            user_input = input(cprint("\n你: ", "cyan", bold=True)).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            print_info("再见!")
            return 0

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("quit", "exit", "q"):
            print_info("再见!")
            return 0
        if cmd in ("clear", "reset"):
            memory.clear_conversation(session_id)
            messages = []
            print_info("对话历史已清空(数据库也清了)")
            continue
        if cmd in ("switch", "切换"):
            print_info("当前可用 providers:")
            for pname, pcfg in cfg["providers"].items():
                status = "[OK]" if pcfg.get("enabled") and pcfg.get("api_key") else "[X]"
                print(f"  {status} {pname}: {pcfg.get('name', pname)}")
            print_info("用法: codex-pp chat --provider <name>")
            continue
        if cmd in ("memory", "记忆"):
            stats = memory.get_stats()
            print_info(f"记忆统计: {stats['messages']} 条消息, {stats['memories']} 个记忆项, {stats['sessions']} 个会话")
            memories = memory.list_memories()
            for m in memories[:10]:
                v = m['value'][:60] + "..." if len(m['value']) > 60 else m['value']
                print(f"  [{m['key']}] = {v}")
            continue

        memory.save_message(session_id, "user", user_input)
        messages.append({"role": "user", "content": user_input})

        # 显示 spinner + 助手头
        print_assistant_header()
        try:
            with Spinner("思考中", color="cyan"):
                result = llm.chat(
                    provider_name=provider,
                    messages=messages,
                    model=model,
                    stream=True,
                )
            # spinner 退出后, 输出回车 + 空行分隔
            print()
            messages.append({"role": "assistant", "content": result["content"]})
            memory.save_message(session_id, "assistant", result["content"])

            # 输出用量
            usage_line = (
                f"  [{result['model']} | "
                f"输入 {format_tokens(result['input_tokens'])} | "
                f"输出 {format_tokens(result['output_tokens'])} | "
                f"耗时 {format_latency(result['latency'])}]"
            )
            print(cprint(usage_line, "dim"))
        except llm.ModelNotSupportedError as e:
            print_error(f"模型不支持: {e}")
            print_info(f"用 `codex-pp models -v` 查看该 provider 支持的模型列表")
        except Exception as e:
            print_error(f"调用失败: {e}")
            print_warning("如持续失败,检查 API key / 网络 / provider 配置")


def cmd_ask(args):
    """单次提问"""
    cfg = config.load_config()
    provider = args.provider or cfg.get("default_provider", "skillai")
    provider_cfg = config.get_provider_config(cfg, provider)

    if not provider_cfg.get("enabled", False) or not provider_cfg.get("api_key"):
        print_error(f"Provider {provider} 未启用或未设置 key")
        return 1

    question = " ".join(args.question)
    messages = [{"role": "user", "content": question}]
    print_assistant_header()
    try:
        with Spinner("思考中", color="cyan"):
            result = llm.chat(
                provider_name=provider,
                messages=messages,
                model=args.model,
                stream=True,
            )
        print()
        print()
        usage = result.get("usage", {})
        if usage:
            print(cprint(
                f"[输入 {format_tokens(usage.get('prompt_tokens', 0))} | "
                f"输出 {format_tokens(usage.get('completion_tokens', 0))} | "
                f"耗时 {format_latency(result.get('latency', 0))}]",
                "dim"
            ))
    except llm.ModelNotSupportedError as e:
        print_error(f"模型不支持: {e}")
        print_info(f"用 `codex-pp models -v` 查看该 provider 支持的模型列表")
        return 1
    except Exception as e:
        print_error(f"调用失败: {e}")
        return 1


def cmd_models(args):
    """列出可用模型"""
    cfg = config.load_config()
    print_info("可用 provider 和模型:")
    for pname, pcfg in cfg["providers"].items():
        status = "[OK] 已配置" if pcfg.get("enabled") and pcfg.get("api_key") else "[X] 未配置"
        print(f"\n  [{pname}] {pcfg.get('name', pname)} - {status}")
        if args.verbose or pcfg.get("enabled"):
            print(f"    URL: {pcfg.get('base_url')}")
            models = llm.list_models_for_provider(pname)
            print(f"    默认模型: {pcfg.get('default_model')}")
            print(f"    可用模型 ({len(models)}):")
            for m in models:
                default = " * 默认" if m == pcfg.get("default_model") else ""
                print(f"      - {m}{default}")


def cmd_config(args):
    """配置子命令"""
    if args.config_action == "set-key":
        if not args.provider or not args.key:
            print_error("用法: codex-pp config set-key <provider> <key>")
            return 1
        config.set_api_key(args.provider, args.key)
        print_success(f"已设置 {args.provider} 的 API key: {config.mask_key(args.key)}")
    elif args.config_action == "set-default":
        if not args.provider:
            print_error("用法: codex-pp config set-default <provider>")
            return 1
        try:
            config.set_default_provider(args.provider)
            print_success(f"默认 provider 已设为: {args.provider}")
        except ValueError as e:
            print_error(str(e))
    elif args.config_action == "enable":
        if not args.provider:
            print_error("用法: codex-pp config enable <provider>")
            return 1
        config.enable_provider(args.provider, True)
        print_success(f"已启用: {args.provider}")
    elif args.config_action == "disable":
        if not args.provider:
            print_error("用法: codex-pp config disable <provider>")
            return 1
        config.enable_provider(args.provider, False)
        print_success(f"已禁用: {args.provider}")
    elif args.config_action == "list":
        print_info("当前配置:")
        cfg = config.load_config()
        print(f"  默认 provider: {cfg['default_provider']}")
        print(f"  语言: {cfg['language']}")
        print()
        print("  Providers:")
        for pname, pcfg in cfg["providers"].items():
            enabled = "[OK]" if pcfg.get("enabled") else "[X]"
            key_status = "已配置" if pcfg.get("api_key") else "未配置"
            print(f"    [{enabled}] {pname}: {key_status}")
    elif args.config_action == "path":
        print(f"配置目录: {config.CONFIG_DIR}")
        print(f"配置文件: {config.CONFIG_FILE}")
    elif args.config_action == "lang":
        if not args.lang:
            print_error("用法: codex-pp config lang <zh|en>")
            return 1
        i18n.set_lang(args.lang)
        print_success(f"语言已切换: {args.lang}")
    elif args.config_action == "export":
        if not args.export_file:
            print_error("用法: codex-pp config export <file>")
            return 1
        try:
            import shutil
            shutil.copy(config.CONFIG_FILE, args.export_file)
            print_success(f"配置已导出到 {args.export_file}")
        except Exception as e:
            print_error(f"导出失败: {e}")
            return 1
    elif args.config_action == "import":
        if not args.import_file:
            print_error("用法: codex-pp config import <file>")
            return 1
        try:
            import shutil
            from pathlib import Path
            src = Path(args.import_file)
            if not src.exists():
                print_error(f"文件不存在: {src}")
                return 1
            shutil.copy(src, config.CONFIG_FILE)
            print_success(f"配置已从 {src} 导入")
        except Exception as e:
            print_error(f"导入失败: {e}")
            return 1
    else:
        print_error("用法: codex-pp config <set-key|set-default|enable|disable|list|path|lang|export|import>")
        return 1


def cmd_stats(args):
    """查看用量统计"""
    stats = config.get_usage_stats()
    print_info("用量统计:")
    print(f"  总请求: {stats['total_requests']}")
    print(f"  总输入 token: {format_tokens(stats['total_input_tokens'])}")
    print(f"  总输出 token: {format_tokens(stats['total_output_tokens'])}")
    total = stats['total_input_tokens'] + stats['total_output_tokens']
    print(f"  合计: {format_tokens(total)}")
    print()
    if stats.get("by_model"):
        print("  按模型:")
        for model, m in stats["by_model"].items():
            sub = m["input"] + m["output"]
            print(f"    {model}: {m['requests']} 次 / {format_tokens(sub)}")


def cmd_version(args):
    """显示版本"""
    print(f"codex-pp v{__version__}")
    print("国产化 AI 编程 CLI")
    print("License: MIT")
    print("GitHub: https://github.com/fast1188/codex-pp (待发布)")


def cmd_skill(args):
    """skill 子命令"""
    if args.skill_action == "list":
        skills = skill.list_skills()
        print_info(f"可用 skills ({len(skills)}):")
        by_cat = {}
        for s in skills:
            by_cat.setdefault(s["category"], []).append(s)
        for cat, items in by_cat.items():
            print(f"\n  [{cat}]")
            for s in items:
                status = "[OK] 已装" if s["installed"] else "  未装"
                print(f"    {status} {s['name']:30} {s['desc']}")
    elif args.skill_action == "install":
        if not args.name:
            print_error("用法: codex-pp skill install <name>")
            return 1
        if not skill.install_skill(args.name):
            return 1
    elif args.skill_action == "show":
        if not args.name:
            print_error("用法: codex-pp skill show <name>")
            return 1
        info = skill.show_skill(args.name)
        if not info:
            print_error(f"未找到: {args.name}")
            return 1
        print_info(f"Skill: {info['name']}")
        print(f"  分类: {info['category']}")
        print(f"  描述: {info['desc']}")
        print(f"  路径: {info['key']}")
        print(f"  已装: {'是' if info['installed'] else '否'}")
        if info.get("skill_md"):
            print(f"  文档: {info['skill_md']}")
    elif args.skill_action == "remove":
        if not args.name:
            print_error("用法: codex-pp skill remove <name>")
            return 1
        if not skill.remove_skill(args.name):
            return 1
    else:
        print_error("用法: codex-pp skill <list|install|show|remove>")
        return 1
    return 0


def cmd_cost(args):
    """v0.5.0: token 成本估算"""
    if args.list:
        rows = cost.list_known_models()
        print_info("已知 model 价格 (USD / 1M tokens):")
        print(f"  {'MODEL':<25} {'IN':<10} {'OUT':<10}")
        print(f"  {'-'*25} {'-'*10} {'-'*10}")
        for r in rows:
            print(f"  {r['model']:<25} ${r['in']:<9.3f} ${r['out']:<9.3f}")
        return 0

    if not args.model or args.prompt_tokens is None or args.completion_tokens is None:
        print_error("用法: codex-pp cost <model> <prompt_tokens> <completion_tokens>")
        print_info("  或: codex-pp cost --list")
        return 1

    r = cost.estimate(args.model, args.prompt_tokens, args.completion_tokens)
    if r is None:
        print_error(f"未知 model: {args.model}")
        print_info("用 'codex-pp cost --list' 看已知列表")
        return 1

    total_tokens = r['prompt_tokens'] + r['completion_tokens']
    print_success(f"Cost 估算 ({r['model']}):")
    print(f"  Tokens: in={r['prompt_tokens']:,}  out={r['completion_tokens']:,}  total={total_tokens:,}")
    print(f"  Price:  in=${r['input_price_per_m']}/M  out=${r['output_price_per_m']}/M")
    print(f"  Cost:   in=${r['cost_input']:.6f}  out=${r['cost_output']:.6f}")
    print(f"          TOTAL=${r['cost_total']:.6f}")
    return 0


def cmd_demo(args):
    """演示模式: 展示所有功能"""
    print_banner()
    print()
    print(cprint("=" * 60, "cyan"))
    print(cprint(" codex-pp 功能演示", "cyan", bold=True))
    print(cprint("=" * 60, "cyan"))
    print()

    # 1. 配置
    print(cprint("(1) 配置管理", "magenta", bold=True))
    cfg = config.load_config()
    print(f"   默认 provider: {cfg['default_provider']}")
    enabled = [p for p, c in cfg['providers'].items() if c.get('enabled') and c.get('api_key')]
    print(f"   已配置: {', '.join(enabled) if enabled else '(无)'}")
    print()

    # 2. 模型
    print(cprint("(2) 多模型支持", "magenta", bold=True))
    print(f"   已集成 {len(cfg['providers'])} 个 provider:")
    for p, c in cfg['providers'].items():
        status = "[OK]" if c.get('enabled') and c.get('api_key') else "[o]"
        print(f"     {status} {p:15} {c.get('name', p)}")
    print()

    # 3. Skills
    print(cprint("(3) Skill 系统(ai-agent-skills 集成)", "magenta", bold=True))
    skills = skill.list_skills()
    installed = [s['name'] for s in skills if s['installed']]
    print(f"   共有 {len(skills)} 个 skill,已装 {len(installed)} 个")
    for s in skills[:5]:
        marker = "[OK]" if s['installed'] else "[o]"
        print(f"     {marker} {s['name']:30} {s['desc']}")
    if len(skills) > 5:
        print(f"     ... 还有 {len(skills) - 5} 个")
    print()

    # 4. 持久化记忆
    print(cprint("(4) 持久化记忆", "magenta", bold=True))
    stats = memory.get_stats()
    print(f"   消息数: {stats['messages']}")
    print(f"   记忆项: {stats['memories']}")
    print(f"   会话数: {stats['sessions']}")
    print()

    # 5. 用量统计
    print(cprint("(5) 用量统计", "magenta", bold=True))
    usage = config.get_usage_stats()
    print(f"   总请求: {usage['total_requests']}")
    print(f"   总 token: {format_tokens(usage['total_input_tokens'] + usage['total_output_tokens'])}")
    if usage.get('by_model'):
        print("   按模型:")
        for model, m in list(usage['by_model'].items())[:3]:
            sub = m['input'] + m['output']
            print(f"     {model}: {m['requests']} 次 / {format_tokens(sub)}")
    print()

    print(cprint("=" * 60, "cyan"))
    print(cprint(" 演示完成! 立即开始: py codex-pp ask '你的问题'", "green", bold=True))
    print(cprint("=" * 60, "cyan"))


def cmd_memory(args):
    """memory 子命令"""
    if args.memory_action == "list":
        memories = memory.list_memories()
        if not memories:
            print_info("还没有任何记忆项")
            return 0
        print_info(f"记忆项 ({len(memories)}):")
        for m in memories:
            v = m['value']
            if isinstance(v, str) and len(v) > 80:
                v = v[:80] + "..."
            print(f"  [{m['key']}] = {v}")
    elif args.memory_action == "set":
        memory.set_memory(args.key, args.value)
        print_success(f"已设置: {args.key} = {args.value}")
    elif args.memory_action == "get":
        val = memory.get_memory(args.key)
        if val is None:
            print_warning(f"未找到: {args.key}")
        else:
            print(f"  [{args.key}] = {val}")
    elif args.memory_action == "delete":
        if memory.delete_memory(args.key):
            print_success(f"已删除: {args.key}")
        else:
            print_warning(f"未找到: {args.key}")
    else:
        print_error("用法: codex-pp memory <list|set|get|delete>")
        return 1
    return 0


def cmd_snippet(args):
    """snippet 子命令 (v0.4.0)"""
    if args.snippet_action == "list":
        snippets = extras.list_snippets(
            tag=getattr(args, "tag", None),
            language=getattr(args, "language", None),
            search=getattr(args, "search", None),
        )
        if not snippets:
            print_info("还没有任何代码片段")
            print_info("用 `codex-pp snippet add` 添加")
            return 0
        print_info(f"代码片段 ({len(snippets)}):")
        for s in snippets:
            tags_str = ",".join(s.get("tags", []))
            print(f"  [{s['id']}] {s['name']} ({s.get('language', 'python')}, {tags_str})")
    elif args.snippet_action == "show":
        s = extras.get_snippet(args.id)
        if not s:
            print_warning(f"未找到: {args.id}")
            return 1
        print(f"\n  # {s['name']}  ({s.get('language', 'python')})")
        print(f"  # tags: {','.join(s.get('tags', []))}")
        print(f"  # created: {s.get('created', '')}  used: {s.get('used', 0)}x")
        print(f"\n{s['content']}\n")
    elif args.snippet_action == "add":
        # 从文件读 content
        if hasattr(args, "file") and args.file:
            from pathlib import Path
            try:
                content = Path(args.file).read_text(encoding="utf-8")
            except Exception as e:
                print_error(f"读文件失败: {e}")
                return 1
        else:
            print_error("用法: codex-pp snippet add <name> --file <path> [--tags t1,t2] [--lang python]")
            return 1
        s = extras.add_snippet(
            name=args.name,
            content=content,
            tags=getattr(args, "tags", "") or "",
            language=getattr(args, "lang", "python"),
        )
        print_success(f"[OK] 已添加: [{s['id']}] {s['name']}")
    elif args.snippet_action == "delete":
        if extras.delete_snippet(args.id):
            print_success(f"[OK] 已删除: {args.id}")
        else:
            print_warning(f"未找到: {args.id}")
    elif args.snippet_action == "search":
        snippets = extras.list_snippets(search=args.query)
        if not snippets:
            print_info(f"未找到: {args.query}")
            return 0
        print_info(f"搜索结果 ({len(snippets)}):")
        for s in snippets:
            print(f"  [{s['id']}] {s['name']}")
    else:
        print_error("用法: codex-pp snippet <list|add|show|delete|search>")
        return 1
    return 0


def cmd_history(args):
    """history 子命令 (v0.4.0)"""
    if getattr(args, "clear", False):
        extras.clear_history()
        print_success("[OK] 历史已清空")
        return 0
    items = extras.get_history(
        limit=getattr(args, "limit", 20) or 20,
        provider=getattr(args, "provider", None),
        search=getattr(args, "search", None),
    )
    if not items:
        print_info("还没有历史")
        return 0
    print_info(f"最近 {len(items)} 条历史:")
    for h in items:
        cmd = h["command"]
        if len(cmd) > 60:
            cmd = cmd[:60] + "..."
        prov = f"[{h.get('provider', '')}/{h.get('model', '')}]" if h.get('provider') else ""
        print(f"  {h['ts_str']}  {prov}  {cmd}")
    return 0


def cmd_completion(args):
    """completion 子命令 (v0.4.0)"""
    shell = getattr(args, "shell", "bash")
    script = extras.get_completion_script(shell)
    print(script)
    print()
    print(f"# 添加到 ~/.{shell}rc:  eval \"$(codex-pp completion {shell})\"", file=__import__('sys').stderr)
    return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="codex-pp",
        description="国产化 AI 编程 CLI - 多模型 + 国内直连 + Skill 联动",
    )
    parser.add_argument("--version", action="store_true", help="显示版本")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # chat
    p_chat = subparsers.add_parser("chat", help="进入对话模式")
    p_chat.add_argument("--provider", help="provider 名称")
    p_chat.add_argument("--model", help="模型名")
    p_chat.add_argument("--system", help="系统提示")
    p_chat.add_argument("--session", help="会话 ID(用于记忆隔离)")
    p_chat.set_defaults(func=cmd_chat)

    # ask
    p_ask = subparsers.add_parser("ask", help="单次提问")
    p_ask.add_argument("question", nargs="+", help="问题")
    p_ask.add_argument("--provider", help="provider 名称")
    p_ask.add_argument("--model", help="模型名")
    p_ask.set_defaults(func=cmd_ask)

    # models
    p_models = subparsers.add_parser("models", help="列出可用模型")
    p_models.add_argument("-v", "--verbose", action="store_true", help="显示详情")
    p_models.set_defaults(func=cmd_models)

    # config
    p_config = subparsers.add_parser("config", help="配置")
    config_sub = p_config.add_subparsers(dest="config_action")
    c_setkey = config_sub.add_parser("set-key", help="设置 API key")
    c_setkey.add_argument("provider", help="provider 名称")
    c_setkey.add_argument("key", help="API key")
    c_setdef = config_sub.add_parser("set-default", help="设置默认 provider")
    c_setdef.add_argument("provider", help="provider 名称")
    c_enable = config_sub.add_parser("enable", help="启用 provider")
    c_enable.add_argument("provider", help="provider 名称")
    c_disable = config_sub.add_parser("disable", help="禁用 provider")
    c_disable.add_argument("provider", help="provider 名称")
    c_list = config_sub.add_parser("list", help="列出所有配置")
    c_path = config_sub.add_parser("path", help="显示配置路径")
    c_lang = config_sub.add_parser("lang", help="设置语言 (zh/en)")
    c_lang.add_argument("lang", nargs="?", help="zh 或 en")
    c_export = config_sub.add_parser("export", help="导出配置到文件")
    c_export.add_argument("export_file", nargs="?", help="目标文件路径")
    c_import = config_sub.add_parser("import", help="从文件导入配置")
    c_import.add_argument("import_file", nargs="?", help="源文件路径")
    p_config.set_defaults(func=cmd_config)

    # stats
    p_stats = subparsers.add_parser("stats", help="用量统计")
    p_stats.set_defaults(func=cmd_stats)

    # snippet (v0.4.0)
    p_snippet = subparsers.add_parser("snippet", help="管理代码片段(v0.4.0)")
    snippet_sub = p_snippet.add_subparsers(dest="snippet_action")
    s_list = snippet_sub.add_parser("list", help="列出所有片段")
    s_list.add_argument("--tag", help="按标签过滤")
    s_list.add_argument("--language", help="按语言过滤")
    s_list.add_argument("--search", help="按关键词搜索")
    s_add = snippet_sub.add_parser("add", help="添加片段")
    s_add.add_argument("name", help="片段名称")
    s_add.add_argument("--file", required=True, help="片段内容文件路径")
    s_add.add_argument("--tags", help="标签(逗号分隔)")
    s_add.add_argument("--lang", default="python", help="语言")
    s_show = snippet_sub.add_parser("show", help="显示片段")
    s_show.add_argument("id", type=int, help="片段 ID")
    s_del = snippet_sub.add_parser("delete", help="删除片段")
    s_del.add_argument("id", type=int, help="片段 ID")
    s_search = snippet_sub.add_parser("search", help="搜索片段")
    s_search.add_argument("query", help="搜索关键词")
    p_snippet.set_defaults(func=cmd_snippet)

    # history (v0.4.0)
    p_history = subparsers.add_parser("history", help="查看命令历史(v0.4.0)")
    p_history.add_argument("--limit", type=int, default=20, help="最多显示 N 条")
    p_history.add_argument("--provider", help="按 provider 过滤")
    p_history.add_argument("--search", help="按命令内容搜索")
    p_history.add_argument("--clear", action="store_true", help="清空历史")
    p_history.set_defaults(func=cmd_history)

    # completion (v0.4.0)
    p_completion = subparsers.add_parser("completion", help="生成 shell 补全脚本(v0.4.0)")
    p_completion.add_argument("shell", nargs="?", default="bash", choices=["bash", "zsh"], help="shell 类型")
    p_completion.set_defaults(func=cmd_completion)

    # version
    p_version = subparsers.add_parser("version", help="显示版本")
    p_version.set_defaults(func=cmd_version)

    # demo
    p_demo = subparsers.add_parser("demo", help="演示所有功能")
    p_demo.set_defaults(func=cmd_demo)

    # skill
    p_skill = subparsers.add_parser("skill", help="管理 skills")
    skill_sub = p_skill.add_subparsers(dest="skill_action")
    skill_sub.add_parser("list", help="列出可用 skills")
    c_install = skill_sub.add_parser("install", help="安装 skill")
    c_install.add_argument("name", help="skill 名")
    c_show = skill_sub.add_parser("show", help="显示 skill 详情")
    c_show.add_argument("name", help="skill 名")
    c_remove = skill_sub.add_parser("remove", help="删除 skill")
    c_remove.add_argument("name", help="skill 名")
    p_skill.set_defaults(func=cmd_skill)

    # memory
    p_memory = subparsers.add_parser("memory", help="管理持久化记忆")
    memory_sub = p_memory.add_subparsers(dest="memory_action")
    memory_sub.add_parser("list", help="列出所有记忆项")
    c_mset = memory_sub.add_parser("set", help="设置记忆项")
    c_mset.add_argument("key", help="记忆 key")
    c_mset.add_argument("value", help="记忆 value")
    c_mget = memory_sub.add_parser("get", help="获取记忆项")
    c_mget.add_argument("key", help="记忆 key")
    c_mdel = memory_sub.add_parser("delete", help="删除记忆项")
    c_mdel.add_argument("key", help="记忆 key")
    p_memory.set_defaults(func=cmd_memory)

    # v0.5.0: cost 估算
    p_cost = subparsers.add_parser("cost", help="token 成本估算 (v0.5.0)")
    p_cost.add_argument("model", nargs="?", help="模型名 (e.g. deepseek-chat)")
    p_cost.add_argument("prompt_tokens", nargs="?", type=int, help="输入 token 数")
    p_cost.add_argument("completion_tokens", nargs="?", type=int, help="输出 token 数")
    p_cost.add_argument("--list", action="store_true", help="列出所有已知 model 价格")
    p_cost.set_defaults(func=cmd_cost)

    args = parser.parse_args()

    if args.version:
        cmd_version(args)
        return 0

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())