# 静态个人博客网站搭建与部署报告

## 一、项目概述

本项目的目标是搭建并部署一个静态个人博客网站，使用 Git 进行版本控制，并以 Markdown 文档记录整个过程。通过本次作业，实践了静态网站生成、Git 工作流、部署发布等前端开发的核心技能。

- **网站地址**: [https://sunan-qin.github.io/my-web](https://sunan-qin.github.io/my-web)
- **技术栈**: HTML + CSS + JavaScript（纯静态站点，未使用框架）
- **部署平台**: GitHub Pages
- **版本控制**: Git

---

## 二、网站搭建与部署

### 2.1 部署平台选择：GitHub Pages

选择 GitHub Pages 的原因：

| 优势 | 说明 |
|------|------|
| **免费** | 无需任何费用即可托管静态网站 |
| **与 Git 集成** | 推送代码到仓库即自动部署，CI/CD 零配置 |
| **自定义域名支持** | 可绑定个人域名 |
| **HTTPS 自动启用** | 免费 SSL 证书，安全可靠 |
| **无需服务器运维** | 不需要管理 Nginx、Apache 等 Web 服务器 |

### 2.2 部署步骤

1. **创建 GitHub 仓库**：在 GitHub 上创建名为 `my-web` 的仓库。
2. **初始化本地项目**：
   ```bash
   git init
   git remote add origin https://github.com/sunan-qin/my-web.git
   ```
3. **构建网站文件**：编写 `index.html`、`styles.css`、`script.js` 等静态文件。
4. **启用 GitHub Pages**：进入仓库 Settings → Pages → 将 Source 设为 `main` 分支的 `/root` 目录。
5. **访问验证**：等待 1-2 分钟后，通过 `https://sunan-qin.github.io/my-web` 访问。

### 2.3 网站整合

在个人博客网站上，通过导航栏中的"作业报告"链接，指向第一份作业的 Markdown 报告文件，实现了作业内容的整合呈现。

---

## 三、使用 Git 进行版本控制

### 3.1 Git 提交记录

以下为本项目具有代表性的 6 次 Git 提交记录：

| 序号 | 提交信息 | 说明 |
|------|----------|------|
| 1 | `feat: 初始化项目结构与 README` | 创建项目骨架、初始化 Git 仓库、添加 .gitignore 和 README.md |
| 2 | `feat: 添加网站主页 HTML 结构` | 实现 index.html，包含导航栏、首页、关于我、博客列表等基本页面结构 |
| 3 | `style: 完成响应式 CSS 样式设计` | 添加完整样式表，实现移动端适配、暗色模式、排版美化 |
| 4 | `feat: 添加 JavaScript 交互脚本` | 实现导航切换、暗色模式切换、滚动动画、回到顶部等交互功能 |
| 5 | `docs: 整合第一份作业 Markdown 报告` | 将第一次作业的 Markdown 报告添加到网站，并在导航栏添加链接入口 |
| 6 | `chore: 配置 GitHub Pages 部署` | 配置部署分支、验证部署域名可访问性 |

### 3.2 Git 管理流程

```
main 分支
  |
  |-- commit 1: 项目初始化
  |-- commit 2: HTML 页面结构
  |-- commit 3: CSS 样式
  |-- commit 4: JavaScript 交互
  |-- commit 5: 文档整合
  |-- commit 6: 部署配置
```

每个提交遵循 **Conventional Commits** 规范（`feat:` / `style:` / `docs:` / `chore:`），确保提交信息清晰表达变更意图，便于后期回顾和协作。

---

## 四、静态站点工具选择说明

### 4.1 为什么选择纯静态 HTML/CSS/JS？

#### 优势

1. **学习价值**：从零编写 HTML/CSS/JS 能深入理解网页的工作原理，包括 DOM 结构、CSS 盒模型、Flex/Grid 布局、事件处理等核心概念。
2. **零依赖**：无需安装 Node.js、Ruby、Python 等运行时环境，项目结构简单清晰。
3. **极速加载**：无框架运行时开销，首屏加载几乎没有多余资源，用户体验好。
4. **完全控制**：每一行代码都可以精准控制，不会受到框架黑盒抽象的限制。

#### 适用场景分析

| 方案 | 适用场景 | 复杂度 |
|------|----------|--------|
| **纯静态 HTML/CSS/JS** | 个人主页、单页简历、小型博客 | ☆☆☆☆☆ |
| **Hugo / Hexo** | 内容密集的博客、文档站点 | ★★★☆☆ |
| **VuePress / Docusaurus** | 组件化的文档站点 | ★★★★☆ |
| **Next.js / Gatsby** | 动态内容、需要 SSG/SSR 的应用 | ★★★★★ |

对于本次作业的个人博客展示需求，纯静态方案是最合适的选择。

### 4.2 技术要点

- **HTML5 语义化标签**：使用 `<header>`、`<nav>`、`<main>`、`<article>`、`<footer>` 等语义标签提升可访问性。
- **CSS3 现代布局**：采用 Flexbox 和 CSS Grid 实现响应式布局，通过 `@media` 查询适配移动端。
- **JavaScript ES6+**：使用模块化的 JavaScript 编写交互逻辑，包括 DOM 操作、事件委托、本地存储等。
