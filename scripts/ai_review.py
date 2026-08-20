"""Call a frontier model via OpenRouter for code review, planning, or debugging.

Ported from Windwright (2026-08-20 governance parity check) -- generic
mechanism, only the docstring examples and the referer/title fallbacks
were project-specific.

Usage:
    # High-level architecture review
    python scripts/ai_review.py --prompt docs/AI_REVIEW_PROMPT.md \
        --files src/guardrail/core/runner.py \
        --model nvidia/nemotron-3-super-120b-a12b:free \
        --output docs/AI_REVIEW_NEMOTRON_3_SUPER_120B_OPENROUTER.md

    # Planning session
    python scripts/ai_review.py --prompt docs/AI_PLANNING_PROMPT.md \
        --model nvidia/nemotron-3-super-120b-a12b:free \
        --output docs/PLAN_2026-08-20.md

    # Debug a specific file
    python scripts/ai_review.py --prompt docs/AI_DEBUG_PROMPT.md \
        --files scripts/compliance_watchdog.py \
        --model nvidia/nemotron-3-super-120b-a12b:free

    # List available models
    python scripts/ai_review.py --list-models

Environment:
    OPENROUTER_API_KEY - required. Read from environment.
    OPENROUTER_REFERER - optional site URL for rankings (default: this
                          repo's own GitHub URL, auto-detected).
    OPENROUTER_TITLE   - optional site title for rankings (default:
                          .guardrail.json's project_name, or "lawkeeper").
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _default_referer() -> str:
    """This repo's own GitHub URL, auto-detected -- never another
    project's hardcoded URL (same pattern as team_chat.py's repo
    detection)."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        url = result.stdout.strip()
        if url.startswith("git@"):
            url = url.replace(":", "/").replace("git@", "https://")
        return url.removesuffix(".git") or "https://github.com/unknown/unknown"
    except OSError:
        return "https://github.com/unknown/unknown"


def _default_title() -> str:
    """.guardrail.json's project_name, or 'lawkeeper' if unset/absent."""
    try:
        path = Path(".guardrail.json")
        if path.exists():
            cfg = json.loads(path.read_text(encoding="utf-8"))
            return str(cfg.get("project_name", "lawkeeper"))
    except (OSError, ValueError):
        pass
    return "lawkeeper"
MODELS_URL = "https://openrouter.ai/api/v1/models"


def get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("ERROR: OPENROUTER_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    return key


def list_models():
    key = get_api_key()
    resp = requests.get(MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    if resp.status_code != 200:
        print(f"ERROR listing models: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    for m in sorted(data.get("data", []), key=lambda x: x.get("id", "")):
        mid = m.get("id", "?")
        ctx = m.get("context_length", "?")
        pricing = m.get("pricing", {})
        prompt_price = pricing.get("prompt", "?")
        print(f"{mid:60s} context={ctx:>10}  prompt=${prompt_price}/1k")


def read_file(path: str, max_chars: int = 12000) -> str:
    p = Path(path)
    if not p.is_file():
        return f"[file not found: {path}]\n"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"[could not read {path}: {e}]\n"
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[... truncated at {max_chars} chars; total {len(text)} chars]"
    return f"### {path}\n```python\n{text}\n```\n\n"


def build_user_message(prompt_path: str, files: list[str]) -> str:
    prompt = Path(prompt_path).read_text(encoding="utf-8", errors="replace")
    parts = [prompt]
    if files:
        parts.append("## Source Files\n")
        for f in files:
            parts.append(read_file(f))
    return "\n\n".join(parts)


DEFAULT_SYSTEM_PROMPT = "You are a senior Python code reviewer and musical instrument acoustics expert."


def call_model(model: str, user_message: str, max_tokens: int = 4000, timeout: int = 300,
                system_prompt: str = DEFAULT_SYSTEM_PROMPT, max_retries: int = 3) -> str:
    key = get_api_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", _default_referer()),
        "X-Title": os.environ.get("OPENROUTER_TITLE", _default_title()),
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": max_tokens,
    }
    # Free-tier OpenRouter models share a rate-limited pool across all
    # users -- a 429 there is a real, expected, transient condition (found
    # by actually running this against real free models, not assumed), not
    # a broken model id. Retry with backoff; anything else fails immediately.
    #
    # Some providers (Kimi/Moonshot observed directly -- user's own real
    # experience, not a guess) signal the same "shared pool is full, try
    # again shortly" condition inside a 200 response body instead of a 429
    # status code -- phrased as "high demand" / "please try again" text
    # rather than an HTTP-level retry signal. Treat that the same way: it's
    # not a broken model or a real answer, it's the same transient
    # congestion under a different provider's wording.
    _SOFT_RATE_LIMIT_PHRASES = ("high demand", "please try again", "try again later",
                                 "too many requests", "temporarily unavailable")
    start = time.time()
    resp = None
    for attempt in range(max_retries):
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
        soft_limited = (
            resp.status_code == 200
            and any(p in resp.text.lower() for p in _SOFT_RATE_LIMIT_PHRASES)
        )
        if resp.status_code != 429 and not soft_limited:
            break
        if attempt < max_retries - 1:
            wait = 2 ** attempt
            reason = "429 (rate-limited)" if resp.status_code == 429 else "soft rate-limit text in a 200 response"
            print(f"OpenRouter {reason} for {model}, retrying in {wait}s "
                  f"(attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
    elapsed = time.time() - start
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    try:
        review = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        # Found live (Law 23): status 200 with a body missing the expected
        # shape is a real, if intermittent, upstream condition -- a bare
        # KeyError like "'choices'" told the caller nothing useful about
        # what actually came back.
        raise RuntimeError(
            f"OpenRouter returned 200 but the response body was missing "
            f"{exc!r}: {json.dumps(data)[:500]}"
        ) from exc
    usage = data.get("usage", {})
    print(f"Model response received in {elapsed:.1f}s (prompt_tokens={usage.get('prompt_tokens')}, completion_tokens={usage.get('completion_tokens')})")
    return review


def main():
    parser = argparse.ArgumentParser(description="Frontier AI review/debug helper via OpenRouter")
    parser.add_argument("--prompt", help="Path to the markdown prompt file")
    parser.add_argument("--files", nargs="+", default=[], help="Source files to include in the prompt")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model ID")
    parser.add_argument("--output", help="Path to write the review output")
    parser.add_argument("--max-tokens", type=int, default=4000, help="Maximum completion tokens")
    parser.add_argument("--timeout", type=int, default=300, help="Request timeout in seconds")
    parser.add_argument("--list-models", action="store_true", help="List available OpenRouter models")
    args = parser.parse_args()

    if args.list_models:
        list_models()
        return 0

    if not args.prompt:
        parser.error("--prompt is required (unless --list-models)")

    if not Path(args.prompt).is_file():
        print(f"ERROR: prompt file not found: {args.prompt}", file=sys.stderr)
        return 1

    user_message = build_user_message(args.prompt, args.files)
    print(f"Calling {args.model} with {len(user_message)} characters...")
    review = call_model(args.model, user_message, max_tokens=args.max_tokens, timeout=args.timeout)

    review = f"""<!-- Generated by scripts/ai_review.py -->
<!-- Model: {args.model} -->
<!-- Prompt: {args.prompt} -->
<!-- Files: {', '.join(args.files) or '(none)'} -->
<!-- Time: {datetime.now(timezone.utc).isoformat()} -->

{review}
"""

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(review, encoding="utf-8")
        print(f"Saved review to {out_path}")
    else:
        print(review)
    return 0


if __name__ == "__main__":
    sys.exit(main())
