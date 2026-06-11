"""
setup.py - 打包用
"""
from setuptools import setup, find_packages

setup(
    name="codex-pp",
    version="0.1.0",
    description="国产化 AI 编程 CLI - 多模型 + 国内直连 + Skill 联动",
    author="fast118 / wudijia2026",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "codex-pp=codex_pp.cli:main",
        ],
    },
)
