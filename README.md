# CVS Replay Notes Skill

`cvs-replay-notes` is a Codex skill for turning an authorized CVS course replay page into week-organized course notes and exam-type review material.

It is designed for school course replay systems that expose platform-generated AI learning data, such as summaries, segmented skims, mind maps, and transcripts. It does **not** bypass login, crack videos, or download replay media by default.

## What Users Give the Agent

For first-time export, give the agent a CVS `play-center` replay URL:

```text
Use this skill to export this CVS course replay and generate weekly notes:
https://cvs.seu.edu.cn/.../#/play-center?teclId=...&courseId=...&target=video
```

Optional scope and exam types:

```text
Use this skill. Weeks: all. Question types: 名词解释、简答题、论述题、列举题、案例分析.
URL: https://cvs.seu.edu.cn/.../#/play-center?teclId=...&courseId=...
```

If the course has already been exported, users can ask only for exam reorganization:

```text
Use this skill to reorganize the existing course data by 名词解释、简答题、论述题、列举题、案例分析.
```

The agent should reuse the newest `weekly_data.json` when one is available.

## How Another Agent Can Use It

Send the agent this repository link and ask it to install or use the skill:

```text
Please install/use the Codex skill from:
https://github.com/Verayi2007/cvs-replay-notes-skill
```

The repository root is the skill root. It contains:

```text
SKILL.md
agents/openai.yaml
references/principles.md
references/exam_planning.md
scripts/cvs_weekly_notes_exporter.py
```

If the agent cannot install skills automatically, it can still read `SKILL.md` and run the script directly.

## What It Crawls

The skill opens the CVS replay page in a local Chrome/Edge session and requests the same JSON data used by the official frontend:

```text
subject_vod_list_new
course/ai/textSummary/{courseId}
course/ai/summary/search/{courseId}
course/ai/translate/{courseId}
```

These endpoints provide:

- replay list, week number, lesson number, teacher, classroom, replay status;
- AI overview and key points;
- segmented classroom skims;
- mind-map nodes;
- transcript/translation segments with timestamps.

The best minimum input is the full `play-center` URL because it contains `teclId`. `teclId` lists the whole teaching-class replay set; `courseId` alone usually identifies only one lesson.

## Outputs

The exporter can generate:

```text
weekly_data.json       structured local data for reuse
raw/*.json             raw API responses, local/private
weekly_notes.md        notes organized by week and lesson
exam_type_review.md    likely exam points grouped by question type
```

`exam_type_review.md` is a review aid, not a guarantee of actual exam questions.

## Exam-Type Review Logic

The skill classifies candidate exam points from:

1. `keyPoints`
2. `fullOverview`
3. `documentSkims`
4. `mindmap.nodes`
5. `translate.afterAssemblyList`

It then weights them by source importance, repetition, and question-type signals:

- 名词解释: concept, definition, connotation, feature
- 简答题: function, cause, influence, method, principle
- 论述题: relationship, meaning, value, development, integration
- 列举题: type, classification, element, stage, method
- 案例分析: named examples, places, events, people, practices
- 比较题: similarities, differences, traditional/modern, Chinese/foreign

For STEM courses, the same workflow still works, but the exam-type rules should shift toward definitions, theorems, formulas, derivations, proofs, calculations, experiments, models, or algorithms.

## Direct Script Usage

Install the Python dependency:

```powershell
pip install websocket-client
```

Export all available weeks:

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks all --manual-login-timeout 120
```

Export selected weeks and generate exam-type review:

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks 9,11,12,13 --exam-types "名词解释,简答题,论述题,列举题,案例分析" --manual-login-timeout 120
```

Reuse existing data without crawling:

```powershell
python .\scripts\cvs_weekly_notes_exporter.py --from-data ".\outputs\weekly_xxx\weekly_data.json" --exam-types "名词解释,简答题,论述题,列举题,案例分析"
```

## Safety and Compliance

- Use only with courses the user is authorized to access.
- Do not bypass authentication, permissions, payment, or platform controls.
- Do not commit browser profiles, cookies, JWTs, raw course data, generated notes, logs, or media files.
- Keep generated course material private unless the user has permission to share it.
- The source code may contain header names such as `jwt-token`; it must not contain real token values.

Before publishing changes, scan for secrets:

```powershell
rg -n "jwt-token|Authorization|Bearer|Cookie|password|token|SESSDATA|OPENAI_API_KEY|DASHSCOPE_API_KEY" -S .
```

## License

MIT
