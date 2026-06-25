# Static Personal Blog Website Setup and Deployment Report

## I. Project Overview

The goal of this project is to build and deploy a static personal blog website, using Git for version control, and documenting the entire process in Markdown. Through this assignment, core front-end development skills such as static site generation, Git workflow, and deployment were practiced.

- **Website URL**: [https://sunan-qin.github.io/my-web](https://sunan-qin.github.io/my-web)
- **Tech Stack**: HTML + CSS + JavaScript (pure static site, no frameworks used)
- **Deployment Platform**: GitHub Pages
- **Version Control**: Git

---

## II. Website Setup and Deployment

### 2.1 Deployment Platform Selection: GitHub Pages

Reasons for choosing GitHub Pages:

| Advantage | Description |
|-----------|-------------|
| **Free** | No cost required to host static websites |
| **Git Integration** | Auto-deploys upon pushing code to the repository, zero-config CI/CD |
| **Custom Domain Support** | Can bind a personal domain name |
| **Automatic HTTPS** | Free SSL certificate, secure and reliable |
| **No Server Maintenance** | No need to manage Nginx, Apache, or other web servers |

### 2.2 Deployment Steps

1. **Create a GitHub Repository**: Create a repository named `my-web` on GitHub.
2. **Initialize Local Project**:
   ```bash
   git init
   git remote add origin https://github.com/sunan-qin/my-web.git
   ```
3. **Build Website Files**: Write static files such as `index.html`, `styles.css`, `script.js`.
4. **Enable GitHub Pages**: Go to Repository Settings → Pages → Set Source to the `/root` directory of the `main` branch.
5. **Access Verification**: After waiting 1-2 minutes, access via `https://sunan-qin.github.io/my-web`.

### 2.3 Website Integration

On the personal blog website, the "Assignment Reports" link in the navigation bar points to the Markdown report file of the first assignment, achieving integrated presentation of the assignment content.

---

## III. Using Git for Version Control

### 3.1 Git Commit History

The following are 6 representative Git commits for this project:

| No. | Commit Message | Description |
|-----|----------------|-------------|
| 1 | `feat: Initialize project structure and README` | Create project skeleton, initialize Git repository, add .gitignore and README.md |
| 2 | `feat: Add website homepage HTML structure` | Implement index.html, including navigation bar, homepage, about me, blog list and other basic page structures |
| 3 | `style: Complete responsive CSS style design` | Add complete stylesheet, implement mobile adaptation, dark mode, typography beautification |
| 4 | `feat: Add JavaScript interaction scripts` | Implement navigation switching, dark mode toggle, scroll animations, back to top and other interactive features |
| 5 | `docs: Integrate first assignment Markdown report` | Add the first assignment's Markdown report to the website, and add a link entry in the navigation bar |
| 6 | `chore: Configure GitHub Pages deployment` | Configure deployment branch, verify deployment domain accessibility |

### 3.2 Git Management Workflow

```
main branch
  |
  |-- commit 1: Project initialization
  |-- commit 2: HTML page structure
  |-- commit 3: CSS styles
  |-- commit 4: JavaScript interaction
  |-- commit 5: Document integration
  |-- commit 6: Deployment configuration
```

Each commit follows the **Conventional Commits** specification (`feat:` / `style:` / `docs:` / `chore:`), ensuring that commit messages clearly express the intent of changes, facilitating later review and collaboration.

---

## IV. Static Site Tool Selection Explanation

### 4.1 Why Pure Static HTML/CSS/JS?

#### Advantages

1. **Learning Value**: Writing HTML/CSS/JS from scratch provides a deep understanding of how web pages work, including DOM structure, CSS Box Model, Flex/Grid layout, event handling and other core concepts.
2. **Zero Dependencies**: No need to install Node.js, Ruby, Python or other runtime environments; the project structure is simple and clear.
3. **Fast Loading**: No framework runtime overhead, almost no extra resources on initial load, providing a good user experience.
4. **Full Control**: Every line of code can be precisely controlled, without being restricted by framework black-box abstractions.

#### Use Case Analysis

| Approach | Use Case | Complexity |
|----------|----------|------------|
| **Pure Static HTML/CSS/JS** | Personal homepage, single-page resume, small blog | ☆☆☆☆☆ |
| **Hugo / Hexo** | Content-heavy blogs, documentation sites | ★★★☆☆ |
| **VuePress / Docusaurus** | Component-based documentation sites | ★★★★☆ |
| **Next.js / Gatsby** | Dynamic content, applications needing SSG/SSR | ★★★★★ |

For the personal blog showcase needs of this assignment, the pure static approach is the most suitable choice.

### 4.2 Technical Highlights

- **HTML5 Semantic Tags**: Use semantic tags such as `<header>`, `<nav>`, `<main>`, `<article>`, `<footer>` to improve accessibility.
- **CSS3 Modern Layout**: Use Flexbox and CSS Grid for responsive layout, with `@media` queries for mobile adaptation.
- **JavaScript ES6+**: Use modular JavaScript for interactive logic, including DOM manipulation, event delegation, local storage, etc.
