#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成小红书发布包：发布操作清单 + 直接复制版（含 ChatGPT 半自动指令）。

内容由用户提供，支持两种输入方式（可混用，直传参数优先）：
1. 素材文件：--source "<工作区>\\小红书发布素材\\文字\\01_工位免费3个月\\01_工位免费3个月.txt"
2. 直接传参：--title/--body/--tags/--cover/--theme/--num

用法示例:
    python build_publish_pack.py --source "素材.txt" --time "明天 10:10"
    python build_publish_pack.py --title "标题" --body "正文" --tags "#话题1 #话题2" --cover "封面.jpg" --theme "主题" --num "02" --time "立即发布"
"""

import argparse
import re
import sys
from pathlib import Path


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def section(text: str, name: str) -> str:
    # 节标题可能带后缀，如 【发布参数（第一篇 · 试发布）】，按名称前缀匹配
    m = re.search(r"【" + name + r"[^】]*】\s*(.*?)(?=【|$)", text, re.S)
    return m.group(1).strip() if m else ""


def first_line(sec: str) -> str:
    for line in sec.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def param_value(sec: str, key: str) -> str:
    for line in sec.splitlines():
        line = line.strip()
        for sep in ("：", ":"):
            if line.startswith(key + sep):
                return line.split(sep, 1)[1].strip()
    return ""


def validate_title(title: str) -> list:
    if not title.strip():
        return ["缺少标题，请补充标题或确认使用备选标题"]
    if len(title) > 20:
        return [f"标题约 {len(title)} 字，超过 20 字限制，请与用户确认或换用备选标题：{title}"]
    return []


def validate_tags(tags: str) -> list:
    tags_clean = [t for t in re.split(r"[\s#]+", tags.strip()) if t]
    if not tags_clean:
        return ["缺少话题标签，请与用户确认或按正文内容建议补充"]
    if len(set(tags_clean)) != len(tags_clean):
        return ["话题标签存在重复，请确认是否需要删减"]
    if len(tags_clean) < 5:
        return [f"话题标签仅 {len(tags_clean)} 个（建议 5-7 个）"]
    if len(tags_clean) > 10:
        return [f"话题标签共 {len(tags_clean)} 个，数量偏多，请确认是否需要删减"]
    return []


def validate_body(body: str) -> list:
    if not body.strip():
        return ["缺少正文，请补充正文后再生成发布包"]
    return []


def scan_risk_candidates(title: str, body: str, tags: str) -> list:
    """只做词面候选扫描；必须由上下文、证据和授权复核后才能下结论。"""
    text = "\n".join(part for part in (title, body, tags) if part)
    candidates = []
    checks = [
        (r"保证|一定|绝对|零风险|100%|永久|根治|最有效", "发现绝对化/保证性表述，需结合证据和适用范围复核"),
        (r"月入|收入|赚到|暴涨|翻倍|收益|回报|增收|变现", "发现收益或效果主张，需核对证据、范围及商业关系披露"),
        (r"加我微信|加微信|微信号|vx|V信|扫码|联系方式|手机号|邮箱|telegram|discord", "发现站外联系方式或导流候选，需确认是否应改为站内动作"),
        (r"医美|医疗|治疗|药物|投资|理财|股票|基金|贷款|升学|保录|培训结果", "涉及可能的高风险行业或结果主张，需进行更严格的证据与边界复核"),
        (r"免费|扣[一1]|评论区.*(数字|扣)|私信.*领取", "发现营销/领取导向候选，需核实实际商业关系并按页面提示处理"),
    ]
    for pattern, message in checks:
        if re.search(pattern, text, re.I):
            candidates.append(message)
    if re.search(r"\d+(?:\.\d+)?\s*(?:%|万|元|天|个月|倍|人|条|个)", text):
        candidates.append("发现精确数字或结果量词，需确认来源、时间范围、适用条件和图片文字是否一致")
    return candidates


def validate_cover(cover: str, base_dir=None) -> list:
    if not cover or "请指定封面" in cover:
        return ["缺少封面图路径，请向用户确认或从配图库选用"]
    candidates = [Path(cover)]
    if base_dir:
        candidates.append(base_dir / cover)
    if not any(p.is_file() for p in candidates):
        return [f"封面文件不存在：{cover}"]
    return []


def build_checklist(m: dict) -> str:
    body_quote = m["body"].replace("\n", "\n> ")
    warnings = m.get("warnings", [])
    preflight = (
        "脚本已发现以下需要人工复核的候选：\n\n" +
        "\n".join(f"- {warning}" for warning in warnings)
        if warnings else
        "脚本未发现词面候选；仍需人工完成上下文、证据、授权和标题—封面—正文一致性复核。"
    )
    return f"""# 第{m['num']}篇《{m['theme']}》发布操作清单

> 用途：在浏览器控制通道不可用时的手动发布备用清单；内容与自动化发布一致。

## 1. 素材位置

- 正文来源：`{m['source'] or '（对话输入，无文件）'}`
- 封面图：`{m['cover']}`{m['alt_cover_note']}

## 2. 内容预审提示

> 下面是脚本候选扫描，不是平台判定；未完成上下文复核前不要发布。

{preflight}

## 3. 操作步骤

1. 打开 Chrome 或 Edge，访问创作者平台：https://creator.xiaohongshu.com/
2. 确认账号已登录；未登录则扫码登录（第一次登录需扫码）。
3. 左侧菜单进入「创作服务」→「发布笔记」（或首页「发布」按钮）。
4. 上传封面：`{m['cover']}`
5. 填写标题：
   > {m['title']}
6. 填写正文（见下）。
7. 填写话题标签：`{m['tags']}`
8. 发布方式：{m['publish_time']}。
9. 核对无误后提交；发布前把填好的页面截图或关键信息发回确认。

## 4. 正文

> {body_quote}

## 5. 备选标题

{m['alt_title'] or '（未提供）'}
"""


def build_direct_copy(m: dict) -> str:
    is_immediate = m["publish_time"].strip() in {"立即发布", "现在发布"}
    publish_action = "核对无误后点「发布」" if is_immediate else "设置定时发布时间，核对无误后点「定时发布」"
    chatgpt_mode = "填好内容后先给我确认，我确认后由我手动点「发布」" if is_immediate else "设置好定时发布后先给我确认，我确认后由我手动点「定时发布」"
    chatgpt = f"""请用浏览器打开小红书创作者平台 https://creator.xiaohongshu.com/ ，先检查登录状态；如果未登录，提示我扫码。登录后新建一篇笔记并帮我填写以下内容，{chatgpt_mode}：

标题：{m['title']}

正文：
{m['body']}

话题标签：{m['tags']}

封面图：{m['cover']}
定时时间：{m['publish_time']}。"""
    warnings = m.get("warnings", [])
    preflight = "；".join(warnings) if warnings else "脚本未发现词面候选，但仍需人工完成上下文、证据、授权和一致性复核"
    return f"""================ 小红书第{m['num']}篇《{m['theme']}》直接复制版 ================

【一、标题】（复制这一行）
{m['title']}

【二、正文】（复制下面整段，含空行）
{m['body']}

【三、话题标签】（复制这一行）
{m['tags']}

【四、封面图】
{m['cover']}

【五、发布前预审提示】（不要复制到平台）
{preflight}

【六、发布步骤（人工操作）】
1. 打开 https://creator.xiaohongshu.com/ ，确认已登录（未登录先扫码）。
2. 「创作服务 → 发布笔记」→ 上传封面图。
3. 标题框粘贴【一】的内容；正文框粘贴【二】的内容；话题区粘贴【三】的内容。
4. 发布方式：{m['publish_time']}。
5. {publish_action}。

【七、交给 ChatGPT 半自动操作的指令】（复制下面整段，发给 ChatGPT）
{chatgpt}

================ END ================
"""


def print_confirmation(m: dict, warnings: list) -> None:
    lines = [
        "===== 发布前待确认清单 =====",
        f"序号/主题：{m['num'] or '-'} {m['theme']}",
        f"标题（约 {len(m['title'])} 字）：{m['title']}",
    ]
    if m.get("alt_title"):
        lines.append(f"备选标题：{m['alt_title']}")
    lines.append(f"正文：\n{m['body']}")
    lines.append(f"话题标签：{m['tags'] or '（缺失）'}")
    lines.append(f"封面图：{m['cover']}")
    if m.get("carousel"):
        lines.append(f"轮播图：{m['carousel']}")
    if m.get("alt_cover") and m["alt_cover"] != m["cover"]:
        lines.append(f"备选封面：{m['alt_cover']}")
    lines.append(f"发布方式/时间：{m['publish_time']}")
    if warnings:
        lines.append("需与用户确认的警告：")
        lines.extend(f"  [警告] {w}" for w in warnings)
    lines.append("============================")
    print("\n".join(lines))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="生成小红书发布包（操作清单 + 直接复制版）")
    parser.add_argument("--source", default=None, help="单篇素材 txt 路径（可选）")
    parser.add_argument("--title", default=None, help="标题（直传时必填）")
    parser.add_argument("--body", default=None, help="正文（直传时必填）")
    parser.add_argument("--tags", default=None, help="话题标签，如：#话题1 #话题2")
    parser.add_argument("--cover", default=None, help="封面图路径")
    parser.add_argument("--outdir", default=None, help="输出目录，默认素材文件所在目录（新目录约定下即 文字\\<主题>）；直传时默认当前目录")
    parser.add_argument("--time", default="立即发布", help="定时时间描述，如：立即发布 / 明天 10:10")
    parser.add_argument("--num", default=None, help="篇序号，默认从文件名提取")
    parser.add_argument("--theme", default=None, help="篇主题，默认取文件名下划线后部分")
    args = parser.parse_args()

    m = {"publish_time": args.time, "alt_cover": "", "carousel": ""}
    warnings = []
    src = None

    if args.source:
        src = Path(args.source)
        text = read_source(src)
        params_sec = section(text, "发布参数")
        stem = src.stem
        num_match = re.match(r"(\d+)", stem)
        m["num"] = args.num or (num_match.group(1) if num_match else "")
        m["theme"] = args.theme or re.sub(r"^\d+_?", "", stem)
        m["title"] = args.title or first_line(section(text, "标题"))
        m["alt_title"] = first_line(section(text, "备选标题"))
        m["body"] = args.body or section(text, "正文")
        m["tags"] = args.tags or " ".join(section(text, "话题标签").split())
        m["cover"] = args.cover or param_value(params_sec, "封面图") or param_value(params_sec, "备选封面") or "（请指定封面图路径）"
        m["alt_cover"] = param_value(params_sec, "备选封面")
        m["carousel"] = param_value(params_sec, "轮播图")
        m["alt_cover_note"] = f"\n- 备选封面：`{m['alt_cover']}`" if m["alt_cover"] and m["alt_cover"] != m["cover"] else ""
        m["source"] = str(src)
    else:
        if not args.title or not args.body:
            parser.error("请提供 --source 素材文件，或提供 --title 与 --body 直传内容")
        m["num"] = args.num or ""
        m["theme"] = args.theme or "新笔记"
        m["title"] = args.title
        m["alt_title"] = ""
        m["body"] = args.body
        m["tags"] = args.tags or ""
        m["cover"] = args.cover or "（请指定封面图路径）"
        m["alt_cover_note"] = ""
        m["source"] = ""

    outdir = Path(args.outdir) if args.outdir else (src.parent if src else Path.cwd())
    outdir.mkdir(parents=True, exist_ok=True)
    suffix = f"{m['num']}_{m['theme']}" if m["num"] else m["theme"]
    checklist = outdir / f"小红书发布操作清单_{suffix}.md"
    direct = outdir / f"小红书发布内容_直接复制版_{suffix}.txt"
    warnings += validate_title(m["title"])
    warnings += validate_body(m["body"])
    warnings += validate_tags(m["tags"])
    warnings += validate_cover(m["cover"], src.parent if src else None)
    warnings += scan_risk_candidates(m["title"], m["body"], m["tags"])
    m["warnings"] = warnings
    checklist.write_text(build_checklist(m), encoding="utf-8-sig")
    direct.write_text(build_direct_copy(m), encoding="utf-8-sig")
    print(f"[OK] {checklist}")
    print(f"[OK] {direct}")
    print_confirmation(m, warnings)


if __name__ == "__main__":
    main()
