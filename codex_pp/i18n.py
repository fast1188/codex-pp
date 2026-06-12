"""
i18n.py - 国际化
================
中英双语支持
"""

# 中文文案
ZH = {
    "version": "codex-pp v{version} - 国产化 AI 编程 CLI",
    "tagline": "差异化版本,解决中文用户痛点",
    "banner": """
+================================================+
|                                                |
|       codex-pp v{version} - 国产化 AI 编程 CLI    |
|                                                |
|  • 多模型支持                                  |
|  • 国内直连(api.skillai.top)                  |
|  • 兼容 ai-agent-skills 生态                   |
|  • 中文优先                                    |
|                                                |
+================================================+
""",
    "ready": "就绪",
    "error_no_provider": "Provider {provider} 未启用或未设置 key",
    "info_setup_key": "先用 `codex-pp config set-key {provider} <your-key>` 设置",
    "info_provider": "Provider: {provider} | Model: {model} | Session: {session}",
    "info_commands": "输入 'quit' / 'exit' 退出, 'switch' 切模型, 'clear' 清空, 'memory' 查记忆",
    "ask_usage": "用法: codex-pp ask <问题>",
    "ask_usage_provider": "用法: codex-pp ask [--provider <name>] <问题>",
    "config_list_title": "当前配置:",
    "config_default": "默认 provider: {provider}",
    "config_lang": "语言: {lang}",
    "config_providers": "Providers:",
    "config_enabled": "[OK]",
    "config_disabled": "[X]",
    "config_set": "已设置: {provider} 的 API key: {key}",
    "config_set_default": "默认 provider 已设为: {provider}",
    "config_set_key_usage": "用法: codex-pp config set-key <provider> <key>",
    "config_set_default_usage": "用法: codex-pp config set-default <provider>",
    "config_enable_usage": "用法: codex-pp config enable <provider>",
    "config_disable_usage": "用法: codex-pp config disable <provider>",
    "config_path": "配置目录: {path}",
    "config_file": "配置文件: {file}",
    "stats_title": "用量统计:",
    "stats_total_requests": "总请求: {n}",
    "stats_input_tokens": "总输入 token: {n}",
    "stats_output_tokens": "总输出 token: {n}",
    "stats_total": "合计: {n}",
    "stats_by_model": "按模型:",
    "skill_list_title": "可用 skills ({n}):",
    "skill_installed": "[OK] 已装",
    "skill_not_installed": "未装",
    "skill_installed_msg": "[OK] 已安装: {name}",
    "skill_install_path": "路径: {path}",
    "skill_install_desc": "描述: {desc}",
    "skill_install_hint": "提示: 跑 {path}/install.bat 完成安装",
    "skill_show_title": "Skill: {name}",
    "skill_show_category": "分类: {category}",
    "skill_show_desc": "描述: {desc}",
    "skill_show_path": "路径: {path}",
    "skill_show_installed": "已装: {status}",
    "skill_show_doc": "文档: {path}",
    "skill_not_found": "未找到: {name}",
    "skill_unknown": "未知 skill: {name}",
    "skill_list_hint": "用 `codex-pp skill list` 查看可用 skills",
    "skill_removed": "[OK] 已删除: {name}",
    "skill_not_installed_short": "未安装: {name}",
    "skill_cmd_usage": "用法: codex-pp skill <list|install|show|remove>",
    "memory_list_title": "记忆项 ({n}):",
    "memory_empty": "还没有任何记忆项",
    "memory_set": "已设置: {key} = {value}",
    "memory_not_found": "未找到: {key}",
    "memory_cmd_usage": "用法: codex-pp memory <list|set|get|delete>",
    "config_import_success": "[OK] 配置已从 {file} 导入",
    "config_export_success": "[OK] 配置已导出到 {file}",
    "config_import_usage": "用法: codex-pp config import <file>",
    "config_export_usage": "用法: codex-pp config export <file>",
    "demo_complete": " 演示完成! 立即开始: py codex-pp ask '你的问题'",
    "section_config": "(1) 配置管理",
    "section_models": "(2) 多模型支持",
    "section_skills": "(3) Skill 系统(ai-agent-skills 集成)",
    "section_memory": "(4) 持久化记忆",
    "section_stats": "(5) 用量统计",
    "lang_switched": "语言已切换: {lang}",
    "info_no_key_warning": "未配置 key 的 provider 不会显示",
}

# 英文文案
EN = {
    "version": "codex-pp v{version} - Localized AI coding CLI",
    "tagline": "Differentiated version for Chinese developer needs",
    "banner": """
+================================================+
|                                                |
|       codex-pp v{version} - Localized AI CLI    |
|                                                |
|  • Multi-model support                         |
|  • CN relay (api.skillai.top)                  |
|  • ai-agent-skills ecosystem                    |
|  • Chinese-first                               |
|                                                |
+================================================+
""",
    "ready": "Ready",
    "error_no_provider": "Provider {provider} not enabled or key not set",
    "info_setup_key": "Run `codex-pp config set-key {provider} <your-key>` first",
    "info_provider": "Provider: {provider} | Model: {model} | Session: {session}",
    "info_commands": "Type 'quit' / 'exit' to leave, 'switch' to change model, 'clear' to reset, 'memory' to view",
    "ask_usage": "Usage: codex-pp ask <question>",
    "ask_usage_provider": "Usage: codex-pp ask [--provider <name>] <question>",
    "config_list_title": "Current config:",
    "config_default": "Default provider: {provider}",
    "config_lang": "Language: {lang}",
    "config_providers": "Providers:",
    "config_enabled": "[OK]",
    "config_disabled": "[X]",
    "config_set": "Set: {provider} API key: {key}",
    "config_set_default": "Default provider: {provider}",
    "config_set_key_usage": "Usage: codex-pp config set-key <provider> <key>",
    "config_set_default_usage": "Usage: codex-pp config set-default <provider>",
    "config_enable_usage": "Usage: codex-pp config enable <provider>",
    "config_disable_usage": "Usage: codex-pp config disable <provider>",
    "config_path": "Config dir: {path}",
    "config_file": "Config file: {file}",
    "stats_title": "Usage stats:",
    "stats_total_requests": "Total requests: {n}",
    "stats_input_tokens": "Total input tokens: {n}",
    "stats_output_tokens": "Total output tokens: {n}",
    "stats_total": "Total: {n}",
    "stats_by_model": "By model:",
    "skill_list_title": "Available skills ({n}):",
    "skill_installed": "[OK] installed",
    "skill_not_installed": "not installed",
    "skill_installed_msg": "[OK] Installed: {name}",
    "skill_install_path": "Path: {path}",
    "skill_install_desc": "Description: {desc}",
    "skill_install_hint": "Hint: run {path}/install.bat to complete setup",
    "skill_show_title": "Skill: {name}",
    "skill_show_category": "Category: {category}",
    "skill_show_desc": "Description: {desc}",
    "skill_show_path": "Path: {path}",
    "skill_show_installed": "Installed: {status}",
    "skill_show_doc": "Doc: {path}",
    "skill_not_found": "Not found: {name}",
    "skill_unknown": "Unknown skill: {name}",
    "skill_list_hint": "Run `codex-pp skill list` to see available skills",
    "skill_removed": "[OK] Removed: {name}",
    "skill_not_installed_short": "Not installed: {name}",
    "skill_cmd_usage": "Usage: codex-pp skill <list|install|show|remove>",
    "memory_list_title": "Memory items ({n}):",
    "memory_empty": "No memory items yet",
    "memory_set": "Set: {key} = {value}",
    "memory_not_found": "Not found: {key}",
    "memory_cmd_usage": "Usage: codex-pp memory <list|set|get|delete>",
    "config_import_success": "[OK] Config imported from {file}",
    "config_export_success": "[OK] Config exported to {file}",
    "config_import_usage": "Usage: codex-pp config import <file>",
    "config_export_usage": "Usage: codex-pp config export <file>",
    "demo_complete": " Demo complete! Start now: py codex-pp ask 'your question'",
    "section_config": "(1) Configuration",
    "section_models": "(2) Multi-model support",
    "section_skills": "(3) Skills system (ai-agent-skills integration)",
    "section_memory": "(4) Persistent memory",
    "section_stats": "(5) Usage statistics",
    "lang_switched": "Language switched: {lang}",
    "info_no_key_warning": "Providers without keys are not shown",
}


_CURRENT_LANG = "zh"  # 默认中文


def set_lang(lang: str):
    """设置语言:zh / en"""
    global _CURRENT_LANG
    if lang in ("zh", "en"):
        _CURRENT_LANG = lang


def t(key: str, **kwargs) -> str:
    """获取翻译(支持占位符)"""
    lang_dict = ZH if _CURRENT_LANG == "zh" else EN
    template = lang_dict.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


def get_lang() -> str:
    """获取当前语言"""
    return _CURRENT_LANG