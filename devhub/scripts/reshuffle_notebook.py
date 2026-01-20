#!/usr/bin/env python3
"""
Reshuffle Session 1 Notebook Cells

The NotebookEdit tool inserted cells at the BEGINNING instead of END,
causing cells to be out of order. This script reorders them based on
unique content patterns from the blueprint.

Usage:
    python devhub/scripts/reshuffle_notebook.py
"""

import json
from pathlib import Path

# Notebook path
NOTEBOOK_PATH = Path("exercises/session_01/session_01_observability.ipynb")

# Unique patterns to identify each cell (cell_number, pattern)
# Based on plans/workshop1/notebook/WORKSHOP1_NOTEBOOK_PROGRESS.md
CELL_PATTERNS = [
    # Section 0: Welcome & Setup (Cells 1-8)
    (1, "# Session 1: Observability in AI Applications"),
    (2, 'The Problem: "It\'s Slow Sometimes"'),
    (3, "What We'll Build Today"),
    (4, "INSTALL REQUIRED PACKAGES"),
    (5, "# CONFIGURATION\n# ="),  # More specific to avoid conflicts
    (6, "TEST JAEGER CONNECTION"),
    (7, "TEST OPENAI CONNECTION"),
    (8, "Setup Complete!"),

    # Section 1: 5-Layer Architecture (Cells 9-18)
    (9, "# Topic 1: Understanding AI System Architecture"),
    (10, "Why Architecture Matters for Debugging"),
    (11, "## The 5-Layer AI Architecture Framework"),  # More specific with ##
    (12, "Layer 1: Application Layer"),
    (13, "Layer 2: Gateway Layer"),
    (14, "Layer 3: Orchestration Layer"),
    (15, "Layer 4: LLM Layer"),
    (16, "Layer 5: Data Layer"),
    (17, "DevHub: Mapped to 5 Layers"),
    (18, "Key Insight: Layer-Based Debugging"),

    # Section 2: Meet DevHub V0 (Cells 19-30)
    (19, "# Topic 2: DevHub - Our Workshop Application"),
    (20, "## What DevHub Does"),
    (21, "DevHub Request Flow"),
    (22, "DEVHUB V0 - THE UNINSTRUMENTED VERSION"),
    (23, "INITIALIZE DEVHUB"),
    (24, "DEMO: Run a documentation query"),
    (25, "DEMO: Try different query types"),
    (26, "Lab 1.1: Explore DevHub"),
    (27, "LAB 1.1: Explore DevHub"),
    (28, "The Frustration Exercise"),
    (29, "TRY TO DEBUG DEVHUB"),
    (30, "Discussion: What Information Would Help"),

    # Section 3: Distributed Tracing Concepts (Cells 31-42)
    (31, "# Topic 3: Distributed Tracing with OpenTelemetry"),
    (32, "The Problem: Where's the Bottleneck"),
    (33, "The Black Box Problem"),
    (34, "What is a Trace?"),
    (35, "What is a Span?"),
    (36, "Trace/Span Hierarchy"),
    (37, "Span Attributes: The Secret Sauce"),
    (38, "Context Propagation: Connecting the Dots"),
    (39, "OpenTelemetry: The Industry Standard"),
    (40, "DEMO: Create a Simple Trace"),
    (41, "HOW TO VIEW YOUR TRACE IN JAEGER"),
    (42, "Key Insight: Traces Show WHERE"),

    # Section 4: Lab 1 - Add Tracing (Cells 43-62)
    (43, "# Lab 1: Instrument DevHub with OpenTelemetry"),
    (44, "What You'll Instrument"),
    (45, "Task 1: Initialize OpenTelemetry"),
    (46, "TASK 1: Initialize OpenTelemetry"),
    (47, "SOLUTION: Task 1"),
    (48, "Task 2: Instrument VectorDB.search()"),
    (49, "TASK 2: Instrument VectorDB"),
    (50, "SOLUTION: Task 2"),
    (51, "Task 3: Instrument TeamDB.find_owner()"),
    (52, "TASK 3: Instrument TeamDB"),
    (53, "SOLUTION: Task 3"),
    (54, "Task 4: Instrument StatusAPI.check_status()"),
    (55, "TASK 4: Instrument StatusAPI"),
    (56, "SOLUTION: Task 4"),
    (57, "Task 5: Instrument DevHubAgent.query()"),
    (58, "TASK 5: Instrument DevHubAgent"),
    (59, "SOLUTION: Task 5"),
    (60, "RUN INSTRUMENTED DEVHUB"),
    (61, "Lab 1 Verification Checklist"),
    (62, "HOW TO VERIFY YOUR TRACES"),

    # Section 5: Lab 2 - Debug with Traces (Cells 63-80)
    (63, "# Lab 2: Debug Production Scenarios Using Traces"),
    (64, "How to Use Jaeger for Debugging"),
    (65, "Jaeger UI Overview"),
    (66, "Scenario 1: The Slow Query"),
    (67, "SCENARIO 1: Reproduce the Slow Query"),
    (68, "Scenario 1: Analysis Worksheet"),
    (69, "SCENARIO 1: Your Analysis"),
    (70, "Scenario 1: Solution"),
    (71, "Scenario 2: The Wrong Owner"),
    (72, "SCENARIO 2: Reproduce the Wrong Owner"),
    (73, "Scenario 2: Analysis Worksheet"),
    (74, "SCENARIO 2: Your Analysis"),
    (75, "Scenario 2: Solution"),
    (76, "Scenario 3: Poor Retrieval Quality"),
    (77, "SCENARIO 3: Reproduce Poor Retrieval"),
    (78, "Scenario 3: Analysis Worksheet"),
    (79, "SCENARIO 3: Your Analysis"),
    (80, "Scenario 3: Solution"),

    # Section 6: Wrap-up (Cells 81-86)
    (81, "# Session 1: Wrap-Up\n\n## What You Learned"),  # More specific
    (82, "Before vs After: The Impact of Observability"),
    (83, "Visual Comparison"),
    (84, "5 Key Takeaways"),
    (85, "Take-Home Exercise"),
    (86, "Coming Up: Session 2"),
]


def identify_cell(cell_source: str) -> int | None:
    """Identify which cell number this is based on content patterns."""
    for cell_num, pattern in CELL_PATTERNS:
        if pattern in cell_source:
            return cell_num
    return None


def main():
    print(f"Reading notebook: {NOTEBOOK_PATH}")

    with open(NOTEBOOK_PATH) as f:
        notebook = json.load(f)

    cells = notebook["cells"]
    print(f"Found {len(cells)} cells")

    # Identify each cell
    cell_mapping = {}  # {cell_num: cell_object}
    unidentified = []

    for i, cell in enumerate(cells):
        source = "".join(cell["source"])
        cell_num = identify_cell(source)

        if cell_num:
            if cell_num in cell_mapping:
                print(f"WARNING: Duplicate match for cell {cell_num}")
                print(f"  Existing: {cell_mapping[cell_num]['source'][0][:50]}...")
                print(f"  New: {source[:50]}...")
            else:
                cell_mapping[cell_num] = cell
                print(f"  Cell {i} -> Blueprint {cell_num}")
        else:
            unidentified.append((i, source[:60]))
            print(f"  Cell {i} -> UNIDENTIFIED: {source[:40]}...")

    print(f"\nIdentified: {len(cell_mapping)} cells")
    print(f"Unidentified: {len(unidentified)} cells")

    if unidentified:
        print("\nUnidentified cells:")
        for idx, preview in unidentified:
            print(f"  {idx}: {preview}...")

    # Check for missing cells
    missing = [i for i in range(1, 87) if i not in cell_mapping]
    if missing:
        print(f"\nMissing cells: {missing}")

    # Reorder cells
    print("\nReordering cells...")
    ordered_cells = []
    for cell_num in range(1, 87):
        if cell_num in cell_mapping:
            ordered_cells.append(cell_mapping[cell_num])
        else:
            print(f"  WARNING: Cell {cell_num} not found, skipping")

    # Update notebook
    notebook["cells"] = ordered_cells

    # Write back
    print(f"\nWriting {len(ordered_cells)} cells to notebook...")
    with open(NOTEBOOK_PATH, "w") as f:
        json.dump(notebook, f, indent=1)

    print("Done!")


if __name__ == "__main__":
    main()
