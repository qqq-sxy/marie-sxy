# marie_sxy ✨

> AI-powered file organizer. Drop a folder, get magic.

用 AI 实现近藤麻理惠的整理魔法：丢一个文件夹给我，还你一个井井有条的世界。

---

## 🚧 Status

**Alpha** - 正在开发中（Week 2 分类核心已完成，当前 Week 3：内容理解）

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

# 按文件名做 AI/离线分类预览（默认 dry-run，不移动文件）
# 需配置 LLM API（见 LiteLLM）；无密钥时可: export MARIE_SXY_OFFLINE=1
uv run marie_sxy organize ~/Downloads --dry-run
```

### API Key（本地文件，不会进 Git）

1. 复制仓库里的 [`.env.example`](./.env.example) 为 **`.env`**（与 `pyproject.toml` 同级即可）。
2. **推荐一套变量走天下**：只填 **`MARIE_SXY_API_KEY`** 和 **`MARIE_SXY_MODEL`**。程序会根据模型名自动把密钥写到 LiteLLM 需要的厂商变量里（例如 `gpt-4o-mini` → `OPENAI_API_KEY`，`deepseek/deepseek-chat` → `DEEPSEEK_API_KEY`）。换厂商时一般只需改这两条。
3. 若不想用统一变量，仍可照旧分别设置 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY` 等（且不设 `MARIE_SXY_API_KEY`）。
4. **`.env` 已在 `.gitignore` 中**，`git push` 不会带上远程。

可选：用环境变量 **`MARIE_SXY_ENV_FILE=/绝对路径/自定义.env`** 指定任意密钥文件（同样请勿提交该文件）。

用户级兜底（不配项目 `.env` 时）：可把密钥放在 `~/.config/marie_sxy/.env`（尊重 `XDG_CONFIG_HOME`）。

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
