#!/usr/bin/env python3
"""
Convert Mermaid (.mmd) files to SVG with validation and width fix.

Usage:
    python scripts/convert_to_svg.py --input exercises/session_02/charts --output exercises/session_02/charts
    python scripts/convert_to_svg.py --input exercises/session_02/charts --validate  # Validate only

This script:
1. Validates .mmd files for common issues (markdown lists, etc.)
2. Converts each to .svg using mmdc (mermaid CLI)
3. Validates the SVG output for errors
4. Fixes the width="100%" issue by extracting max-width from style
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# Common mermaid issues to check for
MERMAID_ISSUES = [
    # (pattern, description, suggestion)
    (
        r'\["[0-9]+\.\s',
        "Numbered list in node label (e.g., '1. Something')",
        "Remove number prefix or use 'Step 1:' format"
    ),
    (
        r'\["[-*]\s',
        "Bullet list in node label (e.g., '- Something')",
        "Remove bullet prefix"
    ),
    (
        r'\["\+\s',
        "Plus list in node label (e.g., '+ Something')",
        "Remove + prefix or use 'Add:' format"
    ),
    (
        r'```',
        "Code fence in mermaid",
        "Remove code fences - mermaid doesn't support them in labels"
    ),
    (
        r'\["\s*#',
        "Markdown header in node label",
        "Remove # prefix"
    ),
]


def find_mmdc() -> str:
    """Find the mmdc executable."""
    import os

    locations = [
        "mmdc",
        "/usr/local/bin/mmdc",
        "/opt/homebrew/bin/mmdc",
    ]

    # Check for nvm-installed version
    home = os.path.expanduser("~")
    nvm_path = Path(home) / ".nvm/versions/node"
    if nvm_path.exists():
        for node_version in nvm_path.iterdir():
            mmdc_path = node_version / "bin/mmdc"
            if mmdc_path.exists():
                locations.insert(0, str(mmdc_path))

    for loc in locations:
        try:
            result = subprocess.run(
                [loc, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return loc
        except (subprocess.SubprocessError, FileNotFoundError):
            continue

    raise RuntimeError(
        "mmdc not found. Install with: npm install -g @mermaid-js/mermaid-cli"
    )


def validate_mermaid_file(mmd_file: Path) -> List[Tuple[int, str, str]]:
    """
    Validate a mermaid file for common issues.

    Returns list of (line_number, issue_description, suggestion) tuples.
    """
    issues = []
    content = mmd_file.read_text()
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        for pattern, description, suggestion in MERMAID_ISSUES:
            if re.search(pattern, line):
                issues.append((line_num, description, suggestion))

    return issues


def validate_svg_output(svg_file: Path) -> List[str]:
    """
    Validate SVG output for error indicators.

    Returns list of error messages found.
    """
    errors = []

    if not svg_file.exists():
        errors.append("SVG file was not created")
        return errors

    content = svg_file.read_text()

    # Check for common error indicators in rendered SVG
    error_patterns = [
        (r'unsupported markdown', "Unsupported markdown syntax detected"),
        (r'Syntax error', "Mermaid syntax error"),
        (r'Parse error', "Mermaid parse error"),
        (r'Error:', "Generic error in output"),
    ]

    for pattern, message in error_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            errors.append(message)

    # Check if SVG is essentially empty (just error message)
    if len(content) < 500:
        errors.append("SVG appears to be too small - possible rendering failure")

    return errors


def convert_mmd_to_svg(mmdc_path: str, input_file: Path, output_file: Path) -> Tuple[bool, str]:
    """
    Convert a single .mmd file to .svg using mmdc.

    Returns (success, error_message).
    """
    try:
        result = subprocess.run(
            [mmdc_path, "-i", str(input_file), "-o", str(output_file), "-b", "transparent"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            return False, f"mmdc failed: {result.stderr}"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Timeout during conversion"
    except Exception as e:
        return False, str(e)


def fix_svg_width(svg_file: Path) -> bool:
    """
    Fix SVG width="100%" by extracting max-width from style attribute.
    """
    try:
        content = svg_file.read_text()

        max_width_match = re.search(r'max-width:\s*([\d.]+)px', content)
        if not max_width_match:
            print(f"    WARNING: No max-width found, skipping width fix")
            return True

        max_width = int(float(max_width_match.group(1)))

        new_content = re.sub(
            r'(<svg[^>]*)\s+width="100%"',
            f'\\1 width="{max_width}px"',
            content,
            count=1
        )

        if new_content == content:
            if f'width="{max_width}px"' in content:
                return True
            print(f"    WARNING: Could not find width=\"100%\"")
            return True

        svg_file.write_text(new_content)
        return True

    except Exception as e:
        print(f"    ERROR fixing width: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert Mermaid (.mmd) files to SVG with validation and width fix"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input folder containing .mmd files"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output folder for .svg files (defaults to input folder)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Only validate .mmd files, don't convert"
    )
    parser.add_argument(
        "--fix-only",
        action="store_true",
        help="Only fix existing SVG widths, don't convert"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    if not input_path.exists():
        print(f"ERROR: Input path does not exist: {input_path}")
        sys.exit(1)

    # Find all .mmd files
    mmd_files = list(input_path.glob("*.mmd"))
    if not mmd_files:
        print(f"No .mmd files found in {input_path}")
        sys.exit(0)

    # Validate only mode
    if args.validate:
        print(f"Validating {len(mmd_files)} Mermaid files...\n")
        total_issues = 0

        for mmd_file in sorted(mmd_files):
            issues = validate_mermaid_file(mmd_file)
            if issues:
                print(f"  {mmd_file.name}:")
                for line_num, description, suggestion in issues:
                    print(f"    Line {line_num}: {description}")
                    print(f"      Fix: {suggestion}")
                total_issues += len(issues)
            else:
                print(f"  {mmd_file.name}: OK")

        print(f"\n{'='*50}")
        if total_issues > 0:
            print(f"VALIDATION FAILED: {total_issues} issues found")
            sys.exit(1)
        else:
            print("VALIDATION PASSED: All files OK")
            sys.exit(0)

    # Fix-only mode
    if args.fix_only:
        svg_files = list(output_path.glob("*.svg"))
        if not svg_files:
            print(f"No .svg files found in {output_path}")
            sys.exit(0)

        print(f"Fixing width in {len(svg_files)} SVG files...")
        success_count = 0
        for svg_file in sorted(svg_files):
            print(f"  {svg_file.name}")
            if fix_svg_width(svg_file):
                success_count += 1

        print(f"\nFixed {success_count}/{len(svg_files)} files")
        sys.exit(0 if success_count == len(svg_files) else 1)

    # Full conversion mode
    output_path.mkdir(parents=True, exist_ok=True)

    # Step 1: Validate all files first
    print(f"Step 1: Validating {len(mmd_files)} Mermaid files...")
    all_valid = True
    for mmd_file in sorted(mmd_files):
        issues = validate_mermaid_file(mmd_file)
        if issues:
            all_valid = False
            print(f"\n  {mmd_file.name} has issues:")
            for line_num, description, suggestion in issues:
                print(f"    Line {line_num}: {description}")
                print(f"      Fix: {suggestion}")

    if not all_valid:
        print(f"\nERROR: Fix validation issues before converting.")
        print("Run with --validate to see all issues.")
        sys.exit(1)

    print("  All files valid!")

    # Step 2: Find mmdc
    print("\nStep 2: Looking for mmdc...")
    try:
        mmdc_path = find_mmdc()
        print(f"  Found: {mmdc_path}")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Step 3: Convert all files
    print(f"\nStep 3: Converting {len(mmd_files)} files...")

    success_count = 0
    for mmd_file in sorted(mmd_files):
        svg_file = output_path / f"{mmd_file.stem}.svg"
        print(f"\n  {mmd_file.name} -> {svg_file.name}")

        # Convert
        success, error = convert_mmd_to_svg(mmdc_path, mmd_file, svg_file)
        if not success:
            print(f"    ERROR: {error}")
            continue

        # Validate SVG output
        svg_errors = validate_svg_output(svg_file)
        if svg_errors:
            print(f"    WARNING: SVG has issues:")
            for err in svg_errors:
                print(f"      - {err}")

        # Fix width
        print(f"    Fixing width...")
        if fix_svg_width(svg_file):
            success_count += 1
            print(f"    Done!")

    # Summary
    print(f"\n{'='*50}")
    print(f"Converted: {success_count}/{len(mmd_files)} files")

    if success_count < len(mmd_files):
        sys.exit(1)


if __name__ == "__main__":
    main()
