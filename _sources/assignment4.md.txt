# IntelliPaper — 智能文献管理工具

## AI辅助开发报告

> **📥 立即下载**：`点击下载 IntelliPaper.exe 

<https://github.com/sunan-qin/my-web/blob/main/_static/downloads/IntelliPaper.exe>`_
---

## I. 背景与设计

### 1.1 软件简介

**IntelliPaper**（全称：Smart Literature Manager）是一款面向研究人员的跨平台桌面文献管理应用。它帮助用户组织、搜索、分析、标注和导出学术论文，并提供可选的AI辅助功能（摘要生成、关键词提取、RAG问答和对话式研究助手）。

### 1.2 设计动机

在学术研究过程中，研究人员经常面临以下痛点：

- **文献散落各处**：PDF文件存放在不同文件夹，缺乏统一管理。
- **元数据录入繁琐**：手动输入标题、作者、摘要等极为耗时。
- **检索困难**：文件系统中无法对论文标题、摘要、全文进行模糊搜索。
- **引用管理复杂**：不同投稿格式（BibTeX、RIS、APA、MLA、Chicago）切换麻烦。
- **AI赋能缺失**：现有工具（如Zotero、Mendeley）缺乏与LLM的深度集成。

**核心设计理念**：**"一个桌面应用，解决文献管理全流程"**——从PDF导入→元数据自动提取→存储与索引→搜索与发现→笔记与标注→引用导出→AI分析，形成完整闭环。

### 1.3 架构决策

采用经典的**三层架构**，模块化分离关注点：

`
┌──────────────────────────────────────────────────┐
│                   UI Layer (PyQt5)                │
│  MainWindow │ Dashboard │ PaperDetail │ Chat     │
│  ImportDialog │ TagDialog │ StatsDialog          │
├──────────────────────────────────────────────────┤
│               Business Logic Layer               │
│  SearchEngine │ SemanticSearch │ CitationExport  │
│  PDFExtractor │ CrossrefAPI │ RAG_QA │ HotFolder│
│  BatchImport │ ExportManager │ AIAssistant       │
├──────────────────────────────────────────────────┤
│               Data Layer (SQLite)                │
│  Models (Paper/Tag) │ Database (CRUD/FullText)  │
└──────────────────────────────────────────────────┘
`

**关键架构决策**：

| 决策 | 选择 | 理由 |
|------|------|------|
| GUI框架 | PyQt5 | 跨平台，原生外观，信号/槽异步机制 |
| 数据库 | SQLite + WAL模式 | 零配置，单文件部署，WAL实现并发读，适合桌面应用 |
| PDF引擎 | PyMuPDF (fitz) | 纯Python高速绑定，元数据+全文提取 |
| AI接口 | 原生HTTP (urllib) | 无外部SDK依赖，支持DeepSeek/OpenAI/Ollama多模型 |
| 搜索方案 | 双层混合搜索 | TF-IDF内置搜索 + 可选sentence-transformers语义搜索 |
| 打包 | PyInstaller | 单文件.exe发布，用户无需安装Python |

---

## II. 技术栈

| 类别 | 技术 |
|------|------|
| **编程语言** | Python 3.9 |
| **GUI框架** | PyQt5 5.15 |
| **PDF处理** | PyMuPDF (fitz) |
| **数据库** | SQLite3（WAL模式，迁移式schema演进） |
| **图像处理** | Pillow 8.0 |
| **语义搜索** | sentence-transformers（可选） |
| **AI模型支持** | DeepSeek-V3 / DeepSeek-R1 / OpenAI GPT-4o / GPT-3.5-turbo / Ollama |
| **构建工具** | PyInstaller 6.20 |
| **测试框架** | pytest 8.4 |
| **操作系统** | Windows 11（开发） / 跨平台（运行） |
| **CPU** | AMD Ryzen 5 5600H |
| **AI开发伙伴** | Codex CLI（基于OpenAI gpt-4o） |

---

## III. 功能特性清单

### 核心功能

| 类别 | 功能 | 说明 |
|------|------|------|
| 📄 **导入** | PDF自动提取 | 导入PDF后自动识别标题、作者、摘要、DOI、年份、期刊 |
| | 拖放导入 | 直接将PDF文件拖入论文列表 |
| | BibTeX/RIS导入 | 批量导入.bib或.ris文件 |
| | 热文件夹监控 | 后台线程实时监控指定目录，自动导入新PDF |
| | 标题搜索导入 | 通过OpenAlex API按标题搜索论文元数据 |
| 🔍 **搜索** | 全文搜索 | 标题/作者/摘要/笔记/DOI多字段联合搜索 |
| | 关键词命中提升 | 标题匹配+5分，作者匹配+3分，提升相关性排名 |
| | 上下文片段 | 搜索结果展示匹配词周围的上下文文本 |
| | 语义搜索 | 可选sentence-transformers嵌入，支持"相似论文推荐" |
| | 高级筛选 | 按标题/作者/年份范围/论文类型/标签/阅读状态筛选 |
| 🏷️ **组织** | 标签管理 | 颜色标签，完整的CRUD管理 |
| | 标签筛选 | 下拉菜单按标签筛选论文 |
| | 可排序表格 | 点击表头按标题/作者/年份/期刊/添加日期排序 |
| | 阅读状态 | 未读/待读/进行中/已读四种状态追踪 |
| | 论文类型 | 期刊/会议/预印本/书籍/论文/其他分类 |
| 📝 **笔记** | 每论文笔记 | 为任意论文添加自由文本笔记 |
| | 自动保存 | 30秒无操作自动保存，切换论文时即时保存 |
| | 笔记导出 | 以Markdown格式导出论文笔记 |
| 📖 **导出** | BibTeX | 一键复制BibTeX引用到剪贴板 |
| | RIS | RIS格式导出，兼容EndNote/Zotero |
| | 多格式引用 | APA 7th / MLA 9th / Chicago格式 |
| | 批量导出 | JSON批量导出/导入整个文库 |
| 🤖 **AI** | 论文摘要 | 结构化摘要（背景/方法/结果/局限），自动填入UI |
| | 关键词提取 | 提取5-8个研究关键词 |
| | 标签建议 | 基于内容建议3-5个分类标签 |
| | RAG问答 | 基于论文全文的检索增强生成问答 |
| | 对话式助手 | 浮动聊天窗口，理解整个文库上下文 |
| | 统计洞察 | AI对文库统计数据的智能解读 |
| 🔐 **备份** | 数据库备份 | 时间戳命名的SQLite快照备份 |
| | 数据库恢复 | 从任意备份文件安全恢复 |
| | 完整归档 | 导出.zip格式（含数据库+PDF附件+缓存） |
| 🖥️ **UX** | 明暗主题 | 一键切换亮色/暗色主题 |
| | 键盘快捷键 | Ctrl+O/E/I/K/D/, 全套快捷键支持 |
| | PDF查看 | 双击或Ctrl+D系统默认打开PDF |
| | 启动闪屏 | 启动时优雅的品牌闪屏 |
| | 全局异常钩子 | 所有未处理异常写入日志并友好提示 |
| | 统计数据 | 年份分布/期刊排名/作者排名/标签云等可视化 |

### 奖励挑战完成情况

| 挑战 | 是否完成 | 说明 |
|------|----------|------|
| **AI智能体集成（+3分）** | ✅ | 浮动AI聊天窗口 + RAG问答对话框 + AI摘要/关键词/标签建议 + 统计AI解读。全异步QThread实现，绝不阻塞UI |
| **跨平台支持（+2分）** | ✅ | PyQt5原生跨平台 + 纯Python无平台依赖 + 数据目录跨平台兼容策略 |

---

## IV. 开发日志

### 4.1 第一阶段：架构规划与数据模型

通过与Codex CLI的讨论，确定了以下核心设计：

- **三层架构**：数据模型层（Paper/Tag/Relationship），业务逻辑层（CRUD/搜索/导出），UI层（PyQt5）
- **数据库**：SQLite，零配置、单文件部署
- **数据模型**：
  - Paper：id, title, authors, abstract, year, journal, doi, file_path, notes, tags, reading_status, rating, paper_type等
  - Tag：id, name, color
  - paper_tags：多对多关联表
- **Schema迁移**：通过 	ry-except ALTER TABLE ADD COLUMN 实现v2→v3自动演进

**AI贡献**：
- Codex建议使用 @dataclass 定义数据模型
- 建议WAL模式提升并发读性能
- 创建title/year/doi索引，fulltext_cache表缓存PDF文本

### 4.2 第二阶段：PDF提取和搜索引擎

**PDF提取策略**：
1. 先读PDF元数据的title字段
2. 如果缺失，从正文前20行中筛选（长度>20且<300，排除章节标题关键词）
3. DOI提取：正则 10.\d{4,}/[^\s,;)]+
4. 年份提取：匹配19xx-20xx范围
5. 性能限制：仅提取前50页

**搜索引擎实现**：
- 搜索词拆分逐词匹配，标题匹配+5分，作者匹配+3分
- 片段提取：定位首个匹配词，前后各取80字符上下文
- 语义搜索：可选 ll-MiniLM-L6-v2，失败时自动降级TF-IDF

**幻觉处理**：

| 问题 | AI最初建议 | 人工/迭代修正 |
|------|-----------|--------------|
| 搜索算法过于简单 | 线性累加匹配次数 | 增加标题/作者加权，防止常见词刷分 |
| PDF提取regex复杂 | 一次性提取所有字段 | 拆分为独立函数，更好维护和测试 |

### 4.3 第三阶段：AI助手集成

**多模型支持设计**：

`python
MODEL_PROVIDERS = {
    "DeepSeek-V3":     {"base_url": "https://api.deepseek.com/...", "model": "deepseek-chat"},
    "DeepSeek-R1":     {"base_url": "https://api.deepseek.com/...", "model": "deepseek-reasoner"},
    "OpenAI GPT-4o":   {"base_url": "https://api.openai.com/...",   "model": "gpt-4o"},
    "OpenAI GPT-3.5":  {"base_url": "https://api.openai.com/...",   "model": "gpt-3.5-turbo"},
    "Ollama (Local)":  {"base_url": "http://localhost:11434/...",   "model": "llama3"},
}
`

**异步架构**：API调用在QThread线程中执行，通过Qt信号（pyqtSignal）将结果传回主线程，彻底避免UI冻结。

**关键Bug修复记录**：

| Bug | 表现 | 根因 | 修复 |
|-----|------|------|------|
| 导入路径错误 | PyInstaller打包后崩溃 | 相对导入在打包后失效 | 改为绝对导入 |
| PyQt5枚举变更 | QTableView.SingleRow不存在 | PyQt5版本间API变更 | 改为 QAbstractItemView.SingleSelection |
| f-string引号冲突 | 语法错误 | PowerShell生成文件时引号转义 | 手动修正引号嵌套 |
| DeepSeek-R1参数 | API返回400 | R1不支持temperature参数 | 条件移除 temperature |
| Ollama响应格式 | KeyError异常 | Ollama响应结构与OpenAI不同 | 增加分支处理 |

### 4.4 第四阶段：UI开发

**主窗口特色**：
- QSplitter可调节左右分栏布局
- 搜索框300ms去抖（QTimer），避免每次按键触发查询
- QTableView + QSortFilterProxyModel 排序
- 自定义DragDropTableView支持PDF拖放导入
- 明暗主题通过150行动态QSS样式表实现

**浮动聊天窗口**：
- 始终置顶的浮动无边框窗口
- 鼠标事件重写实现自由拖拽移动
- Ctrl+Enter发送消息，实时状态反馈

**统计数据仪表盘**：
- 统计卡片：总计/未读/已读/进行中
- 年份分布 + 期刊排名（Unicode条形图）
- 标签云（HSL颜色动态缩放）
- AI统计解读按钮

### 4.5 第五阶段：测试与打包

**测试覆盖（36个测试全部通过）**：

| 测试文件 | 数量 | 覆盖内容 |
|----------|------|----------|
| tests/test_models.py | 7 | Paper格式化、引用生成、默认值 |
| tests/test_database.py | 18 | CRUD、搜索、全文、统计、标签、隔离临时DB |
| tests/test_search_engine.py | 11 | 相关性评分、片段生成、BibTeX/RIS导出 |

**打包成果**：
- [IntelliPaper.exe（78.7 MB）](./IntelliPaper.exe) 单文件免安装可执行程序
- PyInstaller --onefile --windowed 模式

---

## V. 关键问题与解决方案

### 5.1 AI幻觉处理

| 场景 | AI幻觉表现 | 处理方式 |
|------|-----------|----------|
| PDF元数据提取 | AI建议使用多个第三方API | 采用本地PyMuPDF + 正则，无网络依赖更可靠 |
| 搜索相关性 | AI建议BM25算法 | 使用轻量TF-IDF + 标题/作者加权，避免引入外部库 |
| AI摘要格式 | AI返回非结构化文本 | 强制prompt模板：四段式结构 |
| RAG问答 | AI编造文献内容 | 使用检索chunk作为上下文约束LLM生成 |

### 5.2 工程化挑战

| 挑战 | 解决方案 |
|------|----------|
| PyInstaller打包后模块找不到 | 使用 --hidden-import 显式声明，绝对导入 |
| 数据库schema兼容 | try-except ALTER TABLE ADD COLUMN 自动迁移 |
| 跨平台数据目录 | ~/.smart-lit-manager → %TEMP%/smart-lit-manager 带fallback |
| UI响应性 | AI调用进QThread，搜索300ms去抖 |
| 大PDF性能 | 仅提取前50页，控制全文缓存 |

---


`

### 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 导入论文 |
| Ctrl+E | 导出JSON |
| Ctrl+I | 导入JSON |
| Ctrl+K | 设置API密钥 |
| Ctrl+D | 打开PDF |
| Ctrl+, | 偏好设置 |
| Ctrl+Q | 退出 |

---

## VII. 项目结构

`
smart-lit-manager/
├── main.py                          # 入口：闪屏 + 全局异常钩子 + 高DPI支持
├── app/                             # 后端/业务逻辑层
│   ├── models.py                    # 数据模型：Paper, Tag, SearchResult
│   ├── database.py                  # SQLite ORM（CRUD/搜索/标签/统计/备份/恢复）
│   ├── pdf_extractor.py             # PDF元数据+全文提取（PyMuPDF）
│   ├── search_engine.py             # 排名搜索 + 上下文片段
│   ├── semantic_search.py           # 混合语义搜索（sentence-transformers/TF-IDF）
│   ├── citation_export.py           # 引用导出：BibTeX, RIS, APA, MLA, Chicago
│   ├── ai_assistant.py              # AI助手：多模型 + QThread异步
│   ├── rag_qa.py                    # RAG问答：chunk分割+检索+LLM生成
│   ├── batch_import.py              # BibTeX/RIS文件解析
│   ├── crossref_api.py              # Crossref DOI + OpenAlex查询
│   ├── hot_folder.py                # 热文件夹监控（后台线程）
│   ├── export_manager.py            # .zip完整归档（含PDF+DB+缓存）
│   └── logger.py                    # 结构化日志 + 全局异常钩子
├── ui/                              # 前端/GUI层（PyQt5）
│   ├── main_window.py               # 主窗口（菜单/搜索/表格/拖放/设置）
│   ├── paper_model.py               # QAbstractTableModel（可排序）
│   ├── paper_detail.py              # 详情面板（摘要/笔记/AI/引用/PDF）
│   ├── import_dialog.py             # 导入对话框（含自动提取）
│   ├── tag_dialog.py                # 标签管理（颜色选择器）
│   ├── stats_dialog.py              # 统计仪表盘（图表/标签云/洞察）
│   ├── dashboard_page.py            # 首页仪表盘（统计卡片+最近论文）
│   └── chat_window.py               # 浮动AI聊天窗口（始终置顶）
├── tests/                           # 测试套件（36个全通过）
│   ├── test_models.py               # 7 tests
│   ├── test_database.py             # 18 tests
│   └── test_search_engine.py        # 11 tests
├── build_exe.py                     # PyInstaller构建脚本
├── requirements.txt                 # 依赖声明
└── README.md                        # 项目文档
`

---

## VIII. 结论与展望

### 项目总结

IntelliPaper成功地将AI辅助开发从"娱乐式提示"推向了"工程化结果"。项目展示了一个完整的软件工程交付——从架构设计到代码实现、从测试覆盖到可执行打包，全程以LLM（Codex CLI）作为主要开发伙伴完成。

**项目亮点**：
- ✅ [IntelliPaper.exe（78.7 MB）](./IntelliPaper.exe) 独立可执行文件，零外部依赖
- ✅ 36个全覆盖单元测试，全部通过
- ✅ 5个AI模型切换支持（DeepSeek、OpenAI、Ollama）
- ✅ RAG问答引擎 + 浮动AI聊天窗口
- ✅ 跨平台运行（Windows/macOS/Linux）
- ✅ 完整的文献管理全流程闭环

### 后续可能扩展

- **Web服务版本**：Flask/FastAPI后端 + React前端
- **同步服务**：WebDAV/Nextcloud多设备同步
- **浏览器扩展**：自动捕获论文元数据
- **引用网络图**：论文引用关系可视化
- **更多AI能力**：论文翻译、研究方法建议、审稿意见生成

---

*报告生成日期：2026年6月15日*
