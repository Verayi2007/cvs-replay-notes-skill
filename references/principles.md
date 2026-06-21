# CVS Replay Notes: Principle Reference

## Boundary

This workflow automates the same data flow that an authorized browser session uses after a user logs into CVS. It must not be used to bypass authentication, guess identifiers, attack endpoints, or redistribute course materials.

## Architecture

The exporter starts a local Chrome or Edge instance with Chrome DevTools Protocol (CDP):

1. Launch browser with `--remote-debugging-port`.
2. Open the user-provided `#/play-center?...` URL.
3. Let the user log in manually if the session is not authenticated.
4. Run JavaScript inside that page context with `Runtime.evaluate`.
5. Use `fetch(..., credentials: "include")` so browser cookies and same-origin session state are honored.
6. Read the page's JWT from `sessionStorage` or `localStorage` only to attach the same `jwt-token` header the frontend uses.
7. Parse JSON responses and write local notes.

This is browser-session automation, not credential harvesting. Do not print, save, or commit token values.

## URL Parameters

Typical CVS replay URLs contain values such as:

- `teclId`: teaching class id. Used to list all replay records for that class.
- `courseId`: current lesson id. Used mainly for naming output and initial page context.
- `teclCode`, `subjId`, `target`: useful context but not required for the core weekly export.

Parse both the normal query string and the hash-fragment query because CVS uses a hash route.

For arbitrary courses, ask for the full play-center URL first. It is better than asking for separate ids because:

- it opens the correct authenticated origin;
- it usually contains `teclId`, which is required for listing all lessons;
- it contains a current `courseId`, useful for output naming and initial page navigation;
- it avoids asking non-technical users to inspect network parameters.

If a user cannot provide the URL, the fallback minimum is `teclId` plus a CVS page URL from the same platform origin.

## API Objects

Base URL:

```text
https://cvs.seu.edu.cn/jy-application-resourcemanage/v1
```

Important endpoints:

```text
/subject_vod_list_new?page.pageIndex=1&page.pageSize=1000&teclIds=<teclId>&page.orders[0].asc=false&page.orders[0].field=courBeginTime&schoolOpenStatusFlag=false
/course/ai/textSummary/<courseId>
/course/ai/summary/search/<courseId>
/course/ai/translate/<courseId>
/course_vod_urls_new?courseId=<courseId>
```

Fields to expect:

- Replay list: `data.records[]`, `id`, `weekNo`, `weekNumber`, `letiNumber`, `courBeginTime`, `vodStatus`, `teacNames`, `clroName`.
- Summary search: `data.fullOverview`, `data.keyPoints`, `data.documentSkims[]`.
- Text summary: `data.summary`, `data.mindmap.nodes[]`.
- Translate: `data.afterAssemblyList[]`, usually with `res` or `zh` text plus timestamp fields.

`vodStatus == 5` has been the useful filter for available replays in this workflow. Verify if platform behavior changes.

## Note Quality Rules

Good notes should:

- Be organized by actual week numbers from the platform.
- Keep each lesson separate inside the week.
- Extract concepts, definitions, classifications, examples, and teacher-emphasized cases.
- Use transcript segments as evidence, not as filler.
- Avoid third-person narration such as "老师讲了..." unless it preserves a specific classroom example.
- Mark uncertain or missing data clearly.

For exam-ready notes, first create detailed notes, then synthesize:

- likely question types,
- complete answer templates,
- listing题 answers,
- examples that can be reused across prompts.

## Exam-Type Prediction

Question-type prediction should be treated as weighted classification over course material:

1. collect candidate points from key points, full overview, document skims, mind-map nodes, and transcript snippets;
2. score them by source importance, repetition, and question-type keywords;
3. group them under the user's question types;
4. generate likely stems, answer frames, and evidence references.

The strongest signals are:

- appears in `keyPoints`;
- appears as a mind-map parent node;
- appears in multiple lessons/weeks;
- has a classroom example or named case;
- matches the requested question type, such as "类型/方法/阶段" for 列举题 or "关系/意义/影响" for 论述题.

Always label this as prediction or review guidance, not certainty.

## Tooling

Core dependencies:

- Python 3.9+
- `websocket-client` for CDP WebSocket calls
- Chrome or Edge
- Optional `python-docx` if generating DOCX after Markdown

Preferred validation:

- `py_compile` for scripts.
- Count weeks and lessons in `weekly_data.json`.
- `rg` scan for credentials before sharing.

## Failure Modes

- VPN breaks Codex network: run the browser/exporter locally through the user's VPN, keep Codex operations local when possible.
- Login timeout: rerun with `--manual-login-timeout 120` or longer.
- No records for a week: state that the platform returned no available replay for that week.
- Garbled Chinese: ensure files are read/written with UTF-8.
- API returns 401/403: ask the user to log in again; do not attempt bypasses.
