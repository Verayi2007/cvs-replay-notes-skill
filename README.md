# CVS 回放笔记 Skill

`cvs-replay-notes` 是一个 Codex skill，用来把用户有权限访问的 CVS 课程回放整理成按周分类的课程笔记，并且可以根据考试题型进一步整理考点，生成类似“押题/复习方向”的材料。

它适用于学校课程回放系统中已经由平台生成的学习数据，例如 AI 摘要、分段概要、思维导图和转写文本。它**不会绕过登录**、**不会破解视频**，默认也**不下载课程视频**。

## 用户应该给 Agent 什么

首次导出一门课程时，用户最少只需要给 agent 一个 CVS `play-center` 回放链接：

```text
请使用这个 skill 导出 CVS 课程回放，并生成按周整理的课堂笔记：
https://cvs.seu.edu.cn/.../#/play-center?teclId=...&courseId=...&target=video
```

如果希望同时按考试题型整理考点，可以这样说：

```text
请使用这个 skill 导出 CVS 课程回放。
周次：all
题型：名词解释、简答题、论述题、列举题、案例分析
链接：https://cvs.seu.edu.cn/.../#/play-center?teclId=...&courseId=...
```

如果课程之前已经导出过，用户可以只要求重新按题型整理：

```text
请使用这个 skill，根据已有课程数据，按名词解释、简答题、论述题、列举题、案例分析重新整理考点。
```

这时 agent 应该优先复用本地最新的 `weekly_data.json`，不需要重新打开浏览器爬取。

## 其他 Agent 如何使用

把这个仓库链接发给支持 skills 的 agent：

```text
请安装或使用这个 Codex skill：
https://github.com/Verayi2007/cvs-replay-notes-skill
```

本仓库根目录就是 skill 根目录，结构如下：

```text
SKILL.md
agents/openai.yaml
references/principles.md
references/exam_planning.md
scripts/cvs_weekly_notes_exporter.py
```

如果 agent 不能自动安装 skill，也可以直接阅读 `SKILL.md`，再运行 `scripts/cvs_weekly_notes_exporter.py`。

## 它具体爬取什么

这个 skill 会在本地 Chrome 或 Edge 中打开 CVS 回放页面，然后请求 CVS 官方前端本来就会使用的 JSON 数据：

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

最推荐的输入是完整的 `play-center` 链接，因为它通常包含 `teclId`。`teclId` 可以列出整门课或整个教学班的回放；单独的 `courseId` 往往只代表某一节课，不足以稳定导出整门课。

## 输出文件

脚本可以生成：

```text
weekly_data.json       结构化课程数据，便于后续复用
raw/*.json             原始接口响应，只建议本地保存
weekly_notes.md        按周、按课次整理的课堂笔记
exam_type_review.md    按题型整理的考点预测/复习材料
```

其中 `exam_type_review.md` 是复习辅助，不保证真实考试一定命中。

## 题型整理逻辑

skill 会从这些来源里抽取候选考点：

1. `keyPoints`
2. `fullOverview`
3. `documentSkims`
4. `mindmap.nodes`
5. `translate.afterAssemblyList`

然后根据来源重要性、重复程度和题型关键词进行分类与排序：

- 名词解释：概念、定义、内涵、特征；
- 简答题：功能、原因、影响、方法、原则；
- 论述题：关系、意义、价值、发展、融合；
- 列举题：类型、分类、要素、阶段、方法；
- 案例分析：具体案例、地点、事件、人物、实践；
- 比较题：相同点、不同点、传统与现代、中外比较。

如果课程是理科、工科或编程课，这套流程仍然可用，但题型规则应该改成更适合 STEM 的版本，例如定义、定理、公式、推导、证明、计算、实验、模型或算法。

## 直接运行脚本

安装 Python 依赖：

```powershell
pip install websocket-client
```

导出全部可用周次：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks all --manual-login-timeout 120
```

导出指定周次，并同时生成题型整理：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks 9,11,12,13 --exam-types "名词解释,简答题,论述题,列举题,案例分析" --manual-login-timeout 120
```

复用已有数据，不重新爬取：

```powershell
python .\scripts\cvs_weekly_notes_exporter.py --from-data ".\outputs\weekly_xxx\weekly_data.json" --exam-types "名词解释,简答题,论述题,列举题,案例分析"
```

## 安全与合规边界

- 只用于用户本人有权限访问的课程。
- 不绕过登录、权限、付费或平台访问控制。
- 不要提交浏览器 profile、Cookie、JWT、原始课程数据、生成笔记、日志或媒体文件。
- 生成的课程材料默认应保持私有，除非用户确认有权分享。
- 源码中可以出现 `jwt-token` 这样的请求头名称，但不能出现真实 token 值。

提交或公开修改前，建议扫描敏感信息：

```powershell
rg -n "jwt-token|Authorization|Bearer|Cookie|password|token|SESSDATA|OPENAI_API_KEY|DASHSCOPE_API_KEY" -S .
```

## 许可证

MIT
