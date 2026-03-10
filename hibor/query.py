#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any

import requests


CHAT_URL = "https://llmai.hibor.com.cn/project/hibor/api/agent/yanbao_qa_new/chat_stream"
DEFAULT_PAGE_URL = (
    "https://win.hibor.com.cn/AIQA/?abc=0YWZwPsPpOsMtNtPzRvNwP"
    "&def=sQrRnPrPlOmMoNkPrRuN9PrQsRvPnMmMvPrRqQ&vidd=51&keyy=EXGTIU844"
    "&xyz=tQsRxPmPqOrMqN&op=0&ver=3.9.9.0"
)
DEFAULT_USER_NAME = "HM951664889"
DEFAULT_ENGINE = "original"
MODEL_TO_ENGINE = {
    "hibor": "original",
    "deepseek": "reason",
}

THINK_OPEN = "<think>"
THINK_CLOSE = "</think>"
CITE_MARKER_RE = re.compile(r"\[\[id\d+\]\]")


@dataclass
class HiborResult:
    question: str
    thinking: str = ""
    answer: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    raw_chunks: list[dict[str, Any]] = field(default_factory=list)


def build_payload(question: str, user_name: str, engine: str, history: list[dict[str, str]] | None) -> dict[str, Any]:
    return {
        "user_name": user_name,
        "question": question,
        "show_source": True,
        "history": history,
        "date_filter": "auto",
        "start_date": None,
        "end_date": None,
        "aiqa_type": "aiqa_zh",
        "engine": engine,
        "use_short_id": True,
    }


def strip_cite_markers(text: str) -> str:
    cleaned = CITE_MARKER_RE.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_stream_line(raw_line: str) -> str:
    line = raw_line.strip()
    if not line:
        return ""
    if line.startswith("data:"):
        line = line[5:].strip()
    return line


def stream_query(
    question: str,
    user_name: str,
    engine: str,
    history: list[dict[str, str]] | None = None,
    verbose: bool = False,
) -> HiborResult:
    payload = build_payload(question=question, user_name=user_name, engine=engine, history=history)
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Origin": "https://win.hibor.com.cn",
        "Referer": "https://win.hibor.com.cn/AIQA/",
    }

    response = requests.post(
        CHAT_URL,
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        stream=True,
        timeout=180,
    )
    response.raise_for_status()

    result = HiborResult(question=question)
    text_buffer = ""
    saw_think_open = False
    saw_think_close = False

    for raw_line in response.iter_lines(decode_unicode=True):
        line = normalize_stream_line(raw_line)
        if not line:
            continue

        try:
            packet = json.loads(line)
        except json.JSONDecodeError:
            if verbose:
                print(f"\n[ignored-stream-line] {line}", file=sys.stderr)
            continue
        result.raw_chunks.append(packet)

        if "documents" in packet:
            result.sources = [
                {
                    "doc_id": item.get("ID"),
                    "sid": item.get("sid"),
                    "title": item.get("标题"),
                    "date": item.get("日期"),
                    "type": item.get("类型"),
                    "publisher": item.get("发布机构"),
                    "author": item.get("作者"),
                }
                for item in packet.get("documents", [])
            ]
            if verbose:
                print(f"[documents] {len(result.sources)} source(s)", file=sys.stderr)
            continue

        piece = packet.get("data", "")
        if not piece:
            continue

        text_buffer += piece
        if verbose:
            print(piece, end="", file=sys.stderr, flush=True)

        if THINK_OPEN in text_buffer:
            saw_think_open = True
        if THINK_CLOSE in text_buffer:
            saw_think_close = True

    if saw_think_open and saw_think_close:
        think_start = text_buffer.index(THINK_OPEN) + len(THINK_OPEN)
        think_end = text_buffer.index(THINK_CLOSE)
        result.thinking = text_buffer[think_start:think_end].strip()
        result.answer = text_buffer[think_end + len(THINK_CLOSE):].strip()
    else:
        result.answer = text_buffer.strip()

    result.answer = strip_cite_markers(result.answer)
    result.thinking = strip_cite_markers(result.thinking)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query the Hibor AI research assistant stream API.")
    parser.add_argument("question", help="Question to ask Hibor")
    parser.add_argument("--user-name", default=DEFAULT_USER_NAME, help="Hibor user_name parameter")
    parser.add_argument(
        "--model",
        choices=sorted(MODEL_TO_ENGINE),
        help="Friendly model switch: hibor -> original, deepseek -> reason",
    )
    parser.add_argument("--engine", default=DEFAULT_ENGINE, help="Engine parameter, e.g. reason/original")
    parser.add_argument("--history-json", help="Optional JSON array with [{role, content}, ...]")
    parser.add_argument("--page-url", default=DEFAULT_PAGE_URL, help="Source Hibor AIQA page URL for provenance")
    parser.add_argument("--pretty", action="store_true", help="Print a human-readable summary instead of raw JSON")
    parser.add_argument("--verbose-stream", action="store_true", help="Echo streamed text to stderr while collecting")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    history = json.loads(args.history_json) if args.history_json else None
    engine = MODEL_TO_ENGINE.get(args.model, args.engine)
    result = stream_query(
        question=args.question,
        user_name=args.user_name,
        engine=engine,
        history=history,
        verbose=args.verbose_stream,
    )

    if args.pretty:
        print(f"Question: {result.question}")
        print(f"Page URL: {args.page_url}")
        print(f"Model: {args.model or 'hibor'}")
        print(f"Engine: {engine}")
        print("")
        if result.thinking:
            print("Thinking:")
            print(result.thinking)
            print("")
        print("Answer:")
        print(result.answer)
        print("")
        print(f"Sources: {len(result.sources)}")
        for index, source in enumerate(result.sources, start=1):
            title = source.get("title") or ""
            publisher = source.get("publisher") or ""
            date = source.get("date") or ""
            print(f"{index}. {title} | {publisher} | {date}")
        return 0

    print(
        json.dumps(
            {
                "question": result.question,
                "page_url": args.page_url,
                "model": args.model or "hibor",
                "engine": engine,
                "thinking": result.thinking,
                "answer": result.answer,
                "sources": result.sources,
                "raw_chunks": result.raw_chunks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
