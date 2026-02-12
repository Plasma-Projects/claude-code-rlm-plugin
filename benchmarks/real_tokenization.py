#!/usr/bin/env python3
"""
Real tokenization counts per model using model-native tokenizers where possible.

- OpenAI: local tiktoken (no API key required)
- Anthropic: API count_tokens (requires ANTHROPIC_API_KEY)
- Gemini: google.generativeai count_tokens (requires GOOGLE_API_KEY)

Writes:
- benchmarks/real_tokenization_results.json
- benchmarks/real_tokenization_results.md
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


DEFAULT_FILES = [
    "benchmarks/test_data/large_dataset.json",
    "benchmarks/test_data/application.log",
    "benchmarks/test_data/large_dataset.csv",
]

DEFAULT_MODELS = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "claude-sonnet-4-5-20250929",
    "google/gemini-2.5-flash",
]


def read_content(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def normalize_model(model: str) -> Tuple[str, str]:
    if "/" in model:
        provider, name = model.split("/", 1)
        return provider.strip().lower(), name.strip()
    name = model.strip()
    if name.startswith("gpt-"):
        return "openai", name
    if name.startswith("claude-"):
        return "anthropic", name
    if name.startswith("gemini-"):
        return "google", name
    return "unknown", name


def count_tokens_openai(content: str, model: str) -> Tuple[Optional[int], str]:
    try:
        import tiktoken
    except Exception:
        return None, "tiktoken not installed"

    try:
        encoding = tiktoken.encoding_for_model(model)
        note = "encoding_for_model"
    except Exception:
        try:
            encoding = tiktoken.get_encoding("o200k_base")
            note = "fallback o200k_base"
        except Exception:
            return None, "tiktoken encoding unavailable"

    return len(encoding.encode(content)), note


def count_tokens_anthropic(content: str, model: str) -> Tuple[Optional[int], str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "ANTHROPIC_API_KEY not set"

    try:
        import anthropic
    except Exception:
        return None, "anthropic not installed"

    client = anthropic.Anthropic(api_key=api_key)
    try:
        result = client.messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": content}],
        )
        return int(result.input_tokens), "anthropic count_tokens"
    except Exception as exc:
        return None, f"anthropic count_tokens failed: {exc}"


def count_tokens_google(content: str, model: str) -> Tuple[Optional[int], str]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, "GOOGLE_API_KEY not set"

    try:
        import google.generativeai as genai
    except Exception:
        return None, "google.generativeai not installed"

    genai.configure(api_key=api_key)
    try:
        gmodel = genai.GenerativeModel(model)
        result = gmodel.count_tokens(content)
        tokens = getattr(result, "total_tokens", None)
        if tokens is None and isinstance(result, dict):
            tokens = result.get("total_tokens")
        if tokens is None:
            return None, "google count_tokens returned no total_tokens"
        return int(tokens), "google count_tokens"
    except Exception as exc:
        return None, f"google count_tokens failed: {exc}"


def count_tokens(content: str, model: str) -> Tuple[Optional[int], str, str]:
    provider, normalized = normalize_model(model)
    if provider == "openai":
        tokens, note = count_tokens_openai(content, normalized)
        return tokens, note, provider
    if provider == "anthropic":
        tokens, note = count_tokens_anthropic(content, normalized)
        return tokens, note, provider
    if provider == "google":
        tokens, note = count_tokens_google(content, normalized)
        return tokens, note, provider
    return None, "unsupported model/provider", provider


def build_markdown(results: Dict[str, Any]) -> str:
    models = results["models"]
    lines = []
    lines.append("# Real Tokenization Results")
    lines.append("")
    lines.append("Counts are produced using model-native tokenizers where available.")
    lines.append("")

    for file_path, data in results["files"].items():
        lines.append(f"## {file_path}")
        lines.append("")
        header = "| Model | Tokens | Method/Note |"
        sep = "| --- | --- | --- |"
        lines.extend([header, sep])
        for model in models:
            entry = data.get(model, {})
            tokens = entry.get("tokens")
            note = entry.get("note", "")
            token_str = f"{tokens:,}" if isinstance(tokens, int) else "N/A"
            lines.append(f"| {model} | {token_str} | {note} |")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", type=str, default=",".join(DEFAULT_FILES))
    parser.add_argument("--models", type=str, default=",".join(DEFAULT_MODELS))
    parser.add_argument("--output-json", type=str, default="benchmarks/real_tokenization_results.json")
    parser.add_argument("--output-md", type=str, default="benchmarks/real_tokenization_results.md")
    args = parser.parse_args()

    file_list = [f.strip() for f in args.files.split(",") if f.strip()]
    model_list = [m.strip() for m in args.models.split(",") if m.strip()]

    results: Dict[str, Any] = {
        "models": model_list,
        "files": {},
    }

    for file_path in file_list:
        path = Path(file_path)
        if not path.exists():
            continue
        content = read_content(path)
        results["files"][file_path] = {}
        for model in model_list:
            tokens, note, provider = count_tokens(content, model)
            results["files"][file_path][model] = {
                "tokens": tokens,
                "note": note,
                "provider": provider,
            }

    output_json = Path(args.output_json)
    output_json.write_text(json.dumps(results, indent=2))

    output_md = Path(args.output_md)
    output_md.write_text(build_markdown(results))

    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
