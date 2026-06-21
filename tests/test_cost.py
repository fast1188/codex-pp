"""test_cost.py - cost v0.5.0 单元测试
跑法: python -X utf8 -m unittest test_cost -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from codex_pp import cost  # noqa


class TestEstimate(unittest.TestCase):

    def test_known_model(self):
        """deepseek-chat 已知价格"""
        r = cost.estimate("deepseek-chat", 1000, 500)
        self.assertIsNotNone(r)
        self.assertEqual(r["model"], "deepseek-chat")
        # 1000/1e6 * 0.14 + 500/1e6 * 0.28 = 0.00014 + 0.00014 = 0.00028
        self.assertAlmostEqual(r["cost_total"], 0.00028, places=7)

    def test_zero_tokens(self):
        """0 token = 0 费用"""
        r = cost.estimate("gpt-4o-mini", 0, 0)
        self.assertEqual(r["cost_total"], 0)

    def test_unknown_model(self):
        """未知 model 返回 None"""
        r = cost.estimate("totally-fake-model", 100, 100)
        self.assertIsNone(r)

    def test_calculation_deepseek(self):
        """deepseek-reasoner 1000+500 tokens"""
        r = cost.estimate("deepseek-reasoner", 1000, 500)
        # 1000/1e6 * 0.55 + 500/1e6 * 2.19 = 0.00055 + 0.001095 = 0.001645
        self.assertAlmostEqual(r["cost_total"], 0.001645, places=7)
        # 输出比输入贵
        self.assertGreater(r["cost_output"], r["cost_input"])

    def test_gpt4o(self):
        """gpt-4o 100 in + 100 out"""
        r = cost.estimate("gpt-4o", 100, 100)
        # 100/1e6 * 2.5 + 100/1e6 * 10 = 0.00125
        self.assertAlmostEqual(r["cost_total"], 0.00125, places=7)


class TestList(unittest.TestCase):

    def test_list_known_models(self):
        models = cost.list_known_models()
        self.assertGreater(len(models), 5)
        # 至少包含 deepseek-chat
        names = [m["model"] for m in models]
        self.assertIn("deepseek-chat", names)
        # 每条都有 in/out
        for m in models:
            self.assertIn("in", m)
            self.assertIn("out", m)
            self.assertGreater(m["in"], 0)
            self.assertGreater(m["out"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
