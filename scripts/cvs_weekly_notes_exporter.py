from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None


LOGGER = logging.getLogger("cvs_weekly_notes_exporter")
DEFAULT_API_BASE = "https://cvs.seu.edu.cn/jy-application-resourcemanage/v1"


class CDPClient:
    def __init__(self, websocket_url: str):
        if websocket is None:
            raise RuntimeError("Missing dependency: pip install websocket-client")
        self.ws = websocket.create_connection(websocket_url, timeout=5)
        self.next_id = 1

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass

    def send(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10) -> Dict[str, Any]:
        message_id = self.next_id
        self.next_id += 1
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.ws.settimeout(max(0.1, deadline - time.time()))
            try:
                message = json.loads(self.ws.recv())
            except Exception as exc:
                if exc.__class__.__name__ == "WebSocketTimeoutException":
                    break
                raise RuntimeError(f"CDP receive failed for {method}: {exc}") from exc
            if message.get("id") != message_id:
                continue
            if "error" in message:
                raise RuntimeError(f"CDP {method} failed: {message['error']}")
            return message.get("result", {})
        raise TimeoutError(f"Timed out waiting for CDP response: {method}")

    def pump(self, seconds: float) -> None:
        deadline = time.time() + seconds
        while time.time() < deadline:
            self.ws.settimeout(max(0.1, min(1.0, deadline - time.time())))
            try:
                self.ws.recv()
            except Exception:
                continue


class ChromeRunner:
    def __init__(self, chrome_path: Optional[str], user_data_dir: Path, port: int, headless: bool):
        self.chrome_path = chrome_path or find_chrome_path()
        self.user_data_dir = user_data_dir
        self.port = port
        self.headless = headless
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> None:
        if not self.chrome_path:
            raise RuntimeError("Chrome or Edge was not found. Pass --chrome-path.")
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        args = [
            self.chrome_path,
            f"--remote-debugging-port={self.port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-popup-blocking",
            "about:blank",
        ]
        if self.headless:
            args.insert(1, "--headless=new")
            args.insert(2, "--disable-gpu")
        LOGGER.info("Starting browser: %s", self.chrome_path)
        self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._wait_for_devtools()

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def new_page_websocket_url(self) -> str:
        target_url = f"http://127.0.0.1:{self.port}/json/new?about:blank"
        request = urllib.request.Request(target_url, method="PUT")
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        websocket_url = data.get("webSocketDebuggerUrl")
        if not websocket_url:
            raise RuntimeError("Browser did not return a page WebSocket URL.")
        return websocket_url

    def _wait_for_devtools(self) -> None:
        version_url = f"http://127.0.0.1:{self.port}/json/version"
        deadline = time.time() + 15
        last_error: Optional[Exception] = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(version_url, timeout=2) as response:
                    if response.status == 200:
                        return
            except Exception as exc:
                last_error = exc
                time.sleep(0.3)
        raise RuntimeError(f"Browser DevTools did not start: {last_error}")


def find_chrome_path() -> Optional[str]:
    candidates = [
        os.environ.get("CHROME_PATH"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        shutil.which("chrome.exe"),
        shutil.which("msedge.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def parse_url_params(url: str) -> Dict[str, str]:
    parsed = urllib.parse.urlparse(url)
    params: Dict[str, str] = {}

    def merge(query: str) -> None:
        for key, values in urllib.parse.parse_qs(query, keep_blank_values=True).items():
            if values:
                params[key] = values[0]

    merge(parsed.query)
    if "?" in parsed.fragment:
        merge(parsed.fragment.split("?", 1)[1])
    return params


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_weeks(text: str) -> Optional[List[int]]:
    if text.strip().lower() in {"", "all", "*", "全部", "所有"}:
        return None
    weeks: List[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            weeks.extend(range(int(left), int(right) + 1))
        else:
            weeks.append(int(part))
    return sorted(set(weeks))


def parse_exam_types(text: str) -> List[str]:
    separators = [",", "，", "、", ";", "；", "\n"]
    for sep in separators[1:]:
        text = text.replace(sep, separators[0])
    return [item.strip() for item in text.split(",") if item.strip()]


def fmt_seconds(value: Any) -> str:
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return str(value or "")
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def fmt_range(item: Dict[str, Any]) -> str:
    ranges = item.get("timeRanges")
    if ranges:
        return ", ".join(f"{fmt_seconds(r.get('start'))}-{fmt_seconds(r.get('end'))}" for r in ranges)
    time_text = item.get("time")
    if time_text:
        parts = str(time_text).split("-", 1)
        if len(parts) == 2:
            return f"{fmt_seconds(parts[0])}-{fmt_seconds(parts[1])}"
        return str(time_text)
    bg = item.get("bg")
    ed = item.get("ed")
    if bg is not None and ed is not None:
        return f"{fmt_seconds(int(bg) / 1000)}-{fmt_seconds(int(ed) / 1000)}"
    return ""


def truncate(text: str, limit: int = 240) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def normalize_text(text: str) -> str:
    return " ".join(str(text or "").split())


def week_of(course: Dict[str, Any]) -> int:
    return int(course["record"].get("weekNo") or course["record"].get("weekNumber") or 0)


def lesson_label(course: Dict[str, Any]) -> str:
    record = course["record"]
    week = week_of(course)
    lesson = record.get("letiNumber") or ""
    date = str(record.get("courBeginTime") or "")[:10]
    return f"第{week}周 第{lesson}节 {date}".strip()


def cdp_fetch_json(cdp: CDPClient, url: str, timeout: int = 20) -> Any:
    expression = f"""
(async () => {{
  const token =
    sessionStorage.getItem("jy-application-resourcemanage-ui_STORAGE_KEY_JWT_TOKEN") ||
    localStorage.getItem("jy-application-resourcemanage-ui_STORAGE_KEY_JWT_TOKEN") ||
    "";
  const headers = {{"Accept": "application/json, text/plain, */*"}};
  if (token) headers["jwt-token"] = token;
  const response = await fetch({json.dumps(url)}, {{
    method: "GET",
    credentials: "include",
    headers
  }});
  const text = await response.text();
  return {{ok: response.ok, status: response.status, url: response.url, text}};
}})()
"""
    result = cdp.send(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        timeout=timeout,
    )
    value = (result.get("result") or {}).get("value") or {}
    if not value.get("ok"):
        raise RuntimeError(f"Fetch failed {value.get('status')}: {url}\n{value.get('text', '')[:300]}")
    return json.loads(value.get("text") or "{}")


def subject_list_url(api_base: str, tecl_id: str) -> str:
    params = {
        "page.pageIndex": "1",
        "page.pageSize": "1000",
        "teclIds": tecl_id,
        "page.orders[0].asc": "false",
        "page.orders[0].field": "courBeginTime",
        "schoolOpenStatusFlag": "false",
    }
    return f"{api_base.rstrip('/')}/subject_vod_list_new?{urllib.parse.urlencode(params)}"


def endpoint_map(api_base: str, course_id: int) -> Dict[str, str]:
    base = api_base.rstrip("/")
    return {
        "text_summary": f"{base}/course/ai/textSummary/{course_id}",
        "summary_search": f"{base}/course/ai/summary/search/{course_id}",
        "translate": f"{base}/course/ai/translate/{course_id}",
    }


def collect_data(args: argparse.Namespace, output_dir: Path) -> Dict[str, Any]:
    params = parse_url_params(args.url)
    tecl_id = params.get("teclId")
    if not tecl_id:
        raise RuntimeError("URL is missing teclId.")
    chrome = ChromeRunner(
        chrome_path=args.chrome_path,
        user_data_dir=Path(args.user_data_dir).resolve(),
        port=args.port,
        headless=args.headless,
    )
    cdp: Optional[CDPClient] = None
    try:
        chrome.start()
        cdp = CDPClient(chrome.new_page_websocket_url())
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")
        cdp.send("Network.enable")
        LOGGER.info("Opening course page")
        cdp.send("Page.navigate", {"url": args.url}, timeout=10)
        cdp.pump(args.wait)
        if args.manual_login_timeout:
            LOGGER.info("Waiting %s seconds for manual login if needed", args.manual_login_timeout)
            cdp.pump(args.manual_login_timeout)
        raw_dir = output_dir / "raw"
        subject = cdp_fetch_json(cdp, subject_list_url(args.api_base, tecl_id))
        save_json(raw_dir / "subject_vod_list_new.json", subject)
        requested_weeks = parse_weeks(args.weeks)
        records = subject.get("data", {}).get("records", [])
        selected = [
            item
            for item in records
            if (requested_weeks is None or int(item.get("weekNo") or item.get("weekNumber") or -1) in requested_weeks)
            and (args.include_unavailable or int(item.get("vodStatus") or 0) == 5)
        ]
        selected.sort(key=lambda item: (int(item.get("weekNo") or 0), item.get("courBeginTime") or ""))
        selected_weeks = sorted({
            int(item.get("weekNo") or item.get("weekNumber") or 0)
            for item in selected
            if int(item.get("weekNo") or item.get("weekNumber") or 0)
        })
        courses = []
        for item in selected:
            course_id = int(item["id"])
            LOGGER.info("Fetching course %s, week %s", course_id, item.get("weekNo"))
            course_data = {"record": item, "courseId": course_id, "endpoints": {}}
            for name, endpoint in endpoint_map(args.api_base, course_id).items():
                try:
                    data = cdp_fetch_json(cdp, endpoint)
                    save_json(raw_dir / f"{course_id}_{name}.json", data)
                    course_data["endpoints"][name] = data
                except Exception as exc:
                    LOGGER.warning("%s failed for %s: %s", name, course_id, exc)
                    course_data["endpoints"][name] = {"__error__": str(exc)}
            courses.append(course_data)
        payload = {
            "sourceUrl": args.url,
            "teclId": tecl_id,
            "weeks": selected_weeks,
            "requestedWeeks": requested_weeks or "all",
            "recordsFound": len(records),
            "coursesSelected": len(courses),
            "generatedAt": dt.datetime.now().isoformat(timespec="seconds"),
            "courses": courses,
        }
        save_json(output_dir / "weekly_data.json", payload)
        return payload
    finally:
        if cdp:
            cdp.close()
        if not args.keep_browser_open:
            chrome.stop()


def get_summary(course: Dict[str, Any]) -> Dict[str, Any]:
    endpoints = course.get("endpoints", {})
    text_summary = endpoints.get("text_summary", {}).get("data") or {}
    search_summary = endpoints.get("summary_search", {}).get("data") or {}
    if search_summary.get("fullOverview") or search_summary.get("documentSkims"):
        return search_summary
    return text_summary.get("summary") or {}


def get_mindmap(course: Dict[str, Any]) -> Dict[str, Any]:
    return ((course.get("endpoints", {}).get("text_summary", {}).get("data") or {}).get("mindmap") or {})


def get_translate(course: Dict[str, Any]) -> Dict[str, Any]:
    return course.get("endpoints", {}).get("translate", {}).get("data") or {}


def render_mindmap(nodes: List[Dict[str, Any]], level: int = 0, max_level: int = 3) -> List[str]:
    lines: List[str] = []
    indent = "  " * level
    for node in nodes:
        label = node.get("label") or ""
        time_text = fmt_range(node)
        suffix = f" ({time_text})" if time_text else ""
        lines.append(f"{indent}- {label}{suffix}")
        children = node.get("children") or []
        if children and level + 1 < max_level:
            lines.extend(render_mindmap(children, level + 1, max_level))
    return lines


def transcript_sample(course: Dict[str, Any], limit: int = 8) -> List[str]:
    items = get_translate(course).get("afterAssemblyList") or []
    if not items:
        return []
    selected = items if len(items) <= limit else items[:: max(1, len(items) // limit)][:limit]
    lines = []
    for item in selected:
        text = item.get("res") or item.get("zh") or ""
        if text.strip():
            lines.append(f"- **{fmt_range(item)}** {truncate(text, 280)}")
    return lines


def iter_mindmap_labels(nodes: List[Dict[str, Any]]) -> Iterable[Tuple[str, str]]:
    for node in nodes:
        label = normalize_text(node.get("label") or "")
        if label:
            yield label, fmt_range(node)
        children = node.get("children") or []
        if children:
            yield from iter_mindmap_labels(children)


def collect_exam_candidates(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for course in payload.get("courses", []):
        summary = get_summary(course)
        mindmap = get_mindmap(course)
        record = course["record"]
        base = {
            "week": week_of(course),
            "lesson": lesson_label(course),
            "courseId": record.get("id"),
        }

        for point in summary.get("keyPoints") or []:
            text = normalize_text(point)
            if text:
                candidates.append({**base, "text": text, "source": "关键知识点", "weight": 5})

        overview = normalize_text(summary.get("fullOverview") or "")
        if overview:
            candidates.append({**base, "text": truncate(overview, 380), "source": "本节主线", "weight": 4})

        for skim in summary.get("documentSkims") or []:
            overview = normalize_text(skim.get("overview") or "")
            content = normalize_text(skim.get("content") or "")
            combined = "：".join(item for item in [overview, content] if item)
            if combined:
                candidates.append({
                    **base,
                    "text": truncate(combined, 420),
                    "source": f"分段课堂笔记 {fmt_range(skim)}".strip(),
                    "weight": 4,
                })

        for label, time_text in iter_mindmap_labels(mindmap.get("nodes") or []):
            candidates.append({
                **base,
                "text": label,
                "source": f"知识框架 {time_text}".strip(),
                "weight": 3,
            })

        for line in transcript_sample(course, limit=6):
            text = normalize_text(line.replace("**", ""))
            if text:
                candidates.append({**base, "text": truncate(text, 320), "source": "课堂原话摘录", "weight": 2})

    seen = set()
    unique: List[Dict[str, Any]] = []
    for item in candidates:
        key = (item["week"], item["text"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def exam_type_keywords(exam_type: str) -> List[str]:
    text = exam_type.lower()
    mapping = [
        (("名词", "解释", "概念", "定义"), ["概念", "定义", "内涵", "含义", "本质", "特征", "文化", "资源", "审美"]),
        (("简答", "简述", "问答"), ["特点", "作用", "功能", "原因", "影响", "意义", "方式", "路径", "原则", "要求"]),
        (("论述", "分析", "综合"), ["关系", "意义", "价值", "影响", "发展", "融合", "文化", "旅游", "机制", "逻辑"]),
        (("列举", "枚举", "举出"), ["类型", "分类", "包括", "要素", "方法", "阶段", "人物", "事件", "案例", "方式"]),
        (("案例", "材料", "情境"), ["案例", "例如", "比如", "景区", "城市", "酒店", "人物", "事件", "实践", "现象"]),
        (("比较", "辨析", "异同"), ["比较", "区别", "差异", "联系", "中外", "传统", "现代", "不同", "相同"]),
    ]
    for triggers, keywords in mapping:
        if any(trigger in text for trigger in triggers):
            return keywords
    return ["概念", "特点", "作用", "意义", "类型", "案例", "关系", "影响"]


def score_candidate(item: Dict[str, Any], exam_type: str) -> int:
    text = item["text"]
    keywords = exam_type_keywords(exam_type)
    score = int(item.get("weight") or 1)
    score += sum(3 for keyword in keywords if keyword in text)
    if "：" in text or ":" in text:
        score += 1
    if len(text) <= 80:
        score += 1
    if any(mark in text for mark in ["第一", "第二", "第三", "一是", "二是", "三是"]):
        score += 2
    return score


def question_stem(exam_type: str, text: str) -> str:
    topic = truncate(text.split("：", 1)[0].split(":", 1)[0], 36)
    if any(word in exam_type for word in ["名词", "解释"]):
        return f"解释“{topic}”的含义。"
    if any(word in exam_type for word in ["列举", "枚举"]):
        return f"列举与“{topic}”相关的主要类型、要素或方法。"
    if any(word in exam_type for word in ["案例", "材料", "情境"]):
        return f"结合课堂案例，分析“{topic}”体现的旅游文化问题。"
    if any(word in exam_type for word in ["比较", "辨析"]):
        return f"比较“{topic}”相关概念或现象的异同。"
    if any(word in exam_type for word in ["论述", "分析"]):
        return f"论述“{topic}”在课程中的意义、作用与现实启示。"
    return f"简答“{topic}”的核心内容。"


def answer_frame(exam_type: str) -> str:
    if any(word in exam_type for word in ["名词", "解释"]):
        return "定义/内涵 -> 关键特征 -> 课程例子 -> 一句话点明意义。"
    if any(word in exam_type for word in ["列举", "枚举"]):
        return "先总说分类标准 -> 分点列出 -> 每点补一句解释或课堂例子。"
    if any(word in exam_type for word in ["案例", "材料", "情境"]):
        return "概括材料现象 -> 对应课程概念 -> 展开原因/影响 -> 给出评价或启示。"
    if any(word in exam_type for word in ["比较", "辨析"]):
        return "分别定义 -> 找共同点 -> 分角度比较差异 -> 总结适用场景。"
    if any(word in exam_type for word in ["论述", "分析"]):
        return "提出中心论点 -> 分层展开机制/价值/影响 -> 嵌入课堂例子 -> 回到现实意义。"
    return "概念开头 -> 分点回答 -> 每点用课堂材料支撑 -> 简短总结。"


def render_exam_type_review(payload: Dict[str, Any], output_dir: Path, exam_types_text: str, limit: int = 12) -> Optional[Path]:
    exam_types = parse_exam_types(exam_types_text)
    if not exam_types:
        return None
    candidates = collect_exam_candidates(payload)
    lines = [
        "# 按题型整理的考点预测",
        "",
        "> 说明：这是基于 CVS 平台 AI 摘要、分段概要、思维导图和转写片段生成的复习辅助，不保证命题命中。",
        f"> 生成时间：{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for exam_type in exam_types:
        ranked = sorted(candidates, key=lambda item: score_candidate(item, exam_type), reverse=True)[:limit]
        lines.extend([f"## {exam_type}", "", f"**答题骨架：** {answer_frame(exam_type)}", ""])
        for index, item in enumerate(ranked, 1):
            lines.append(f"### {index}. {question_stem(exam_type, item['text'])}")
            lines.append("")
            lines.append(f"- **押题依据：** {item['source']}，{item['lesson']}")
            lines.append(f"- **可用考点：** {item['text']}")
            lines.append(f"- **答题提示：** 按“概念/观点 -> 分点展开 -> 课堂例子 -> 意义或评价”的顺序组织。")
            lines.append("")
    path = output_dir / "exam_type_review.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def render_course_note(course: Dict[str, Any]) -> List[str]:
    record = course["record"]
    summary = get_summary(course)
    mindmap = get_mindmap(course)
    key_points = summary.get("keyPoints") or []
    skims = summary.get("documentSkims") or []
    title = f"{record.get('courBeginTime', '')} 第{record.get('letiNumber', '')}节"
    lines = [f"### {title}", ""]
    lines.append(f"- 课程 ID：{record.get('id')}")
    lines.append(f"- 教师：{', '.join(record.get('teacNames') or [])}")
    lines.append(f"- 教室：{record.get('clroName') or ''}")
    lines.append("")
    overview = summary.get("fullOverview")
    if overview:
        lines.extend(["#### 本节主线", "", overview, ""])
    if key_points:
        lines.extend(["#### 关键知识点", ""])
        lines.extend(f"- {point}" for point in key_points)
        lines.append("")
    if skims:
        lines.extend(["#### 分段课堂笔记", ""])
        for skim in skims:
            lines.extend([f"##### {fmt_range(skim)} {skim.get('overview', '')}", ""])
            if skim.get("content"):
                lines.extend([skim.get("content", ""), ""])
    nodes = mindmap.get("nodes") or []
    if nodes:
        lines.extend(["#### 知识框架", ""])
        lines.extend(render_mindmap(nodes))
        lines.append("")
    examples = transcript_sample(course)
    if examples:
        lines.extend(["#### 课堂原话摘录", ""])
        lines.extend(examples)
        lines.append("")
    return lines


def render_weekly_notes(payload: Dict[str, Any], output_dir: Path) -> Path:
    courses = payload["courses"]
    by_week: Dict[int, List[Dict[str, Any]]] = {}
    for course in courses:
        week = int(course["record"].get("weekNo") or course["record"].get("weekNumber") or 0)
        by_week.setdefault(week, []).append(course)
    for values in by_week.values():
        values.sort(key=lambda item: item["record"].get("courBeginTime") or "")
    lines = [
        "# CVS 课程回放按周笔记",
        "",
        f"> 生成时间：{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 来源链接：{payload.get('sourceUrl')}",
        f"> 周次：{', '.join(str(item) for item in payload.get('weeks', []))}",
        "",
    ]
    all_points: List[str] = []
    for course in courses:
        all_points.extend(get_summary(course).get("keyPoints") or [])
    unique_points = list(dict.fromkeys(point for point in all_points if point))
    if unique_points:
        lines.extend(["## 总复习关键词", ""])
        lines.extend(f"- {point}" for point in unique_points)
        lines.append("")
    for week in sorted(by_week):
        week_courses = by_week[week]
        lines.extend([f"## 第{week}周", ""])
        dates = [item["record"].get("courBeginTime", "")[:10] for item in week_courses if item["record"].get("courBeginTime")]
        if dates:
            lines.append(f"- 日期：{', '.join(sorted(set(dates)))}")
        lines.extend([f"- 课时数：{len(week_courses)}", ""])
        week_points: List[str] = []
        for course in week_courses:
            week_points.extend(get_summary(course).get("keyPoints") or [])
        week_points = list(dict.fromkeys(point for point in week_points if point))
        if week_points:
            lines.extend(["### 本周知识点总览", ""])
            lines.extend(f"- {point}" for point in week_points)
            lines.append("")
        for course in week_courses:
            lines.extend(render_course_note(course))
    notes_path = output_dir / "weekly_notes.md"
    notes_path.write_text("\n".join(lines), encoding="utf-8")
    return notes_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export week-organized notes from authorized CVS replay AI data.")
    parser.add_argument("url", nargs="?", help="CVS play-center URL")
    parser.add_argument("--from-data", help="Existing weekly_data.json; skips browser crawling")
    parser.add_argument("--weeks", default="all", help="Weeks to include, e.g. all, 9-15, or 9,11,12,13")
    parser.add_argument("-o", "--output", default="./outputs", help="Output base directory")
    parser.add_argument("--exam-types", default="", help="Optional question types, e.g. 名词解释,简答题,论述题,列举题,案例分析")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="CVS API base URL")
    parser.add_argument("--manual-login-timeout", type=int, default=90, help="Seconds to wait for manual login")
    parser.add_argument("--headless", action="store_true", help="Run browser without a visible window")
    parser.add_argument("--include-unavailable", action="store_true")
    parser.add_argument("--keep-browser-open", action="store_true")
    parser.add_argument("--user-data-dir", default="./.cvs-chrome-profile")
    parser.add_argument("--chrome-path")
    parser.add_argument("--port", type=int, default=9230)
    parser.add_argument("--wait", type=float, default=12)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.from_data:
        data_path = Path(args.from_data).resolve()
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        output_dir = data_path.parent if args.output == "./outputs" else Path(args.output).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        if not args.url:
            parser.error("url is required unless --from-data is provided")
        params = parse_url_params(args.url)
        course_id = params.get("courseId", "unknown")
        output_dir = Path(args.output).resolve() / f"weekly_{course_id}_{stamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = collect_data(args, output_dir)
    notes_path = render_weekly_notes(payload, output_dir)
    LOGGER.info("Wrote notes to %s", notes_path)
    exam_path = render_exam_type_review(payload, output_dir, args.exam_types)
    if exam_path:
        LOGGER.info("Wrote exam type review to %s", exam_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
