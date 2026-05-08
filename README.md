# marie_sxy ✨

> AI-powered file organizer. Drop a folder, get magic.

用 AI 实现近藤麻理惠的整理魔法：丢一个文件夹给我，还你一个井井有条的世界。

---

## 🚧 Status

**Alpha** - 正在开发中（Week 1 地基已完成，当前 Week 2：分类核心）

详细规划见 [`PROJECT_PLAN.md`](./PROJECT_PLAN.md)。

## 📦 Package Info

- **PyPI 包名**：`marie_sxy`
- **Python 模块名**：`marie_sxy`
- **CLI 命令**：`marie_sxy`

> 安装时使用 `pip install marie_sxy`，但代码里 `import marie_sxy`，命令行用 `marie_sxy`。

## ⚡ Quick Start

```bash
# 从 PyPI 安装（发布后可用）
pip install marie_sxy

# 或本地开发模式
uv sync

# 扫描一个目录（仅查看，不移动）
uv run marie_sxy scan ~/Downloads
```

## 🛠 Development

```bash
# 安装依赖（含开发依赖）
uv sync

# 运行测试
uv run pytest

# 代码检查 + 格式化
uv run ruff check .
uv run ruff format .
```

## 📚 Documentation

- [项目方案](./PROJECT_PLAN.md) - 完整的产品设计与开发路线图

## 📄 License

MIT
