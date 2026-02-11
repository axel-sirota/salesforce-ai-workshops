#!/usr/bin/env python3
"""
Build Session 6 notebook by PARSING the plan file.

Reads plans/workshop1/notebook/SESSION6_NOTEBOOK_PROGRESS.md,
extracts cell contents from markdown code blocks, applies
Gemini->OpenAI transformations, and writes the notebook JSON.
"""

import json
import re
import os

PLAN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plans", "workshop1", "notebook", "SESSION6_NOTEBOOK_PROGRESS.md")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exercises", "session_06", "session_06_prompt_tdd.ipynb")

CHART_BASE = "https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_06/charts"


def parse_cells_from_plan(plan_text):
    """Parse cell definitions from the plan markdown file."""
    cells = []

    # Pattern: ### Cell N - TYPE: Description
    # Followed by a code block with the cell content
    cell_pattern = re.compile(
        r'### Cell (\d+) - (MARKDOWN|CODE): (.+?)\n\n```(?:markdown|python)\n(.*?)```',
        re.DOTALL
    )

    for match in cell_pattern.finditer(plan_text):
        cell_num = int(match.group(1))
        cell_type = match.group(2).lower()
        description = match.group(3).strip()
        source = match.group(4)

        # Remove trailing newline if present
        if source.endswith('\n'):
            source = source[:-1]

        cells.append({
            "cell_num": cell_num,
            "cell_type": cell_type if cell_type == "markdown" else "code",
            "description": description,
            "source": source
        })

    return cells


def apply_transformations(cells):
    """Apply Gemini->OpenAI and SVG URL transformations."""
    for cell in cells:
        src = cell["source"]

        # 1. Fix SVG URLs: relative charts/ -> absolute GitHub URLs
        src = re.sub(
            r'!\[([^\]]*)\]\(charts/(\d{2}_[^)]+\.svg)\)',
            lambda m: '![' + m.group(1) + '](' + CHART_BASE + '/' + m.group(2) + ')',
            src
        )

        # 2. Remove google-generativeai from install
        src = src.replace(" google-generativeai>=0.8.0", "")

        # 3. Remove GEMINI_API_KEY from credentials
        lines = src.split('\n')
        filtered_lines = []
        for line in lines:
            if 'GEMINI_API_KEY' in line:
                continue
            filtered_lines.append(line)
        src = '\n'.join(filtered_lines)

        # 4. Replace GeminiModel imports and usage
        src = src.replace("from deepeval.models import GeminiModel\n", "")
        src = src.replace("from deepeval.models import GeminiModel", "")
        src = re.sub(
            r'judge_model = GeminiModel\(model="gemini-2\.0-flash", api_key=GEMINI_API_KEY\)',
            'judge_model = "gpt-4o"',
            src
        )
        src = src.replace('model=judge_model', 'model="gpt-4o"')

        # 5. Replace Gemini Flash references in text
        src = src.replace("G-Eval with Gemini Flash", "G-Eval with GPT-4o")
        src = src.replace("G-Eval + Gemini Flash", "G-Eval + GPT-4o")
        src = src.replace("Gemini Flash", "GPT-4o")
        src = src.replace("Gemini 2.0 Flash", "GPT-4o")
        src = src.replace("gemini-2.0-flash", "gpt-4o")

        # 6. Fix "Why Gemini as Judge" narrative
        src = src.replace("Why Use a Different Model as Judge?", "Why GPT-4o as Judge?")
        src = src.replace("Why Gemini as Judge", "Why GPT-4o as Judge")

        # Fix cross-model evaluation references
        src = src.replace(
            "**Cross-model evaluation** (Gemini judges GPT)",
            "**Stronger-model evaluation** (GPT-4o judges GPT-4o-mini)"
        )
        src = src.replace(
            "We use **Gemini Flash** to judge **GPT-4o-mini** outputs. Why not use GPT-4o-mini to judge itself?",
            "We use **GPT-4o** to judge **GPT-4o-mini** outputs. Why not use GPT-4o-mini to judge itself?"
        )
        src = src.replace(
            "We use **GPT-4o** to judge **GPT-4o-mini** outputs. Why not use GPT-4o-mini to judge itself?",
            "We use **GPT-4o** to judge **GPT-4o-mini** outputs. Why not use GPT-4o-mini to judge itself?"
        )

        # 7. Gemini Flash -> GPT-4o in stack descriptions
        src = src.replace(
            "**Judge model:** Gemini 2.0 Flash (fast, cheap, good at evaluation)",
            "**Judge model:** GPT-4o (stronger model evaluates weaker model's outputs)"
        )
        src = src.replace(
            "**Judge model:** GPT-4o (fast, cheap, good at evaluation)",
            "**Judge model:** GPT-4o (stronger model evaluates weaker model's outputs)"
        )

        # 8. Fix remaining Gemini mentions
        src = src.replace(
            "GPT-4o is fast and inexpensive",
            "GPT-4o is a strong evaluator"
        )
        src = src.replace(
            "Cheap (GPT-4o is fast and inexpensive)",
            "Same provider (one API key, simpler setup)"
        )

        # 9. Resources section - remove Gemini link
        src = src.replace(
            "- [GPT-4o](https://ai.google.dev/) \u2014 Fast, affordable judge model for evaluation\n",
            ""
        )

        # 10. Fix print messages
        src = src.replace(
            "GPT-4o judge model initialized!",
            "GPT-4o judge model initialized!"
        )

        # 11. Cross-model -> stronger-model
        src = src.replace("cross-model evaluation", "stronger-model evaluation")
        src = src.replace("Cross-model evaluation", "Stronger-model evaluation")

        # 12. Fix "This is the industry standard approach used by..."
        src = src.replace(
            "This is the industry standard approach used by Anthropic, OpenAI, and Google for prompt evaluation.",
            "This is the industry standard approach: use a stronger model to evaluate a weaker one."
        )

        cell["source"] = src

    return cells


def rewrite_gemini_cells(cells):
    """Rewrite cells 17-18 which are specifically about Gemini as judge."""
    for cell in cells:
        if cell["cell_num"] == 17:
            cell["source"] = (
                "## G-Eval: The Standard for LLM Evaluation\n"
                "\n"
                "**G-Eval** (Liu et al., 2023) is a framework for using LLMs as evaluators. The key innovation: instead of asking \"rate this 1-5\", you give the judge:\n"
                "\n"
                "1. **Evaluation criteria** \u2014 a clear definition of what \"good\" means\n"
                "2. **Evaluation steps** \u2014 a chain-of-thought procedure for scoring\n"
                "\n"
                "The original paper uses both, but **in DeepEval's implementation, these are mutually exclusive** \u2014 you provide one or the other. We'll use `criteria` and let the model generate its own reasoning steps.\n"
                "\n"
                "This produces much more consistent and reliable scores than naive prompting.\n"
                "\n"
                "**Our stack:**\n"
                "- **Judge model:** GPT-4o (stronger model evaluates weaker model's outputs)\n"
                "- **Framework:** DeepEval's `GEval` metric class\n"
                "- **Dimensions:** Correctness, Completeness, Tone, Safety\n"
                "\n"
                "DeepEval handles the G-Eval protocol \u2014 we just define criteria and run evaluations."
            )

        elif cell["cell_num"] == 18:
            cell["source"] = (
                "## Why GPT-4o as Judge?\n"
                "\n"
                "We use **GPT-4o** to judge **GPT-4o-mini** outputs. Why not use GPT-4o-mini to judge itself?\n"
                "\n"
                "| Approach | Problem |\n"
                "|----------|--------|\n"
                "| **Self-evaluation** (same model judges itself) | Self-serving bias \u2014 models rate their own outputs higher |\n"
                "| **Stronger-model evaluation** (GPT-4o judges GPT-4o-mini) | Independent assessment from a more capable model |\n"
                "| **Human evaluation** | Gold standard but doesn't scale |\n"
                "\n"
                "**Stronger-model evaluation** is the practical sweet spot:\n"
                "- A more capable model catches errors the weaker model misses\n"
                "- Automated (scales to 100s of test cases)\n"
                "- Same provider (one API key, simpler setup)\n"
                "- Reproducible (same criteria every time)\n"
                "\n"
                "Using GPT-4o to evaluate GPT-4o-mini is the same principle as having a senior engineer review a junior's code."
            )

    return cells


def build_notebook(cells):
    """Build the notebook JSON structure."""
    nb_cells = []
    for i, cell in enumerate(cells):
        cell_id = "cell-{:03d}".format(i)
        nb_cell = {
            "cell_type": cell["cell_type"],
            "id": cell_id,
            "metadata": {},
            "source": cell["source"]
        }
        if cell["cell_type"] == "code":
            nb_cell["outputs"] = []
            nb_cell["execution_count"] = None

        nb_cells.append(nb_cell)

    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0"
            }
        },
        "cells": nb_cells
    }


def verify_notebook(notebook):
    """Print verification stats."""
    cells = notebook["cells"]
    total = len(cells)
    markdown_count = sum(1 for c in cells if c["cell_type"] == "markdown")
    code_count = sum(1 for c in cells if c["cell_type"] == "code")
    exercise_count = sum(1 for c in cells if "YOUR CODE HERE" in c["source"])
    svg_count = sum(1 for c in cells if ".svg" in c["source"])

    full_text = json.dumps(notebook)
    gemini_count = full_text.lower().count("gemini")
    abs_svg = full_text.count("raw.githubusercontent.com")
    rel_svg = len(re.findall(r'\(charts/', full_text))
    double_brace = full_text.count('{{')

    print("\n" + "=" * 60)
    print("NOTEBOOK VERIFICATION")
    print("=" * 60)
    print("  Total cells:        {}".format(total))
    print("  Markdown cells:     {}".format(markdown_count))
    print("  Code cells:         {}".format(code_count))
    print("  Exercise cells:     {}".format(exercise_count))
    print("  SVG references:     {}".format(svg_count))
    print("  Absolute SVG URLs:  {}".format(abs_svg))
    print("  Relative SVG URLs:  {}".format(rel_svg))
    print("  Gemini references:  {}".format(gemini_count))
    print("  Double-brace {{{{:   {}".format(double_brace))
    print("=" * 60)

    checks = [
        ("Total cells == 83", total == 83),
        ("Exercise cells >= 12", exercise_count >= 12),
        ("SVG refs >= 8", svg_count >= 8),
        ("No relative SVG URLs", rel_svg == 0),
        ("No Gemini references", gemini_count == 0),
        ("Has double-brace escaping", double_brace > 0),
    ]

    all_pass = True
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print("  {} | {}".format(status, name))
        if not ok:
            all_pass = False

    return all_pass


def main():
    plan_path = os.path.abspath(PLAN_FILE)
    print("Reading plan: {}".format(plan_path))
    with open(plan_path, 'r') as f:
        plan_text = f.read()

    cells = parse_cells_from_plan(plan_text)
    print("Parsed {} cells from plan".format(len(cells)))

    # Sort by cell number
    cells.sort(key=lambda c: c["cell_num"])

    # Verify continuity
    actual = [c["cell_num"] for c in cells]
    expected = list(range(len(cells)))
    if actual != expected:
        missing = set(expected) - set(actual)
        extra = set(actual) - set(expected)
        print("WARNING: Cell numbering issue!")
        if missing:
            print("  Missing cells: {}".format(sorted(missing)))
        if extra:
            print("  Extra cells: {}".format(sorted(extra)))

    # Apply transformations
    cells = apply_transformations(cells)
    cells = rewrite_gemini_cells(cells)

    # Build notebook
    notebook = build_notebook(cells)

    # Write
    output_path = os.path.abspath(OUTPUT_FILE)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(notebook, f, indent=1)
    print("Written: {}".format(output_path))

    # Verify
    ok = verify_notebook(notebook)
    if ok:
        print("\nAll checks passed!")
    else:
        print("\nSome checks failed - review above.")


if __name__ == "__main__":
    main()
