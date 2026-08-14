# xiaohongshu-publish

> 小红书笔记发布技能（Codex Skill）· Xiaohongshu (RED) Note Publishing Skill
>
> 收集并校验标题 / 正文 / 话题标签 / 封面，生成发布包，并引导完成发布。
> Collect and validate title / body / hashtags / cover, generate a publish pack, and guide the publishing workflow.

## 目录 / Table of Contents

1. [简介 / Introduction](#1-简介--introduction)
2. [功能特性 / Features](#2-功能特性--features)
3. [目录结构 / Repository Structure](#3-目录结构--repository-structure)
4. [安装 / Installation](#4-安装--installation)
5. [环境要求与快速安装 / Requirements & Quick Setup](#5-环境要求与快速安装--requirements--quick-setup)
6. [使用方法 / Usage](#6-使用方法--usage)
7. [标准流程 / Standard Workflow](#7-标准流程--standard-workflow)
8. [发布方式 / Publishing Paths](#8-发布方式--publishing-paths)
9. [脚本说明 / Scripts Reference](#9-脚本说明--scripts-reference)
10. [关键规则 / Key Rules](#10-关键规则--key-rules)
11. [本地化适配 / Localization](#11-本地化适配--localization)
12. [协议 / License](#12-协议--license)

---

## 1. 简介 / Introduction

**中文**

`xiaohongshu-publish` 是一个面向 Codex 的**参考流程技能**，帮助完成小红书图文笔记的发布准备与发布引导。所有内容由用户提供、不固定，技能负责：解析五要素（标题、备选标题、正文、话题标签、封面图）→ 补齐缺失项 → 校验 → 生成「发布操作清单 + 直接复制版」发布包 → 按选定路径完成发布（手动 / 半自动 / 浏览器自动化）。

核心原则：**缺什么补什么，补完才生成发布包**；任何内容未经用户确认不得发布。

**English**

`xiaohongshu-publish` is a **reference-workflow skill** for Codex that prepares and guides Xiaohongshu (RED) image-text note publishing. All content is user-provided and varies per task. The skill parses the five elements (title, alt title, body, hashtags, cover image), fills in missing items, validates them, generates a publish pack (operation checklist + copy-ready version), and guides publishing through manual, semi-automated, or browser-automated paths.

Core principle: **fill in whatever is missing, and only generate the publish pack when everything is complete**; nothing is published without explicit user confirmation.

## 2. 功能特性 / Features

**中文**

- **五要素收集、补齐与校验**：标题（≤20 字）、备选标题、正文（保留换行与 emoji，不自行改写）、话题标签（通常 5-7 个）、封面图（至少 1 张）
- **生成发布包**：「发布操作清单」（Markdown）+「直接复制版」（txt，含 ChatGPT 半自动指令）
- **三种发布方式**：官方定时发布 / 半自动（AI 填表、用户点发布）/ Playwright + Edge 调试端口自动化
- **覆盖常见坑点**：标题超限截断、正文换行注入失效、话题残留字符、营销声明弹窗、按钮隐藏等
- **双重确认门禁**：解析结果确认（门禁①）+ 发布前最终确认（门禁②），两步不可互相替代

**English**

- **Collect, complete, and validate the five elements**: title (≤20 chars), alt title, body (preserves line breaks & emoji, never rewritten), hashtags (typically 5-7), cover image (at least 1)
- **Generate a publish pack**: an operation checklist (Markdown) and a copy-ready bundle (txt, including a ChatGPT semi-auto instruction)
- **Three publishing paths**: official scheduled publish / semi-automated (AI fills the form, user clicks publish) / Playwright + Edge debugging-port automation
- **Covers known pitfalls**: title overflow/truncation, newline injection failures, leftover `#` characters, marketing-declaration popups, hidden buttons, etc.
- **Double confirmation gates**: parsed-content confirmation (gate 1) + final pre-publish confirmation (gate 2); they cannot replace each other

## 3. 目录结构 / Repository Structure

| 路径 / Path | 说明 / Description |
|---|---|
| `SKILL.md` | 技能主文件：标准流程、五要素校验规则、输入约定、关键规则 |
| `README.md` | 本文件：技能说明与使用文档（中英双语） |
| `agents/openai.yaml` | 技能元数据（OpenAI agents 格式） |
| `references/content-production.md` | 内容生产参考：竞品调研、系列文案撰写、素材拆分、配图库规范 |
| `references/platform-notes.md` | 创作者平台表单填写细节与实测坑点 |
| `references/publish-paths.md` | 发布方式决策表、Playwright 桥接操作步骤与风险说明 |
| `scripts/build_publish_pack.py` | 生成发布包（操作清单 + 直接复制版），支持素材文件或直传参数 |
| `scripts/pw-bridge.cjs` | Playwright + Edge 调试端口桥接服务，暴露 HTTP 接口 |
| `scripts/setup.ps1` | 一键环境检查与依赖安装脚本 |
| `package.json` | npm 依赖声明（`playwright-core`）与 `npm run setup` 快捷命令 |

## 4. 安装 / Installation

**中文**

- **方式一（推荐）**：使用 skill-installer 技能从本仓库安装；
- **方式二**：将仓库内容手动放入 Codex 技能目录，如 `~/.codex/skills/xiaohongshu-publish`（Windows：`%USERPROFILE%\.codex\skills\xiaohongshu-publish`）；
- 安装完成后重启 Codex 会话，即可在对话中按技能流程使用。
- 建议运行 `scripts/setup.ps1` 完成环境检查与依赖安装（详见第 5 节）。

**English**

- **Option 1 (recommended)**: install via the skill-installer skill from this repository;
- **Option 2**: copy the repository contents into a Codex skills directory, e.g. `~/.codex/skills/xiaohongshu-publish` (Windows: `%USERPROFILE%\.codex\skills\xiaohongshu-publish`);
- Restart the Codex session after installation.
- It is recommended to run `scripts/setup.ps1` afterwards to check the environment and install dependencies (see section 5).

## 5. 环境要求与快速安装 / Requirements & Quick Setup

**中文**

运行本技能需要以下环境：

| 组件 | 用途 | 说明 |
|---|---|---|
| Python 3 | `build_publish_pack.py` | 仅用标准库，无需 pip 安装任何包 |
| Node.js | `pw-bridge.cjs` | 版本 ≥ 14 即可，需包含 npm |
| Microsoft Edge | 浏览器自动化 | 通过调试端口驱动，无需下载 Chromium |
| playwright-core | `pw-bridge.cjs` | 自动安装到仓库本地 `node_modules`，或自动探测 Codex 运行库 |

一键检查与安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
# 或：npm run setup
```

脚本会检查上述四项是否就绪；缺失时给出提示，并用 npm 把 `playwright-core` 安装到仓库本地
`node_modules`（需要联网），最后做加载验证。参数：`-SkipInstall`（只检查不安装）、`-Force`（强制重装）。

**English**

Running this skill requires:

| Component | Used by | Notes |
|---|---|---|
| Python 3 | `build_publish_pack.py` | stdlib only; no pip packages needed |
| Node.js | `pw-bridge.cjs` | ≥ 14, with npm |
| Microsoft Edge | browser automation | driven via debugging port; no Chromium download |
| playwright-core | `pw-bridge.cjs` | auto-installed into repo-local `node_modules`, or auto-detected from the Codex runtime |

One-command check & setup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
# or: npm run setup
```

The script verifies the four items above, warns about missing ones, installs `playwright-core` into the
repo-local `node_modules` via npm (network required), and verifies it can be loaded. Options:
`-SkipInstall` (check only), `-Force` (reinstall).

## 6. 使用方法 / Usage

**中文**

**对话式使用**：直接给出标题、正文、话题标签、封面路径，或提供素材文件路径（推荐格式见 `SKILL.md` 的「输入约定」），技能会解析五要素、补齐缺失项并生成发布包。

**脚本直用**：

```powershell
# 素材文件方式
python scripts/build_publish_pack.py --source "素材.txt" --time "明天 10:10"

# 直传参数方式
python scripts/build_publish_pack.py --title "标题" --body "正文" --tags "#话题1 #话题2" --cover "封面.jpg" --theme "主题" --num "02" --time "立即发布"
```

**输出产物**：

- `小红书发布操作清单_NN_主题.md`：手动发布操作清单
- `小红书发布内容_直接复制版_NN_主题.txt`：直接复制版（含 ChatGPT 半自动指令）
- 控制台「发布前待确认清单」：标题字数、话题数量、封面文件等校验警告

**English**

**Chat usage**: provide title, body, hashtags, and cover path directly in conversation, or pass a material file path (recommended format in `SKILL.md` → “Input conventions”). The skill parses the five elements, fills gaps, and generates the publish pack.

**Direct script usage**: see the PowerShell examples above.

**Outputs**:

- `小红书发布操作清单_NN_主题.md` — manual operation checklist
- `小红书发布内容_直接复制版_NN_主题.txt` — copy-ready bundle (includes a ChatGPT semi-auto instruction)
- Console “pre-publish confirmation checklist” — validation warnings for title length, hashtag count, cover file, etc.

## 7. 标准流程 / Standard Workflow

**中文**

| 步骤 | 内容 | 输出 / 门禁 |
|---|---|---|
| 1. 收集输入 | 判断输入类型 → 解析五要素 → 补齐缺失 → 校验 | 解析结果经用户确认（门禁①） |
| 2. 生成发布包 | 运行 `scripts/build_publish_pack.py` | 操作清单 + 直接复制版 |
| 3. 选择发布方式 | 按 `references/publish-paths.md` 决策表选择 | 手动 / 半自动 / 自动化 |
| 4. 平台填写与确认 | 按 `references/platform-notes.md` 填表 | 发布前最终确认（门禁②），发布按钮由用户点击 |

**五要素校验规则**：

| 要素 | 校验规则 |
|---|---|
| 标题 | 必填；≤20 字，超限与用户确认或换备选标题 |
| 备选标题 | 可选；缺失不阻塞 |
| 正文 | 保留换行与 emoji，不自行改写 |
| 话题标签 | 通常 5-7 个；缺失或过少时提示补充 |
| 封面图 | 至少 1 张；缺失时进入补齐步骤 |

门禁①确认**解析结果**（内容是否正确提取、有无缺失）；门禁②确认**最终发布状态**（登录账号、发布时间、表单填写结果）。两步不互相替代。

**English**

The workflow has four steps: (1) collect input — classify input type, parse the five elements, fill gaps, validate; (2) generate the publish pack with `scripts/build_publish_pack.py`; (3) choose a publishing path per the decision table in `references/publish-paths.md`; (4) fill the platform form per `references/platform-notes.md` and confirm before publishing.

Two confirmation gates apply: gate 1 confirms the **parsed content** (correct extraction, no missing items); gate 2 confirms the **final publish state** (logged-in account, publish time, form contents). They cannot replace each other.

## 8. 发布方式 / Publishing Paths

**中文**

| 场景 | 推荐路径 |
|---|---|
| 追求稳定、零风控 | 官方「定时发布」+ 操作清单（人工设置，约 20-30 分钟） |
| 有 ChatGPT 或浏览器控制可用 | 半自动：AI 打开页面并填表，用户点发布 |
| 会话具备 Computer Use / 浏览器工具 | 浏览器自动化（发布前仍人工确认） |
| 会话无任何浏览器工具（如 js_repl=false） | Playwright + Edge 调试端口桥接（方案三，本技能已验证） |

注意事项：

- 小红书无公开发布 API，任何方式都无法绕过登录直接发布；
- 默认先停在填写完成页面；用户明确确认后，半自动由用户点击发布，自动化模式可由助手点击发布并核验结果；
- 高频自动操作有账号风控风险，建议低频率 + 发布前人工核对；
- 未登录时需用户扫码，助手无法代劳。

**English**

| Scenario | Recommended path |
|---|---|
| Maximum stability, zero risk | Official scheduled publish + operation checklist (manual, ~20-30 min) |
| ChatGPT or browser control available | Semi-automated: AI opens the page and fills the form, user clicks publish |
| Computer Use / browser tools available | Browser automation (still confirm before publishing) |
| No browser tools in session (e.g. js_repl=false) | Playwright + Edge debugging-port bridge (path 3, verified) |

Notes:

- Xiaohongshu has no public publishing API; no method can bypass login;
- By default, stop after filling the form; after explicit user confirmation, semi-automated mode leaves the button to the user, while browser automation may click it and verify the result;
- High-frequency automation carries account-risk-control risk; keep frequency low and review before publishing;
- Login requires the user to scan a QR code; the assistant cannot do it.

## 9. 脚本说明 / Scripts Reference

### `scripts/build_publish_pack.py`

**中文**：生成发布包，支持素材文件（`--source`）与直传参数两种输入（可混用，直传优先）。

| 参数 / Option | 说明 / Description |
|---|---|
| `--source` | 素材 txt 路径 |
| `--title` / `--body` | 直传标题 / 正文（无 `--source` 时必填） |
| `--tags` | 话题标签，如 `#话题1 #话题2` |
| `--cover` | 封面图路径 |
| `--outdir` | 输出目录（默认：素材上级目录 / 当前目录） |
| `--time` | 发布方式或时间描述，如 `立即发布`、`明天 10:10` |
| `--num` / `--theme` | 篇序号 / 篇主题（默认从文件名提取） |

### `scripts/setup.ps1`

**中文**：一键检查 Python 3 / Node.js / Edge / `playwright-core`；缺失时提示，并自动把
`playwright-core` 安装到仓库本地 `node_modules`（需要联网）。参数：`-SkipInstall`（只检查不安装）、
`-Force`（强制重装）。

**English**: one-command environment check & setup. It verifies Python 3 / Node.js / Edge /
`playwright-core`, warns about missing items, and auto-installs `playwright-core` into the repo-local
`node_modules` (network required). Options: `-SkipInstall` (check only), `-Force` (reinstall).

### `scripts/pw-bridge.cjs`

**中文**：

- 用途：Playwright + Edge 调试端口桥接服务，HTTP 接口 `GET /health`、`POST /exec`；
- 依赖：本机 `node.exe` 与 `playwright-core`（优先使用仓库本地 `node_modules`，其次自动探测 Codex 运行库，
  也可通过环境变量 `PW_PLAYWRIGHT_MODULES` 指定目录）；
- 详细操作见 `references/publish-paths.md` 方案三。

**English**: `build_publish_pack.py` generates the publish pack from a material file or direct arguments
(see the option table above). `setup.ps1` performs a one-command environment check and dependency install.
`pw-bridge.cjs` is a Playwright-to-Edge bridge service exposing `GET /health` and `POST /exec`; it prefers
the repo-local `node_modules`, auto-discovers `playwright-core` under the Codex runtime directory, or uses
the `PW_PLAYWRIGHT_MODULES` environment variable. See `references/publish-paths.md`, path 3 for details.

## 10. 关键规则 / Key Rules

**中文**

- 标题不超过 20 字；超限先与用户确认，或换用备选标题；
- 发布前必须向用户确认完整内容与定时时间；默认停在填写完成页面，自动化发布只有在用户明确确认后才提交并核验；
- 会话没有浏览器控制工具时，**不擅自修改全局配置**（如 `js_repl` / Computer Use 开关），优先使用方案三桥接；
- 正文含「免费」「扣 1」等营销词时，可能触发平台营销声明，需用户手动处理；
- 官方「定时发布」最稳定、零风控；发布节奏建议每周一 / 三 / 五。

**English**

- Titles must be ≤20 characters; if over, confirm with the user or switch to the alt title;
- Always confirm the full content and schedule with the user before publishing; stop after filling by default, and let browser automation submit only after explicit confirmation and result verification;
- When no browser-control tool is available in the session, do **not** modify global configuration (e.g. `js_repl` / Computer Use toggles); prefer the path-3 bridge;
- Marketing words such as “free” or “comment 1” may trigger a platform marketing declaration that requires manual handling;
- Official scheduled publishing is the most stable option with zero risk; a Monday/Wednesday/Friday cadence is suggested.

## 11. 本地化适配 / Localization

**中文**：文档与示例使用占位符，按本机实际环境替换：

| 占位符 | 含义 |
|---|---|
| `<工作区>` | 素材与工作目录（如 `F:\codex`） |
| `<用户名>` | Windows 用户名（如 `C:\Users\11`） |
| `<版本>` | Codex 运行库版本号 |
| `<账号昵称>` | 小红书账号昵称 |

`pw-bridge.cjs` 也可通过环境变量 `PW_PLAYWRIGHT_MODULES` 直接指定依赖目录，无需改代码。

**English**: Paths in the docs use placeholders — `<工作区>` (workspace root), `<用户名>` (Windows username), `<版本>` (Codex runtime version), `<账号昵称>` (Xiaohongshu nickname). Replace them with your local values; alternatively point `pw-bridge.cjs` to your dependency directory via the `PW_PLAYWRIGHT_MODULES` environment variable.

## 12. 协议 / License

**中文**：本项目暂未指定开源协议，仅供个人学习与内部工作流参考；如需二次发布或商用，请先与作者确认。

**English**: This project does not yet specify an open-source license. It is provided as a reference workflow for personal/private use; contact the author before redistribution or commercial use.
