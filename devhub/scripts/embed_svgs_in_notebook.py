#!/usr/bin/env python3
"""
Embed SVG Diagrams in Session 1 Notebook

Adds markdown cells with GitHub-hosted SVG images at appropriate locations.
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("exercises/session_01/session_01_observability.ipynb")
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/axel-sirota/salesforce-ai-workshops/main/exercises/session_01/charts"

# SVG placements: (pattern_to_find, svg_filename, insert_position)
# insert_position: "after" = insert after the cell with pattern
SVG_PLACEMENTS = [
    # 5-Layer Architecture diagram after the framework intro
    ("## The 5-Layer AI Architecture Framework", "01_five_layer_architecture.svg", "after"),
    # DevHub request flow after "DevHub Request Flow" or "What DevHub Does"
    ("## What DevHub Does", "02_devhub_request_flow.svg", "after"),
    # Trace hierarchy after "What is a Trace?"
    ("What is a Trace?", "03_trace_span_hierarchy.svg", "after"),
    # Span attributes after "Span Attributes: The Secret Sauce"
    ("Span Attributes: The Secret Sauce", "04_span_attributes.svg", "after"),
    # Context propagation after that section
    ("Context Propagation: Connecting the Dots", "05_context_propagation.svg", "after"),
    # Before/After in wrap-up visual comparison
    ("Visual Comparison", "06_before_after_observability.svg", "after"),
    # OTel architecture after "Task 1: Initialize OpenTelemetry"
    ("Task 1: Initialize OpenTelemetry", "07_otel_architecture.svg", "after"),
]


def create_image_cell(svg_filename: str, alt_text: str) -> dict:
    """Create a markdown cell with an embedded SVG image."""
    url = f"{GITHUB_RAW_BASE}/{svg_filename}"
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            f"![{alt_text}]({url})\n"
        ]
    }


def find_cell_index(cells: list, pattern: str) -> int | None:
    """Find the index of the cell containing the pattern."""
    for i, cell in enumerate(cells):
        source = "".join(cell.get("source", []))
        if pattern in source:
            return i
    return None


def main():
    print(f"Reading notebook: {NOTEBOOK_PATH}")

    with open(NOTEBOOK_PATH) as f:
        notebook = json.load(f)

    cells = notebook["cells"]
    print(f"Found {len(cells)} cells")

    # Track insertions (insert from end to preserve indices)
    insertions = []

    for pattern, svg_file, position in SVG_PLACEMENTS:
        idx = find_cell_index(cells, pattern)
        if idx is None:
            print(f"  WARNING: Pattern not found: '{pattern[:40]}...'")
            continue

        # Create alt text from filename
        alt_text = svg_file.replace(".svg", "").replace("_", " ").title()
        alt_text = alt_text[3:]  # Remove number prefix

        insert_idx = idx + 1 if position == "after" else idx
        insertions.append((insert_idx, svg_file, alt_text))
        print(f"  Found '{pattern[:30]}...' at cell {idx}, will insert {svg_file}")

    # Sort insertions by index descending to preserve positions
    insertions.sort(key=lambda x: x[0], reverse=True)

    # Check if images already exist to avoid duplicates
    existing_images = set()
    for cell in cells:
        source = "".join(cell.get("source", []))
        for _, svg_file, _ in SVG_PLACEMENTS:
            if svg_file in source:
                existing_images.add(svg_file)

    # Insert cells
    inserted = 0
    for insert_idx, svg_file, alt_text in insertions:
        if svg_file in existing_images:
            print(f"  SKIP: {svg_file} already in notebook")
            continue

        new_cell = create_image_cell(svg_file, alt_text)
        cells.insert(insert_idx, new_cell)
        inserted += 1
        print(f"  Inserted {svg_file} at index {insert_idx}")

    # Update notebook
    notebook["cells"] = cells

    # Write back
    print(f"\nWriting {len(cells)} cells to notebook ({inserted} new)...")
    with open(NOTEBOOK_PATH, "w") as f:
        json.dump(notebook, f, indent=1)

    print("Done!")


if __name__ == "__main__":
    main()
