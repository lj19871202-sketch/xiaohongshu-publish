# 发布方式选择与浏览器接入

## 浏览器优先级

1. **内置浏览器**：优先使用当前会话的内置浏览器（保留登录态、可直接控制页面）。
2. **外置浏览器**：内置浏览器不可用或无法完成操作时，才切换 Edge 或 Chrome（按本机可用性与登录态选择），并告知用户已切换。
3. **桥接方案**：会话没有任何浏览器控制工具（如 `js_repl=false`）时，使用下方方案三「Playwright + Edge 调试端口」。

## 必选确认（生成内容后）

- 内容生成并完成预审后，进入发布环节前，**必须先让用户选择**：发布方式（手动 / 半自动 / 自动）和发布时间（立即发布 / 指定时间定时发布）；未选择前不得开始填写或提交。

## 决策表

| 场景 | 推荐路径 |
|---|---|
| 追求稳定、零风控 | 官方「定时发布」+ 操作清单（人工设置一次约 20-30 分钟） |
| 浏览器控制可用（默认） | **内置浏览器优先**；内置浏览器不可用时切换外置浏览器（Edge / Chrome） |
| 有 ChatGPT 或浏览器控制可用 | 半自动：AI 打开页面并填表，用户点发布 |
| 会话具备 Computer Use / 浏览器工具 | 浏览器自动化（仍建议发布前人工确认；按上方浏览器优先级执行） |
| 会话无任何浏览器工具（js_repl=false） | 方案三：Playwright + Edge 调试端口桥接（本技能已验证，不依赖 js_repl） |

## 方案一：官方定时发布（最稳）

- 素材就绪后生成《发布操作清单》，运营按「日期 / 时间 / 标题 / 正文 / 话题 / 配图」逐篇在创作者平台设置定时。
- 零封号风险；小红书无公开发布 API，任何助手都无法绕过登录直接调接口发布。

## 方案二：半自动（推荐组合）

- 助手侧：整理「直接复制版」内容（标题/正文/话题/封面路径），生成一段发给 ChatGPT 的指令：
  打开 creator.xiaohongshu.com → 检查登录（未登录提示扫码）→ 新建笔记填内容 → 设置定时发布 → 用户确认后提交；半自动由用户点发布，浏览器自动化由助手点击并核验。
- ChatGPT 会话需已安装浏览器扩展并授权；默认停在填写完成页面。用户明确确认发布后，可以代为点击发布，并核验页面结果；若用户只要求填写，则不提交。

## 方案三：Playwright + Edge 调试端口（js_repl 关闭时也能自动化）

> 适用场景：内置浏览器与外置浏览器控制均不可用，且当前会话没有暴露 Node REPL / Computer Use 工具（`[features] js_repl = false`），
> 且不想修改全局配置。**不依赖 js_repl 或浏览器扩展**，通过 Edge 调试端口 + Playwright 桥接直接驱动浏览器。
> 已实测可行（2026-08-12），但依赖具体运行环境，可能随版本变化失效。

### 前置条件

- Edge 已安装（本机：`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`）。
- `node.exe` 与 `playwright-core` 可用（本机位于 Codex cua_node 运行库：
  `C:\Users\<用户名>\AppData\Local\OpenAI\Codex\runtimes\cua_node\<版本>\bin\` 下）。
- 桥接脚本：本技能 `scripts/pw-bridge.cjs`（工作区实测副本：`<工作区>\.codex-bridge\pw-bridge.cjs`）。
- 启动 Edge / 后台服务需要提升权限（GUI 应用与读运行库目录）。

### 操作步骤

**1. 启动 Edge（独立 profile + 调试端口）**

```powershell
$profile = "<工作区>\.codex-bridge\edge-profile"   # 独立配置目录，保存登录态，首次需扫码
New-Item -ItemType Directory -Force -Path $profile | Out-Null
Start-Process -FilePath "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" `
  -ArgumentList "--user-data-dir=`"$profile`"","--remote-debugging-port=9222","--remote-allow-origins=*","--no-first-run","--new-window","https://creator.xiaohongshu.com/"
Start-Sleep -Seconds 6
Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/version" -TimeoutSec 5   # 验证端口就绪
```

> 注意：已有 Edge 实例无法附加调试端口，必须用 `--user-data-dir` 独立配置目录启动。
> 端口 9222 被占用时先确认无残留进程。

**2. 启动 Playwright 桥接服务（后台隐藏窗口）**

```powershell
$bridgeDir = "<工作区>\.codex-bridge"
$node = "C:\Users\<用户名>\AppData\Local\OpenAI\Codex\runtimes\cua_node\<版本>\bin\node.exe"
Remove-Item -LiteralPath "$bridgeDir\pw.port" -Force -ErrorAction SilentlyContinue
$p = Start-Process -FilePath $node -ArgumentList "`"$bridgeDir\pw-bridge.cjs`"" -WorkingDirectory $bridgeDir -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 4
$port = Get-Content -LiteralPath "$bridgeDir\pw.port"   # 桥接 HTTP 端口
Invoke-RestMethod -Uri "http://127.0.0.1:$port/health"  # {"ok":true}
```

**3. 通过 HTTP `/exec` 执行 Playwright 代码**

桥接脚本暴露 `POST http://127.0.0.1:<port>/exec`，body：`{"code": "<JS>", "timeout_ms": <ms>}`。
执行上下文提供：`browser`（CDP 连接的浏览器）、`pages`（所有页面）、`page`（首个页面）、`fs`、`path`。
**代码必须以 `return` 返回结果**（AsyncFunction 不会隐式返回最后一个表达式）。

示例——枚举页面并检查登录：

```powershell
$code = @'
const out = [];
for (const p of pages) {
  out.push({ title: await p.title().catch(() => null), url: p.url() });
}
return JSON.stringify(out);
'@
$body = @{ code = $code; timeout_ms = 60000 } | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:$port/exec" -Method Post -ContentType "application/json; charset=utf-8" -Body $body -UseBasicParsing
```

登录检查：读取 `new/home` 页面侧边栏文本，出现昵称（如 `<账号昵称>`）即已登录；未登录提示用户扫码（无法代劳）。

### 表单填写要点（实测，2026-08-12）

- **进入发布**：首页点「发布图文笔记」→ 打开 `publish/publish?from=homepage&target=image` 页面。
- **上传封面**：`p.locator('input[type=file]').first().setInputFiles('封面路径.png')`，等待 3-4 秒。
- **标题**：`input[placeholder="填写标题会有更多赞哦"]`，`click + fill + insertText`；注意 ≤20 字。
- **正文**：`.tiptap.ProseMirror` 编辑区，`click` 后逐段 `keyboard.insertText(...)`，段落间按 `Enter`（不要用 `\n`，换行不会被识别）。
- **话题标签**：在正文末尾逐个 `keyboard.insertText('#话题名 ')`（带空格结尾），间隔 400ms 以上，发布后自动识别为话题。
  **不要点击工具栏「话题」按钮**——会在正文末尾插入孤立 `#`，需用 Backspace 清理。
- **发布方式**：
  - 立即发布：默认状态，发布按钮 `XHS-PUBLISH-BTN` 的 `submit-text="发布"`；
  - 定时发布：点击 `post-time-switch-container` 区域开关（页面下方「定时发布」行）。
- **发布按钮确认**：`XHS-PUBLISH-BTN[submit-disabled="false"]` 可点；`submit-text` 决定文案。
  **默认只填表不提交**；用户明确回复“确认发布/自动发布”后，助手才可点击发布或定时发布，并检查成功提示、跳转页面或作品列表。若用户未确认，停留在可发布页面。
- **营销声明**：正文含「免费」「扣 1」等营销词时，点发布可能弹「内容包含营销广告」声明，需用户手动勾选。

### 风险与注意事项

- 依赖具体运行环境与版本，可能随 Codex 或 Edge 更新失效；环境变量与运行库路径变化时需同步调整。
- 小红书反自动化（滑块、扫码、验证码）需人工介入；高频自动操作有账号风控风险，建议低频率 + 发布前人工核对。
- 复用工作区 `<工作区>\.codex-bridge\edge-profile` 可保留登录态；不要擅自删除该目录。
- 会话结束时不要强制杀 Edge 主进程（可能破坏登录态）；正常关闭浏览器或保留后台即可。

## 通用前提与确认

- 电脑在发布时间点保持开机、浏览器保持登录。
- 未登录需要用户扫码（无法代劳）。
- 发布前把发布方式、标题、正文、话题、封面、定时时间完整列给用户确认。
