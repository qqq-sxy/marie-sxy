# Marie - AI 文件智能整理工具

> 用 AI 实现近藤麻理惠的整理魔法：丢一个文件夹给我，还你一个井井有条的世界。

---

## 目录

- [一、产品定位](#一产品定位)
- [二、核心卖点](#二核心卖点差异化)
- [三、MVP 功能清单](#三mvp-功能清单v01)
- [四、技术架构](#四技术架构)
- [五、项目结构](#五项目结构)
- [六、6 周开发路线图](#六6-周开发路线图每周-15-20-小时)
- [七、Prompt 设计](#七prompt-设计核心难点)
- [八、需要避开的坑](#八需要避开的坑)
- [九、README 必备元素](#九readme-必备元素决定-80-的-star)
- [十、传播策略](#十传播策略拿-star-关键)
- [立刻可以做的事](#立刻可以做的事)

---

## 一、产品定位

### 一句话定义

> **看一眼你的"下载"文件夹，AI 帮你自动整理成有条理的目录结构。**

### 名字候选

| 名字 | 含义 | 适合度 |
|------|------|--------|
| `tidyai` | tidy + ai，简洁好记 | ⭐⭐⭐⭐⭐ |
| `organize-ai` | 直白 | ⭐⭐⭐⭐ |
| `folderly` | folder + 友好后缀 | ⭐⭐⭐ |
| `marie` | 致敬"近藤麻理惠"（怦然心动整理法） | ⭐⭐⭐⭐⭐ 但 PyPI 已被占用 |
| `cleansweep` | 大扫除 | ⭐⭐⭐ |

> **最终选择**：
> - **PyPI 包名**：`marie-sxy`（因为 `marie` 在 PyPI 已被占用，加作者后缀区分）
> - **Python 模块名**：`marie`（保留短名，便于 `import marie` 使用）
> - **CLI 命令**：`marie`（保留短名，方便用户输入）
>
> 这种"PyPI 名带后缀、import 名保持短名"的做法在社区很常见，例如 `pillow`/`PIL`、`beautifulsoup4`/`bs4`、`python-dotenv`/`dotenv`。

### Slogan

> **"Drop a folder. Get a magic tidy."**
>
> 中文："丢一个文件夹给我，还你一个井井有条的世界。"

---

## 二、核心卖点（差异化）

跟现有工具（`organize`、`hazel`、`maid`）对比，Marie 的杀手锏：

| 特性 | 传统工具 | Marie |
|------|---------|-------|
| 整理依据 | **文件名 / 后缀** 规则 | **AI 看文件内容** |
| 配置成本 | 要写规则 / YAML | **零配置，开箱即用** |
| 智能程度 | 死板 | 能识别"发票"、"简历"、"截图" |
| 学习能力 | 无 | **能学习用户整理偏好** |
| 安全性 | 直接移动 | **Dry-run 预览 + 一键回滚** |

**核心创新点**：

1. **AI 看内容**：PDF 知道是发票还是论文，图片知道是截图还是表情包
2. **可回滚**：每次整理都有 undo 历史
3. **先预览后执行**：默认 dry-run，避免误操作
4. **学习用户习惯**：记住用户拒绝过的整理建议

---

## 三、MVP 功能清单（v0.1）

### 必做（Week 1-3）

```text
[CLI] marie ~/Downloads
  → 扫描所有文件
  → AI 分析（按类型 + 内容）
  → 生成整理建议（控制台展示树形结构）
  → 用户确认 → 执行移动

[默认分类]
  📁 图片
    ├── 截图
    ├── 表情包
    └── 照片
  📁 文档
    ├── 发票
    ├── 简历
    ├── 合同
    └── 论文
  📁 代码
    ├── Python
    └── 前端
  📁 安装包
  📁 压缩包
  📁 视频
  📁 音频
  📁 其他
```

### 加分项（Week 4-5）

- `--dry-run` 模式（默认开启）
- `--undo` 回滚上次整理
- `--rules custom.yaml` 自定义规则
- 处理重名文件（自动加后缀）
- 进度条（用 `rich`）

### v0.2 之后

- TUI 界面（用 `Textual`，前端思维友好）
- Web GUI（拖拽文件夹）
- 桌面通知 / 定时任务
- 多语言支持
- 更多模型支持（本地 Ollama）

---

## 四、技术架构

### 整体架构图

```text
┌─────────────────────────────────────────┐
│         CLI (typer + rich)              │  ← 用户入口
├─────────────────────────────────────────┤
│         Scanner（文件扫描）              │  ← 遍历目录、获取元数据
├─────────────────────────────────────────┤
│         Analyzer（内容分析）             │  ← 提取文件特征
│  ├── 文件名 / 扩展名                    │
│  ├── PDF 提取首页文本                   │
│  ├── 图片用多模态 LLM                   │
│  └── 代码文件读 shebang / 头部           │
├─────────────────────────────────────────┤
│         Classifier（AI 分类）            │  ← 调 LLM 分类
│  ├── litellm（多模型支持）              │
│  └── 缓存层（避免重复调用）              │
├─────────────────────────────────────────┤
│         Planner（生成移动计划）          │  ← 处理冲突、去重
├─────────────────────────────────────────┤
│         Executor（执行移动）             │  ← 移动 + 记录日志
├─────────────────────────────────────────┤
│         History（操作历史）              │  ← 支持 undo
└─────────────────────────────────────────┘
```

### 推荐技术栈

```toml
# pyproject.toml 核心依赖
[project]
dependencies = [
    "typer>=0.12",            # CLI 框架
    "rich>=13",               # 漂亮的终端输出
    "litellm>=1.50",          # 统一多家 LLM API
    "pydantic>=2",            # 数据校验
    "pypdf>=4",               # PDF 文本提取
    "Pillow>=10",             # 图片处理
    "python-magic",           # 文件类型识别
    "diskcache>=5",           # LLM 调用缓存
    "platformdirs",           # 跨平台配置目录
]

[project.optional-dependencies]
local = ["ollama"]            # 本地模型
ui = ["textual>=0.80"]        # TUI 界面（可选）

[project.scripts]
marie = "marie.cli:app"       # 注册命令
```

---

## 五、项目结构

```text
marie/
├── src/
│   └── marie/
│       ├── __init__.py
│       ├── cli.py                   # CLI 入口（typer）
│       ├── core/
│       │   ├── scanner.py           # 文件扫描
│       │   ├── analyzer.py          # 内容分析
│       │   ├── classifier.py        # LLM 分类逻辑
│       │   ├── planner.py           # 整理计划
│       │   ├── executor.py          # 执行移动
│       │   └── history.py           # 操作历史 / undo
│       ├── llm/
│       │   ├── client.py            # litellm 封装
│       │   ├── cache.py             # 调用缓存
│       │   └── prompts/             # Prompt 模板
│       │       ├── classify.txt
│       │       └── image.txt
│       ├── extractors/              # 各文件类型的特征提取
│       │   ├── pdf.py
│       │   ├── image.py
│       │   ├── code.py
│       │   └── archive.py
│       ├── config.py                # 配置管理
│       └── ui/
│           ├── tree.py              # 用 rich 画整理树
│           └── confirm.py           # 交互式确认
├── tests/
│   ├── test_scanner.py
│   ├── test_classifier.py
│   └── fixtures/                    # 测试用的假文件
├── examples/
│   ├── before_after.png             # 整理前后对比图
│   └── demo.gif                     # 演示动图
├── docs/
│   └── prompts.md                   # Prompt 工程文档
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── publish.yml              # 自动发 PyPI
├── pyproject.toml
├── README.md                         # 门面！要花时间打磨
├── LICENSE                           # MIT
├── CONTRIBUTING.md
└── .pre-commit-config.yaml
```

---

## 六、6 周开发路线图（每周 15-20 小时）

### Week 1：地基

- [ ] 初始化项目（用 `uv init`）
- [ ] 搭好 pyproject.toml + ruff + pytest
- [ ] 实现 `Scanner`：递归扫描、获取文件元数据
- [ ] 实现基础 CLI：`marie scan ~/Downloads` 输出文件列表
- **里程碑**：能 print 出"找到 X 个文件"

### Week 2：分类核心

- [ ] 接入 `litellm`，实现最简单的"按文件名分类"
- [ ] 设计 Prompt（输出 JSON，用 Pydantic 校验）
- [ ] 加缓存层（避免每次都调 API）
- [ ] 用 `rich.tree` 展示分类结果
- **里程碑**：跑通 `marie ~/Downloads --dry-run` 看到分类树

### Week 3：内容理解

- [ ] PDF 提取首页文本 → 给 LLM 判断是发票/简历/论文
- [ ] 图片用多模态 LLM（GPT-4o-mini / Claude Haiku）
- [ ] 代码文件识别语言
- **里程碑**：能区分"截图"和"表情包"

### Week 4：执行 + 安全

- [ ] 实现 `Executor`（移动文件 + 处理冲突）
- [ ] 实现 `History`（记录操作 → 支持 undo）
- [ ] 交互式确认（用 `rich.prompt`）
- [ ] 写单元测试
- **里程碑**：完整闭环，敢于在自己电脑上用

### Week 5：打磨 + 文档

- [ ] 进度条 / 美化输出
- [ ] 写详细 README（带 GIF）
- [ ] 录制 Demo（用 [`vhs`](https://github.com/charmbracelet/vhs)）
- [ ] 写 CONTRIBUTING.md / 提交模板
- [ ] 发 PyPI（配置 GitHub Actions 自动发布）
- **里程碑**：v0.1 发布

### Week 6：发布 + 推广

- [ ] 发到 GitHub，写好 release notes
- [ ] 提交到 [Hacker News](https://news.ycombinator.com/show)、[r/Python](https://www.reddit.com/r/Python/)、[r/commandline](https://www.reddit.com/r/commandline/)
- [ ] 写一篇博客（dev.to / 掘金 / 少数派）
- [ ] 发 Twitter / 即刻
- [ ] 收集首批反馈
- **里程碑**：第一批 Star

---

## 七、Prompt 设计（核心难点）

### 分类 Prompt 示例

```text
你是一个文件整理专家。根据下面的文件信息，把它分类到合适的目录。

[文件信息]
- 文件名: invoice_2025_03.pdf
- 大小: 245 KB
- 类型: PDF
- 首页文本片段: "发票号码: 12345 ... 金额: ¥199 ..."

[可选分类]
- 文档/发票
- 文档/合同
- 文档/简历
- 文档/论文
- 文档/其他
- ...

[输出 JSON]
{
  "category": "文档/发票",
  "confidence": 0.95,
  "reason": "包含发票号码和金额，明确是发票文件",
  "suggested_name": "发票_2025_03.pdf"
}
```

### Pydantic 校验

```python
from pydantic import BaseModel, Field

class FileClassification(BaseModel):
    category: str
    confidence: float = Field(ge=0, le=1)
    reason: str
    suggested_name: str | None = None
```

---

## 八、需要避开的坑

### 1. API 成本失控

- 必须做缓存（同一个文件不要重复调用）
- 文件名足够明确时跳过 LLM（先用规则）
- 批量调用（一次给 LLM 看 10 个文件）

### 2. 误移动文件

- **默认 dry-run**，必须显式 `--apply`
- 永远不要删除文件
- 操作前自动备份索引（路径映射 JSON）

### 3. 隐私问题

- 文件名和文件类型可以发给 LLM
- 文件**内容**默认不发，需要用户开启 `--read-content`
- 提供本地模式（Ollama）

### 4. 跨平台兼容

- 用 `pathlib`，不用 `os.path`
- Windows 路径要测试
- 中文文件名要测试

### 5. 不要过度工程化

- MVP 不要做 Web UI
- MVP 不要做插件系统
- MVP 不要做云同步

---

## 九、README 必备元素（决定 80% 的 Star）

按这个顺序写：

```markdown
# Marie ✨
> AI-powered file organizer. Drop a folder, get magic.

[Badges: PyPI / Stars / License / CI]

## 🎬 Demo
[GIF：从混乱的下载文件夹 → 整理后的截图]

## ⚡ Quick Start
pip install marie-sxy
marie ~/Downloads          # 预览
marie ~/Downloads --apply  # 执行

## ✨ Features
- 🧠 AI-powered classification (looks at content, not just names)
- 👀 Dry-run by default (no surprises)
- ↩️ One-command undo
- 🌐 Multi-LLM support (OpenAI / Claude / Gemini / Ollama)
- 🔒 Privacy-first (local mode available)

## 📸 Before / After
[截图对比]

## 🛠 Installation / Configuration / Usage
...

## 🤝 Contributing
...
```

---

## 十、传播策略（拿 Star 关键）

### 第一波（发布日）

- **Hacker News Show HN**：周二/周三上午 9 点（北京时间晚上）
- **Reddit r/Python + r/commandline + r/selfhosted**
- **Twitter/X**：带 GIF，@ 几个 Python 大 V
- **即刻 / 小红书**：中文社区，配"我做了个 AI 工具"故事

### 第二波（持续运营）

- 每发布新版本写 release notes
- 收集用户反馈，标记 `good first issue`
- 上 [awesome-python](https://github.com/vinta/awesome-python) 列表
- 找 [`marktechpost`](https://www.marktechpost.com/) 等 AI 媒体投稿

---

## 立刻可以做的事

不需要等开始写代码，今天就能完成的：

1. ~~**抢名字**：去 [PyPI](https://pypi.org/) 搜 `marie` 看是否被占用~~ → 已确认被占用，最终采用 `marie-sxy`
2. **抢域名**：考虑买个 `.dev` 域名（10 美元/年）
3. **建 GitHub 空仓库**：先把 README 写好，push 上去（哪怕没代码）
4. **拍一张"凌乱的下载文件夹"截图**：作为日后的 before 对比图

### 心态准备

- 第一周可能会迷茫，正常
- 第一个版本会很丑，正常
- 发布后头三天可能没人 star，正常
- **坚持迭代 + 持续推广**，3 个月内能到 100-500 Star

---

## 附录：技术选型理由

| 选择 | 理由 |
|------|------|
| `uv` | 比 pip/poetry 快 10-100 倍，Astral 出品，2025 年的事实标准 |
| `typer` | 基于类型注解，比 click 更现代，FastAPI 同作者 |
| `rich` | 终端美化的天花板，进度条/表格/树形/语法高亮一站式 |
| `litellm` | 一行代码切换 100+ 家 LLM，避免被单家厂商绑定 |
| `pydantic v2` | LLM 输出结构化数据的事实标准，配合 instructor 库更香 |
| `diskcache` | 纯 Python 文件缓存，零依赖，比 Redis 适合 CLI 工具 |
| `platformdirs` | 跨平台配置目录（macOS/Linux/Windows 自动适配）|

---

**文档版本**：v1.0
**最后更新**：2026-05-08
