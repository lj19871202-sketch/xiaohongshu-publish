# xiaohongshu-publish

小红书笔记发布参考流程技能（Codex Skill）：收集并校验标题/正文/话题标签/封面等要素，生成「发布操作清单 + 直接复制版」发布包，并支持手动、半自动与 Playwright 浏览器自动化三种发布路径。

## 功能

- 五要素（标题/备选标题/正文/话题标签/封面）收集、补齐与校验
- 生成发布操作清单与直接复制版（含 ChatGPT 半自动指令）
- 三种发布方式：官方定时发布 / 半自动 / Playwright + Edge 调试端口自动化
- 覆盖标题 20 字限制、话题数量、封面缺失、营销声明等常见坑点

## 安装

作为 Codex 技能使用，将本仓库内容放入技能目录（如 `~/.codex/skills/xiaohongshu-publish`），或用 skill-installer 技能从本仓库安装。

## 使用

在 Codex 对话中给出标题、正文、话题标签、封面路径（或素材文件），技能会按标准流程生成发布包并引导发布：

```powershell
python scripts/build_publish_pack.py --source "素材.txt" --time "明天 10:10"
python scripts/build_publish_pack.py --title "标题" --body "正文" --tags "#话题1 #话题2" --cover "封面.jpg" --theme "主题" --num "02" --time "立即发布"
```

详细流程见 `SKILL.md` 与 `references/` 目录。

## 注意事项

- 标题不超过 20 字；发布前必须向用户确认完整内容与定时时间。
- 半自动/自动化模式下，发布按钮始终留给用户点击。
- 文档中的 `<工作区>`、`<用户名>`、`<账号昵称>` 等为占位符，请按本机实际路径替换。
