---
name: final-exam-cram
description: Export and organize authorized CVS/东南大学课程回放学习数据 into week-by-week notes and exam-type review material. Use when the user asks for 期末速成, crawl,抓取,导出,整理,总结,押题,按题型整理考点, or复盘 CVS course replay pages, especially URLs under cvs.seu.edu.cn play-center; includes the safe browser-login/CDP workflow, exact AI-summary/transcript APIs, compliance boundaries, and note-generation steps.
---

# 期末速成

Use this skill to turn an authorized CVS course replay page into usable week-by-week course notes, then optionally reorganize the material by exam question type for final-exam review.

## Safety First

- Treat CVS as an authenticated school platform. Only work with courses the user can access.
- Do not bypass login, payment, permission checks, or platform access controls.
- Do not upload or commit browser profiles, cookies, JWTs, raw API responses, videos, generated notes, or logs unless the user explicitly requests and the target is private.
- Prefer exporting platform-provided AI learning data: summaries, segment skims, mind maps, and transcripts. Do not download replay videos unless the user explicitly asks and has permission.
- If preparing code for GitHub, keep it private by default when it names a school domain or course platform.

## What Is Crawled

Read `references/principles.md` when the user asks for the mechanism, asks whether it is safe/allowed, or wants documentation.

In short, this workflow does not scrape screen pixels or crack video streams. It opens the CVS `play-center` page in a controlled Chrome session, then requests the JSON endpoints that the official page already uses:

- `subject_vod_list_new`: list replay records for a teaching class, including week number, lesson number, date, replay status, teacher, and course id.
- `course/ai/textSummary/{courseId}`: platform AI summary, mind map, and sometimes key points.
- `course/ai/summary/search/{courseId}`: richer full overview and segmented classroom skims when available.
- `course/ai/translate/{courseId}`: transcript/translation segments with timestamps.
- Optional: `course_vod_urls_new?courseId=...` only when checking media availability; avoid saving media URLs in public artifacts.

## User Inputs

Minimum input for any course:

- **CVS play-center URL**. This is the best single input because it contains `teclId` and opens the correct authenticated page origin. Any replay URL from the target teaching class is enough; the exporter uses `teclId` to list all available replay records.

Minimum input after a course has already been exported:

- **Exam question types only**, if a recent `weekly_data.json` is already available in the workspace. Reuse that file with `--from-data` and skip browser crawling.

Useful optional inputs:

- **Weeks/scope**: `all`, `1-16`, or `9,11,12,13`. Default to `all` for arbitrary courses.
- **Exam question types**: natural language such as `名词解释, 简答题, 论述题, 列举题, 案例分析, 比较题`.
- **Course name / exam scope / teacher hints**: use only for file naming and prioritization; do not invent unavailable weeks or content.

If the user only provides `courseId`, ask for a full play-center URL or `teclId`. `courseId` alone identifies one lesson, but `teclId` is what lists the whole course/teaching-class replay set.

## Workflow

1. Inspect local files before crawling.
   - Reuse an existing clean exporter script if present, such as `cvs-weekly-notes-exporter/src/cvs_weekly_notes_exporter.py` or this skill's `scripts/cvs_weekly_notes_exporter.py`.
   - Check `.gitignore` before generating data.

2. Run the exporter with a visible browser on first use.
   - Use the user's real CVS play-center URL.
   - Ask the user to log in manually in the opened browser if needed.
   - Keep the browser profile local and ignored, for example `.cvs-chrome-profile/`.

3. Select replay records by week.
   - Use `weekNo`/`weekNumber` from `subject_vod_list_new`.
   - Include only records with `vodStatus == 5` unless the user asks to inspect unavailable records.
   - Preserve two lessons per week when present. Do not invent a missing week.

4. Fetch AI learning data per selected `courseId`.
   - Save raw JSON only inside an ignored local output directory.
   - Prefer `summary/search` over `textSummary.summary` when it has `fullOverview` or `documentSkims`.
   - Use `translate.afterAssemblyList` for timestamped examples and transcript evidence.

5. Generate notes.
   - Organize by week, then by lesson/date.
   - Write knowledge-point notes, not a third-person diary of what the teacher did.
   - Include timestamps for segmented knowledge points when available.
   - For open-book exam notes, add answer-ready sections only after detailed weekly notes exist.

6. Optionally generate exam-type review.
   - Use `--exam-types` when the user gives question types.
   - Classify candidates from key points, segment skims, mind maps, and transcript samples.
   - Present results as predictions with basis, not guaranteed exam answers.
   - Read `references/exam_planning.md` when designing richer exam-ready documents.

7. Validate before delivery.
   - Count selected weeks and lessons against `subject_vod_list_new`.
   - Confirm missing weeks explicitly, e.g. "第10周无可用回放".
   - Scan outputs for real tokens/cookies before sharing or committing.

## Commands

Use the bundled script when no project-specific exporter is available:

```powershell
python .\scripts\cvs_weekly_notes_exporter.py "<CVS play-center URL>" --weeks all --manual-login-timeout 120
```

Reclassify existing data by exam question type without crawling again:

```powershell
python .\scripts\cvs_weekly_notes_exporter.py --from-data ".\outputs\weekly_xxx\weekly_data.json" --exam-types "名词解释,简答题,论述题,列举题,案例分析"
```

Useful options:

```text
--weeks 9-15
--from-data ".\outputs\weekly_xxx\weekly_data.json"
--exam-types "名词解释,简答题,论述题,列举题,案例分析"
--output outputs
--manual-login-timeout 120
--headless
--user-data-dir ./.cvs-chrome-profile
--chrome-path "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

## Output Expectations

- `weekly_data.json`: structured local data for follow-up processing.
- `raw/*.json`: raw local API responses; keep ignored/private.
- `weekly_notes.md`: week-organized notes.
- `exam_type_review.md`: generated only when `--exam-types` is provided.
- Optional DOCX: use the document tooling only after the Markdown content is correct.

## GitHub Hygiene

If the user wants to publish the tool:

- Publish only code, README, license, and safe examples.
- Add `.gitignore` for `.cvs-chrome-profile/`, `outputs/`, `raw/`, `weekly_data.json`, videos, docx notes, logs, `.env`, cookies, and token-like files.
- Run a sensitive scan before commit:

```powershell
rg -n "jwt-token|Authorization|Bearer|Cookie|password|token|SESSDATA|OPENAI_API_KEY|DASHSCOPE_API_KEY" -S .
```

It is acceptable for source code to contain literal header names such as `jwt-token`; it is not acceptable to contain real token values.
