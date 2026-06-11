"""
cli.py - 命令行界面
==================
中文化的 CLI 入口
"""

import sys
import argparse

from . import config, llm, skill, memory, i18n
from .ui import (
    cprint, print_banner, print_error, print_warning, print_success,
    print_info, print_table, format_tokens, format_latency
)

__version__ = "0.2.0"


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
                status = "✓" if pcfg.get("enabled") and pcfg.get("api_key") else "✗"
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

        try:
            result = llm.chat(
                provider_name=provider,
                messages=messages,
                model=model,
                stream=True,
            )
            messages.append({"role": "assistant", "content": result["content"]})
            memory.save_message(session_id, "assistant", result["content"])

            # 输出用量
            usage_line = (
                f"[{result['model']} | "
                f"输入 {format_tokens(result['input_tokens'])} | "
                f"输出 {format_tokens(result['output_tokens'])} | "
                f"耗时 {format_latency(result['latency'])}]"
            )
            print(cprint(usage_line, "dim"))
        except Exception as e:
            print_error(f"调用失败: {e}")


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
    try:
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
    except Exception as e:
        print_error(f"调用失败: {e}")
        return 1


def cmd_models(args):
    """列出可用模型"""
    cfg = config.load_config()
    print_info("可用 provider 和模型:")
    for pname, pcfg in cfg["providers"].items():
        status = "✓ 已配置" if pcfg.get("enabled") and pcfg.get("api_key") else "✗ 未配置"
        print(f"\n  [{pname}] {pcfg.get('name', pname)} - {status}")
        if args.verbose or pcfg.get("enabled"):
            print(f"    URL: {pcfg.get('base_url')}")
            models = llm.list_models_for_provider(pname)
            print(f"    默认模型: {pcfg.get('default_model')}")
            print(f"    可用模型 ({len(models)}):")
            for m in models:
                default = " ⭐ 默认" if m == pcfg.get("default_model") else ""
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
            enabled = "✓" if pcfg.get("enabled") else "✗"
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
    print("GitHub: https://github.com/fast118/codex-pp (待发布)")


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
                status = "✓ 已装" if s["installed"] else "  未装"
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


def cmd_demo(args):
    """演示模式: 展示所有功能"""
    print_banner()
    print()
    print(cprint("=" * 60, "cyan"))
    print(cprint(" codex-pp 功能演示", "cyan", bold=True))
    print(cprint("=" * 60, "cyan"))
    print()

    # 1. 配置
    print(cprint("① 配置管理", "magenta", bold=True))
    cfg = config.load_config()
    print(f"   默认 provider: {cfg['default_provider']}")
    enabled = [p for p, c in cfg['providers'].items() if c.get('enabled') and c.get('api_key')]
    print(f"   已配置: {', '.join(enabled) if enabled else '(无)'}")
    print()

    # 2. 模型
    print(cprint("② 多模型支持", "magenta", bold=True))
    print(f"   已集成 {len(cfg['providers'])} 个 provider:")
    for p, c in cfg['providers'].items():
        status = "✓" if c.get('enabled') and c.get('api_key') else "○"
        print(f"     {status} {p:15} {c.get('name', p)}")
    print()

    # 3. Skills
    print(cprint("③ Skill 系统(ai-agent-skills 集成)", "magenta", bold=True))
    skills = skill.list_skills()
    installed = [s['name'] for s in skills if s['installed']]
    print(f"   共有 {len(skills)} 个 skill,已装 {len(installed)} 个")
    for s in skills[:5]:
        marker = "✓" if s['installed'] else "○"
        print(f"     {marker} {s['name']:30} {s['desc']}")
    if len(skills) > 5:
        print(f"     ... 还有 {len(skills) - 5} 个")
    print()

    # 4. 持久化记忆
    print(cprint("④ 持久化记忆", "magenta", bold=True))
    stats = memory.get_stats()
    print(f"   消息数: {stats['messages']}")
    print(f"   记忆项: {stats['memories']}")
    print(f"   会话数: {stats['sessions']}")
    print()

    # 5. 用量统计
    print(cprint("⑤ 用量统计", "magenta", bold=True))
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