<div align="center">

# 期末速成.skill

> “把课程回放里的摘要、转写和思维导图，蒸馏成可以直接复习的课堂笔记。”

<p>
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-yellow">
  <img alt="Python 3.9+" src="https://img.shields.io/badge/Python-3.9%2B-blue">
  <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-Skill-8A2BE2">
  <img alt="Agent Ready" src="https://img.shields.io/badge/Agent-Ready-brightgreen">
  <img alt="CVS Replay" src="https://img.shields.io/badge/CVS-Replay-555">
</p>

一个给 Agent 用的课程回放整理 skill：把你有权限访问的 CVS 课程回放整理成按周课堂笔记，也可以按考试题型生成复习材料。

仓库地址：<https://github.com/Verayi2007/cvs-replay-notes-skill>

技能展示名：`期末速成.skill`<br>
技能内部名：`final-exam-cram`

</div>

---

<div align="center">

## 用户指南

> “你只要给课程链接和考试题型，剩下交给 Agent 跑。”

<p>
  <img alt="User Guide" src="https://img.shields.io/badge/User-Guide-555">
  <img alt="Course Notes" src="https://img.shields.io/badge/Weekly-Notes-blue">
  <img alt="Exam Review" src="https://img.shields.io/badge/Exam-Review-green">
</p>

</div>

# 第一部分：用户指南

这一部分给普通用户看。你不需要懂脚本，也不需要手动分析接口，只需要把下面的内容发给你的 Agent。

## 1. 最简单的用法

把这段话复制给 Agent：

```text
请使用这个 GitHub 仓库里的 skill：
https://github.com/Verayi2007/cvs-replay-notes-skill

skill 名称：期末速成.skill

帮我导出这个 CVS 课程回放，并生成按周整理的课堂笔记：
这里粘贴 CVS play-center 回放链接
```

课程链接最好长这样：

```text
https://cvs.seu.edu.cn/.../#/play-center?teclId=...&courseId=...&target=video
```

完整 `play-center` 链接比单独 `courseId` 更好，因为它通常包含 `teclId`，Agent 可以用它列出整门课的所有回放。

## 2. 想顺便按题型整理考点

把这段话发给 Agent：

```text
请使用这个 GitHub 仓库里的 skill：
https://github.com/Verayi2007/cvs-replay-notes-skill

skill 名称：期末速成.skill

帮我导出这个 CVS 课程回放，生成按周课堂笔记，并按考试题型整理考点。

周次：all
题型：名词解释、简答题、论述题、列举题、案例分析
课程链接：这里粘贴 CVS play-center 回放链接
```

题型可以按真实考试改，例如：

```text
名词解释、简答题、论述题、列举题、案例分析、比较题
```

理科、工科或编程课可以写成：

```text
定义题、公式题、推导题、证明题、计算题、实验题、算法题
```

## 3. 已经爬过课程，只想重新整理

如果本地已经有 `weekly_data.json`，可以不重新爬取：

```text
请使用这个 GitHub 仓库里的 skill：
https://github.com/Verayi2007/cvs-replay-notes-skill

skill 名称：期末速成.skill

根据已有 weekly_data.json，不重新爬取课程，只按这些题型重新整理考点：
名词解释、简答题、论述题、列举题、案例分析
```

Agent 应该优先在本地寻找最新的 `weekly_data.json`。如果有多个课程数据，它应该让你选择。

## 4. 你需要准备什么

- CVS 课程回放的完整 `play-center` 链接。
- 可以正常登录 CVS 的账号状态。
- 如果 Agent 打开浏览器要求登录，你需要在弹出的 Chrome 或 Edge 中手动登录。

可选提供：

- 周次范围，例如 `all`、`1-16`、`9,11,12,13`。
- 考试题型。
- 老师给过的考试范围或复习提示。
- 想要的输出格式，例如 Markdown 或 Word。

## 5. 会生成什么

常见输出：

```text
weekly_notes.md        按周、按课次整理的课堂笔记
exam_type_review.md    按题型整理的考点预测/复习材料
weekly_data.json       结构化课程数据，后续可复用
raw/*.json             原始接口响应，只建议本地保存
```

`exam_type_review.md` 是复习辅助，不保证真实考试一定命中。

## 6. 重要提醒

- 只用于你本人有权限访问的课程。
- 默认不下载课程视频。
- 不要把生成的课程笔记、原始 JSON、浏览器 profile、Cookie、JWT 或视频文件公开到 GitHub。
- 如果公开工具代码，只公开代码和说明，不公开课程内容。

---

<div align="center">

## Agent 指南

> “先拿授权数据，再整理知识点，最后按题型变成复习材料。”

<p>
  <img alt="Agent Guide" src="https://img.shields.io/badge/Agent-Guide-555">
  <img alt="CDP Workflow" src="https://img.shields.io/badge/CDP-Workflow-blue">
  <img alt="No Video Download" src="https://img.shields.io/badge/No_Video_Download-Default-green">
</p>

</div>

# 第二部分：Agent 指南

这一部分给执行任务的 Agent 看。收到本仓库链接后，请按以下步骤执行。

## 1. 加载方式

本仓库根目录就是 skill 根目录。优先读取：

```text
SKILL.md
```

按需读取：

```text
references/principles.md
references/exam_planning.md
```

脚本入口：

```text
scripts/cvs_weekly_notes_exporter.py
```

如果环境支持安装 Codex skill，请直接把本仓库作为 skill 安装或加载。如果不能自动安装，请克隆仓库并按 `SKILL.md` 与本 README 执行。

```powershell
git clone https://github.com/Verayi2007/cvs-replay-notes-skill
cd cvs-replay-notes-skill
pip install websocket-client
```

## 2. 判断任务类型

收到用户请求后，先判断属于哪一种：

1. **首次爬取课程**：用户提供 CVS `play-center` URL。
2. **首次爬取并按题型整理**：用户提供 URL 和题型。
3. **复用已有数据整理题型**：用户要求根据已有数据重新整理。
4. **转成 Word 或继续润色**：先确认 Markdown 内容已经生成。

如果用户只给 `courseId`，追问完整 `play-center` URL 或 `teclId`。完整 URL 比单独 ID 更可靠，因为 `teclId` 用来列出整门课回放。

## 3. 首次爬取课程

运行：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks all --manual-login-timeout 120
```

如果用户指定周次：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks 9,11,12,13 --manual-login-timeout 120
```

如果浏览器需要登录，让用户在弹出的 Chrome 或 Edge 中手动登录，然后等待脚本继续。

## 4. 首次爬取并按题型整理

运行：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks all --exam-types "名词解释,简答题,论述题,列举题,案例分析" --manual-login-timeout 120
```

题型来自用户原话。可以把顿号、逗号、分号、换行统一解析成列表，不要强迫用户按固定格式输入。

## 5. 复用已有数据，不重新爬取

先找 `weekly_data.json`：

```powershell
Get-ChildItem -Recurse -Filter weekly_data.json | Sort-Object LastWriteTime -Descending
```

如果只有一个明显候选，直接使用。如果有多个，询问用户要用哪一个。如果没有，要求用户提供 CVS `play-center` URL 先爬取。

运行：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py --from-data ".\outputs\weekly_xxx\weekly_data.json" --exam-types "名词解释,简答题,论述题,列举题,案例分析"
```

---

<div align="center">

## 爬取原理

> “它爬的不是视频，而是官方页面已经使用的学习数据。”

<p>
  <img alt="Authorized" src="https://img.shields.io/badge/Authorized-Only-brightgreen">
  <img alt="JSON APIs" src="https://img.shields.io/badge/JSON-APIs-blue">
  <img alt="Transcript" src="https://img.shields.io/badge/Transcript-Timestamps-555">
</p>

</div>

## 6. 它具体爬取什么

不要把这个流程描述成“下载视频”。它主要请求 CVS 官方前端已经使用的学习数据 JSON：

```text
subject_vod_list_new
course/ai/textSummary/{courseId}
course/ai/summary/search/{courseId}
course/ai/translate/{courseId}
```

这些数据通常包含：

- 回放列表、周次、课次、教师、教室、回放状态。
- AI 总览和关键知识点。
- 分段课堂概要。
- 思维导图节点。
- 带时间戳的转写或字幕片段。

运行机制：

1. 启动本地 Chrome 或 Edge，并开启 Chrome DevTools Protocol。
2. 打开用户提供的 CVS `play-center` 页面。
3. 用户如未登录，则在浏览器里手动登录。
4. 在页面上下文中使用 `fetch(..., credentials: "include")` 请求 JSON。
5. 只在内存中读取前端同样使用的 `jwt-token` 请求头，不打印、不保存真实 token。
6. 将 JSON 整理为按周笔记和题型复习材料。

---

<div align="center">

## 押题逻辑

> “按题型整理考点，但不假装自己能保证命题。”

<p>
  <img alt="Question Types" src="https://img.shields.io/badge/Question-Types-blue">
  <img alt="Evidence Based" src="https://img.shields.io/badge/Evidence-Based-green">
  <img alt="Prediction" src="https://img.shields.io/badge/Prediction-Not_Guarantee-yellow">
</p>

</div>

## 7. 题型整理规则

候选考点来源优先级：

1. `keyPoints`
2. `fullOverview`
3. `documentSkims`
4. `mindmap.nodes`
5. `translate.afterAssemblyList`

文科、通识类常见题型信号：

- 名词解释：概念、定义、内涵、特征。
- 简答题：功能、原因、影响、方法、原则。
- 论述题：关系、意义、价值、发展、融合。
- 列举题：类型、分类、要素、阶段、方法。
- 案例分析：具体案例、地点、事件、人物、实践。
- 比较题：相同点、不同点、传统与现代、中外比较。

理科、工科、编程课不要机械套用文科模板，应切换到：

```text
定义、定理、公式、推导、证明、计算、实验、模型、算法、误差分析
```

输出时必须说明：这是“考点整理/复习预测”，不是保证命题。

## 8. 输出交付

完成后告诉用户：

- 输出目录。
- 成功处理了哪些周次和课次。
- 是否有缺失周次。
- 是否有接口失败。
- 生成了哪些文件。

如果用户要 Word 文档，先确认 Markdown 内容可用，再转换成 `.docx`。

---

<div align="center">

## 安全边界

> “只处理用户有权访问的课程，只公开工具代码，不公开课程内容。”

<p>
  <img alt="Private Data" src="https://img.shields.io/badge/Course_Data-Private-red">
  <img alt="No Cookies" src="https://img.shields.io/badge/No-Cookies-red">
  <img alt="MIT" src="https://img.shields.io/badge/License-MIT-yellow">
</p>

</div>

## 9. 安全与合规要求

必须遵守：

- 只处理用户本人有权限访问的课程。
- 不绕过登录、权限、付费或平台访问控制。
- 不爆破、不猜测课程 ID，不批量扫无关课程。
- 默认不下载课程视频。
- 不提交浏览器 profile、Cookie、JWT、原始课程数据、生成笔记、日志或媒体文件。
- 生成的课程材料默认保持私有，除非用户确认有权分享。

提交或公开修改前，扫描敏感信息：

```powershell
rg -n "jwt-token|Authorization|Bearer|Cookie|password|token|SESSDATA|OPENAI_API_KEY|DASHSCOPE_API_KEY" -S .
```

源码中出现 `jwt-token` 这样的请求头名称是可以的；出现真实 token 值是不可以的。

## 10. 失败处理

- 登录失败或 401/403：让用户重新登录 CVS，不要尝试绕过。
- 找不到回放：报告平台返回的周次和 `vodStatus`，不要编造内容。
- 某周没有回放：明确写“平台未返回该周可用回放”。
- 网络/VPN 冲突：让用户在本机浏览器登录，尽量复用本地会话。
- 中文乱码：确保文件按 UTF-8 读写。
- 多个 `weekly_data.json`：让用户选择课程或输出目录。

## 许可证

MIT
