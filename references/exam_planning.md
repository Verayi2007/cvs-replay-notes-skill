# Exam-Type Planning

## Goal

Turn replay-derived weekly notes into exam-oriented review material after the data has already been collected. This is a prediction aid, not a promise of actual exam questions.

## Minimal User Input

Ask for the user's exam question types. Accept loose natural language:

```text
名词解释、简答题、论述题、列举题、案例分析、比较题
```

Optional but useful:

- exam scope, such as weeks or chapters;
- known teacher hints;
- scoring format, such as "5道简答+2道论述";
- whether the output should be "速查版" or "完整答案版".

Do not require the user to design a schema. Parse natural-language type names.

If the user gives only question types, first search the workspace for the newest `weekly_data.json`. If exactly one good candidate is found, use it. If several courses exist, ask which course/output directory to use. If none exists, ask for the CVS play-center URL and crawl first.

## Classification Sources

Use these fields in descending priority:

1. `summary.keyPoints`
2. `summary_search.fullOverview`
3. `summary_search.documentSkims`
4. `textSummary.mindmap.nodes`
5. `translate.afterAssemblyList`

Give more weight to repeated concepts, key points, mind-map parent nodes, and content that appears in multiple weeks.

## Type Heuristics

- 名词解释: concepts, definitions, connotations, short key terms, "内涵/概念/本质/特征".
- 简答题: functions, characteristics, causes, influence, meaning, principles, methods.
- 论述题: broad relationships, development logic, cultural meaning, value, integration, real-world implication.
- 列举题: classifications, types, elements, stages, methods, people, events, examples.
- 案例分析: classroom examples, named places, events, people, policies, hotels, scenic spots, cultural practices.
- 比较题: paired concepts, "中外/传统与现代/相同与不同/差异/联系".

## Output Shape

For each question type, produce:

- likely question stem;
- prediction basis: week, lesson, source field, repeated signal if available;
- usable answer material;
- answer frame;
- optional full answer if the user asks for open-book exam notes.

Keep wording honest:

- Say "高频考点/可能考法/押题依据".
- Avoid "一定会考".
- Mark thin evidence as "弱依据".

## Full-Answer Expansion

When the user wants complete open-book answers, expand each predicted point into:

1. direct answer;
2. definition or core concept;
3. 3-5 structured subpoints;
4. classroom example;
5. concluding sentence that returns to course theme.

For listing questions, include enough items to survive partial recall, but keep them grouped and scannable.
