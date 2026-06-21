# 给 Agent 的使用指南：CVS 回放笔记 Skill

你是一个收到本仓库链接的 agent。用户希望你使用这个 skill，从其有权限访问的 CVS 课程回放中导出课程笔记，并可按考试题型整理考点。

仓库链接：

```text
https://github.com/Verayi2007/cvs-replay-notes-skill
```

本仓库根目录就是 skill 根目录。核心入口是：

```text
SKILL.md
```

请优先阅读并遵守 `SKILL.md`。当需要理解原理或题型整理逻辑时，再读取：

```text
references/principles.md
references/exam_planning.md
```

可执行脚本在：

```text
scripts/cvs_weekly_notes_exporter.py
```

## 1. 你应该先做什么

如果你的运行环境支持安装 Codex skill，请把本仓库作为 skill 安装或加载。

如果不能自动安装，请直接按以下顺序处理：

1. 克隆或读取本仓库。
2. 阅读 `SKILL.md`。
3. 根据用户输入判断是“首次爬取课程”还是“基于已有数据重新整理题型”。
4. 必要时运行 `scripts/cvs_weekly_notes_exporter.py`。
5. 将生成的笔记路径、输出内容摘要和任何失败原因告诉用户。

手动克隆示例：

```powershell
git clone https://github.com/Verayi2007/cvs-replay-notes-skill
cd cvs-replay-notes-skill
```

Python 依赖：

```powershell
pip install websocket-client
```

## 2. 向用户索取什么输入

### 首次爬取课程

最少只需要用户提供一个 CVS `play-center` 回放链接。

推荐让用户发这种链接：

```text
https://cvs.seu.edu.cn/.../#/play-center?teclId=...&courseId=...&target=video
```

原因：

- `teclId` 用来列出整门课或整个教学班的回放。
- `courseId` 通常只代表当前这一节课，单独给 `courseId` 不足以稳定导出整门课。
- 完整 URL 能让浏览器打开正确的平台页面和登录上下文。

可选输入：

```text
周次：all / 1-16 / 9,11,12,13
题型：名词解释、简答题、论述题、列举题、案例分析、比较题
输出：Markdown / Word / 只要数据
```

如果用户只给 `courseId`，请追问完整 `play-center` URL 或 `teclId`。

### 已经爬取过课程

如果用户只说“按题型重新整理”“重新押题”“根据已有数据整理考点”，你应该先在当前工作区搜索最新的 `weekly_data.json`。

可以用：

```powershell
Get-ChildItem -Recurse -Filter weekly_data.json | Sort-Object LastWriteTime -Descending
```

如果只找到一个明显候选，直接复用。  
如果找到多个课程，询问用户要用哪一个。  
如果没有找到，要求用户提供 CVS `play-center` URL 先爬取。

## 3. 典型用户请求与对应动作

### 用户给课程链接，要求按周生成笔记

用户可能会说：

```text
用这个 skill 整理这个课程回放：
https://cvs.seu.edu.cn/.../#/play-center?teclId=...&courseId=...
```

你应该运行：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks all --manual-login-timeout 120
```

如果浏览器要求登录，请让用户在弹出的 Chrome/Edge 中手动登录，然后等待脚本继续。

### 用户给课程链接和题型

用户可能会说：

```text
用这个 skill 爬取课程，题型是名词解释、简答题、论述题、列举题、案例分析。
链接：...
```

你应该运行：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks all --exam-types "名词解释,简答题,论述题,列举题,案例分析" --manual-login-timeout 120
```

### 用户只给题型，要求重新整理

用户可能会说：

```text
根据已有数据，按名词解释、简答题、论述题、列举题、案例分析重新整理。
```

你应该找到 `weekly_data.json`，然后运行：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py --from-data ".\outputs\weekly_xxx\weekly_data.json" --exam-types "名词解释,简答题,论述题,列举题,案例分析"
```

## 4. 输出文件如何交付

脚本通常会生成：

```text
weekly_data.json       结构化课程数据，后续可复用
raw/*.json             原始接口响应，只应本地保存
weekly_notes.md        按周、按课次整理的课堂笔记
exam_type_review.md    按题型整理的考点预测/复习材料
```

交付时告诉用户：

- 输出目录在哪里；
- 哪些周次和课次被成功处理；
- 是否有缺失周次或接口失败；
- 如果生成了题型整理，说明它是“复习预测/考点整理”，不是保证命题。

如果用户需要 Word 文档，你可以在 Markdown 内容确认后再转换为 `.docx`。

## 5. 它具体爬取什么

这个 skill 不是下载视频来听写笔记，而是通过已登录浏览器请求 CVS 前端本来就会使用的学习数据接口。

核心接口包括：

```text
subject_vod_list_new
course/ai/textSummary/{courseId}
course/ai/summary/search/{courseId}
course/ai/translate/{courseId}
```

这些接口通常提供：

- 回放列表、周次、课次、教师、教室、回放状态；
- AI 总览和关键知识点；
- 分段课堂概要；
- 思维导图节点；
- 带时间戳的转写/字幕片段。

运行机制：

1. 启动本地 Chrome 或 Edge，并开启 Chrome DevTools Protocol。
2. 打开用户提供的 CVS `play-center` 页面。
3. 用户如未登录，则在浏览器里手动登录。
4. 在页面上下文中使用 `fetch(..., credentials: "include")` 请求 JSON。
5. 只在内存中读取前端同样使用的 `jwt-token` 请求头，不打印、不保存真实 token。
6. 将 JSON 整理为按周笔记和题型复习材料。

## 6. 题型整理如何工作

题型整理不是“保证押中”，而是根据课程材料生成复习优先级。

候选考点来源优先级：

1. `keyPoints`
2. `fullOverview`
3. `documentSkims`
4. `mindmap.nodes`
5. `translate.afterAssemblyList`

常见题型信号：

- 名词解释：概念、定义、内涵、特征；
- 简答题：功能、原因、影响、方法、原则；
- 论述题：关系、意义、价值、发展、融合；
- 列举题：类型、分类、要素、阶段、方法；
- 案例分析：具体案例、地点、事件、人物、实践；
- 比较题：相同点、不同点、传统与现代、中外比较。

如果课程是理科、工科或编程课，不要机械使用文科模板。应把题型规则切换为：

```text
定义、定理、公式、推导、证明、计算、实验、模型、算法、误差分析
```

## 7. 安全与合规要求

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

## 8. 失败时怎么处理

- 登录失败或 401/403：让用户重新登录 CVS，不要尝试绕过。
- 找不到回放：报告平台返回的周次和 `vodStatus`，不要编造内容。
- 第某周没有回放：明确写“平台未返回该周可用回放”。
- 网络/VPN 冲突：让用户在本机浏览器登录，尽量复用本地会话。
- 中文乱码：确保文件按 UTF-8 读写。
- 多个 `weekly_data.json`：让用户选择课程或输出目录。

## 9. 最短执行提示

当用户只把这个 GitHub 链接发给你时，你可以按下面这句话理解任务：

```text
读取本仓库的 SKILL.md。若用户提供 CVS play-center URL，则用 scripts/cvs_weekly_notes_exporter.py 导出课程回放学习数据并生成 weekly_notes.md；若用户提供考试题型，则额外生成 exam_type_review.md；若已有 weekly_data.json，则优先用 --from-data 复用已有数据。
```

## 许可证

MIT
