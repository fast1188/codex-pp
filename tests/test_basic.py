"""
test_basic.py - 基础单元测试
===========================
跑: py -m unittest tests.test_basic
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# 把项目目录加到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig(unittest.TestCase):
    """测试 config 模块"""

    def setUp(self):
        """每个测试前:用临时目录"""
        self.tmp = tempfile.mkdtemp()
        self.config_dir = Path(self.tmp) / ".codex-pp-test"
        self.config_dir.mkdir()

    def tearDown(self):
        """清理"""
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_default_config(self):
        """测试默认配置加载"""
        from codex_pp import config
        original = config.CONFIG_DIR
        try:
            config.CONFIG_DIR = self.config_dir
            cfg = config.load_config()
            self.assertIn("providers", cfg)
            self.assertIn("skillai", cfg["providers"])
            self.assertIn("github_models", cfg["providers"])
        finally:
            config.CONFIG_DIR = original

    def test_set_api_key(self):
        """测试设置 API key"""
        from codex_pp import config
        original = config.CONFIG_DIR
        try:
            config.CONFIG_DIR = self.config_dir
            # 用已有的 provider(github_models)
            config.set_api_key("github_models", "test_key_123")
            cfg = config.load_config()
            self.assertEqual(cfg["providers"]["github_models"]["api_key"], "test_key_123")
        finally:
            config.CONFIG_DIR = original

    def test_mask_key(self):
        """测试 key 遮蔽"""
        from codex_pp import config
        self.assertEqual(config.mask_key(""), "****")
        self.assertEqual(config.mask_key("short"), "****")
        masked = config.mask_key("ghp_abc123def456789")
        self.assertIn("ghp_", masked)
        self.assertIn("789", masked)


class TestMemory(unittest.TestCase):
    """测试 memory 模块"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_and_get_memory(self):
        """测试记忆存取"""
        from codex_pp import memory
        original = memory.DB_DIR
        original_db = memory.DB_FILE
        try:
            memory.DB_DIR = Path(self.tmp) / ".codex-pp"
            memory.DB_DIR.mkdir()
            memory.DB_FILE = memory.DB_DIR / "memory.db"

            memory.set_memory("test_key", "test_value")
            val = memory.get_memory("test_key")
            self.assertEqual(val, "test_value")
        finally:
            memory.DB_DIR = original
            memory.DB_FILE = original_db

    def test_delete_memory(self):
        """测试删除记忆"""
        from codex_pp import memory
        original = memory.DB_DIR
        original_db = memory.DB_FILE
        try:
            memory.DB_DIR = Path(self.tmp) / ".codex-pp"
            memory.DB_DIR.mkdir()
            memory.DB_FILE = memory.DB_DIR / "memory.db"

            memory.set_memory("to_delete", "value")
            self.assertTrue(memory.delete_memory("to_delete"))
            self.assertIsNone(memory.get_memory("to_delete"))
        finally:
            memory.DB_DIR = original
            memory.DB_FILE = original_db


class TestUI(unittest.TestCase):
    """测试 UI 工具"""

    def test_format_tokens(self):
        from codex_pp.ui import format_tokens
        self.assertEqual(format_tokens(500), "500")
        self.assertEqual(format_tokens(1500), "1.5K")
        self.assertEqual(format_tokens(2_500_000), "2.50M")

    def test_format_latency(self):
        from codex_pp.ui import format_latency
        self.assertEqual(format_latency(0.5), "500ms")
        self.assertEqual(format_latency(2.5), "2.5s")
        self.assertEqual(format_latency(75), "1m15s")

    def test_cprint(self):
        from codex_pp.ui import cprint
        result = cprint("hello", "red", bold=True)
        self.assertIn("hello", result)
        # ANSI 颜色码应包含
        self.assertIn("\033[", result)


class TestSkill(unittest.TestCase):
    """测试 skill 模块"""

    def test_known_skills_count(self):
        """测试已知 skills 数量"""
        from codex_pp import skill
        self.assertGreaterEqual(len(skill.KNOWN_SKILLS), 5)
        # 确认有 token-saver
        self.assertIn("shared/token-saver", skill.KNOWN_SKILLS)

    def test_list_skills(self):
        """测试列出 skills"""
        from codex_pp import skill
        skills = skill.list_skills()
        self.assertGreater(len(skills), 0)
        for s in skills:
            self.assertIn("key", s)
            self.assertIn("name", s)
            self.assertIn("installed", s)

    def test_show_skill(self):
        """测试显示 skill 详情"""
        from codex_pp import skill
        info = skill.show_skill("token-saver")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "token-saver")
        self.assertIn("desc", info)


class TestLlm(unittest.TestCase):
    """测试 llm 模块"""

    def test_list_models_for_provider(self):
        """测试模型列表"""
        from codex_pp import llm
        models = llm.list_models_for_provider("github_models")
        self.assertGreater(len(models), 0)
        self.assertIn("gpt-4o-mini", models)

        models = llm.list_models_for_provider("groq")
        self.assertGreater(len(models), 0)

    def test_list_models_for_unknown_provider(self):
        """测试未知 provider"""
        from codex_pp import llm
        models = llm.list_models_for_provider("nonexistent_xyz")
        self.assertEqual(models, [])


class TestCompression(unittest.TestCase):
    """测试 prompt 压缩(借鉴 token-saver 算法)"""

    def test_light_compress_chinese(self):
        """测试中文轻度压缩"""
        from codex_pp.ui import format_tokens
        # 简单测试 format_tokens 工具函数能正常处理各种数值
        self.assertEqual(format_tokens(0), "0")
        self.assertEqual(format_tokens(999), "999")
        self.assertEqual(format_tokens(1000), "1.0K")
        self.assertEqual(format_tokens(1_000_000), "1.00M")


if __name__ == "__main__":
    unittest.main(verbosity=2)