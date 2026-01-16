"""Generator for JsonUI test documentation."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from .schema import (
    SUPPORTED_ACTIONS,
    SUPPORTED_ASSERTIONS,
    PARAMETER_DESCRIPTIONS,
)
from .validator import TestValidator, ValidationResult


class DocumentGenerator:
    """Generates human-readable documentation from test files."""

    def __init__(self):
        self.validator = TestValidator()
        self._test_file_path: Path | None = None

    def _resolve_description(self, case: dict) -> dict | str:
        """
        Resolve the description for a test case.

        If descriptionFile is specified, reads and parses the JSON file.
        Otherwise, returns the inline description.

        Args:
            case: Test case dictionary

        Returns:
            Description dict (from JSON file) or string (inline description)
        """
        # Check for external description file
        if "descriptionFile" in case and self._test_file_path:
            desc_file_path = case["descriptionFile"]
            # Resolve relative to test file location
            if not Path(desc_file_path).is_absolute():
                desc_file_path = self._test_file_path.parent / desc_file_path

            desc_path = Path(desc_file_path)
            if desc_path.exists():
                try:
                    with open(desc_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    return f"[Error reading {case['descriptionFile']}: {e}]"
            else:
                return f"[Description file not found: {case['descriptionFile']}]"

        # Fall back to inline description
        return case.get("description", "")

    def generate(self, file_path: Path, output_path: Path | None = None, format: str = "markdown") -> str | None:
        """
        Generate documentation from a test file.

        Args:
            file_path: Path to the .test.json file
            output_path: Optional output path (if None, returns string)
            format: Output format ("markdown" or "html")

        Returns:
            Generated content as string if output_path is None
        """
        # Store file path for resolving relative description files
        self._test_file_path = Path(file_path).resolve()

        # First validate
        result = self.validator.validate_file(file_path)

        if not result.is_valid:
            raise ValueError(f"Validation failed for {file_path}: {result.error_count} errors")

        # Generate based on format
        if format == "markdown":
            content = self._generate_markdown(result)
        elif format == "html":
            content = self._generate_html(result)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Write or return
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return None
        else:
            return content

    def _format_description_markdown(self, desc: dict | str) -> list[str]:
        """Format description (dict or string) for Markdown output."""
        lines = []
        if isinstance(desc, dict):
            # Description from JSON file
            if desc.get("summary"):
                lines.append(desc["summary"])
                lines.append("")
            if desc.get("preconditions"):
                lines.append("**Preconditions:**")
                for item in desc["preconditions"]:
                    lines.append(f"- {item}")
                lines.append("")
            if desc.get("test_procedure"):
                lines.append("**Test Procedure:**")
                for i, item in enumerate(desc["test_procedure"], 1):
                    lines.append(f"{i}. {item}")
                lines.append("")
            if desc.get("expected_results"):
                lines.append("**Expected Results:**")
                for item in desc["expected_results"]:
                    lines.append(f"- {item}")
                lines.append("")
            if desc.get("notes"):
                lines.append(f"**Notes:** {desc['notes']}")
                lines.append("")
        elif desc:
            # Inline description string
            lines.append(desc)
            lines.append("")
        return lines

    def _generate_markdown(self, result: ValidationResult) -> str:
        """Generate Markdown documentation."""
        data = result.test_data
        lines = []

        # Header
        metadata = data.get("metadata", {})
        title = metadata.get("name", result.file_path.stem)
        description = metadata.get("description", "")

        lines.append(f"# {title}")
        lines.append("")
        if description:
            lines.append(f"> {description}")
            lines.append("")

        # Test info
        lines.append("## Test Information")
        lines.append("")
        lines.append(f"- **Type:** {data.get('type', 'unknown')}")
        lines.append(f"- **Platform:** {data.get('platform', 'all')}")
        if "source" in data:
            lines.append(f"- **Layout:** `{data['source'].get('layout', 'N/A')}`")
        lines.append(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Test cases
        cases = data.get("cases", [])
        if cases:
            lines.append("## Test Cases")
            lines.append("")

            for i, case in enumerate(cases, 1):
                case_name = case.get("name", f"Case {i}")
                case_desc = self._resolve_description(case)

                lines.append(f"### {i}. {case_name}")
                lines.append("")
                lines.extend(self._format_description_markdown(case_desc))

                # Steps table
                steps = case.get("steps", [])
                if steps:
                    lines.append("| # | Type | Action/Assert | Target | Details |")
                    lines.append("|---|------|---------------|--------|---------|")

                    for j, step in enumerate(steps, 1):
                        step_type = "Action" if "action" in step else "Assert"
                        action_name = step.get("action") or step.get("assert", "?")
                        target = step.get("id") or ", ".join(step.get("ids", [])) or "-"
                        details = self._format_step_details(step)
                        lines.append(f"| {j} | {step_type} | `{action_name}` | `{target}` | {details} |")

                    lines.append("")

        # Setup/Teardown
        for section_name in ["setup", "teardown"]:
            section = data.get(section_name, [])
            if section:
                lines.append(f"## {section_name.title()}")
                lines.append("")
                for j, step in enumerate(section, 1):
                    action_name = step.get("action") or step.get("assert", "?")
                    target = step.get("id", "-")
                    lines.append(f"{j}. `{action_name}` on `{target}`")
                lines.append("")

        return "\n".join(lines)

    def _format_description_html(self, desc: dict | str) -> list[str]:
        """Format description (dict or string) for HTML output."""
        parts = []
        if isinstance(desc, dict):
            # Description from JSON file
            if desc.get("summary"):
                escaped = self._escape_html(desc["summary"])
                parts.append(f"  <p class='summary'>{escaped}</p>")
            if desc.get("preconditions"):
                parts.append("  <div class='desc-section'>")
                parts.append("    <strong>Preconditions:</strong>")
                parts.append("    <ul>")
                for item in desc["preconditions"]:
                    escaped = self._escape_html(item)
                    parts.append(f"      <li>{escaped}</li>")
                parts.append("    </ul>")
                parts.append("  </div>")
            if desc.get("test_procedure"):
                parts.append("  <div class='desc-section'>")
                parts.append("    <strong>Test Procedure:</strong>")
                parts.append("    <ol>")
                for item in desc["test_procedure"]:
                    escaped = self._escape_html(item)
                    parts.append(f"      <li>{escaped}</li>")
                parts.append("    </ol>")
                parts.append("  </div>")
            if desc.get("expected_results"):
                parts.append("  <div class='desc-section'>")
                parts.append("    <strong>Expected Results:</strong>")
                parts.append("    <ul>")
                for item in desc["expected_results"]:
                    escaped = self._escape_html(item)
                    parts.append(f"      <li>{escaped}</li>")
                parts.append("    </ul>")
                parts.append("  </div>")
            if desc.get("notes"):
                escaped = self._escape_html(desc["notes"])
                parts.append(f"  <p class='notes'><strong>Notes:</strong> {escaped}</p>")
        elif desc:
            # Inline description string
            escaped = self._escape_html(desc)
            parts.append(f"  <p>{escaped}</p>")
        return parts

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def _generate_html(self, result: ValidationResult) -> str:
        """Generate HTML documentation."""
        data = result.test_data
        metadata = data.get("metadata", {})
        name = metadata.get("name", result.file_path.stem)
        description = metadata.get("description", "")
        title = description or name
        cases = data.get("cases", [])

        html_parts = self._get_html_header(title, cases)

        # Main content wrapper
        html_parts.append("  <main class='main-content'>")
        html_parts.append(f"    <h1>{self._escape_html(title)}</h1>")
        html_parts.append(f"    <p class='test-name-label'><strong>Test Name:</strong> <code>{self._escape_html(name)}</code></p>")

        # Test info
        html_parts.append("    <div class='info'>")
        html_parts.append(f"      <strong>Type:</strong> {data.get('type', 'unknown')}<br>")
        html_parts.append(f"      <strong>Platform:</strong> {data.get('platform', 'all')}<br>")
        if "source" in data:
            html_parts.append(f"      <strong>Layout:</strong> <code>{self._escape_html(data['source'].get('layout', 'N/A'))}</code><br>")
        html_parts.append(f"      <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        html_parts.append("    </div>")

        # Test cases
        if cases:
            html_parts.append("    <h2>Test Cases</h2>")

            for i, case in enumerate(cases, 1):
                case_name = case.get("name", f"Case {i}")
                case_display = case.get("description") or case_name
                case_id = f"case-{i}"
                case_desc = self._resolve_description(case)

                html_parts.append(f"    <h3 id='{case_id}'>{i}. {self._escape_html(case_display)}</h3>")
                html_parts.append(f"    <p class='case-name-label'><strong>Case Name:</strong> <code>{self._escape_html(case_name)}</code></p>")
                html_parts.extend(self._format_description_html(case_desc))

                steps = case.get("steps", [])
                if steps:
                    html_parts.append("    <table>")
                    html_parts.append("      <tr><th>#</th><th>Type</th><th>Action/Assert</th><th>Target</th><th>Details</th></tr>")

                    for j, step in enumerate(steps, 1):
                        step_type = "action" if "action" in step else "assert"
                        type_label = "Action" if step_type == "action" else "Assert"
                        action_name = step.get("action") or step.get("assert", "?")
                        target = step.get("id") or ", ".join(step.get("ids", [])) or "-"
                        details = self._format_step_details(step)
                        html_parts.append(f"      <tr><td>{j}</td><td><span class='{step_type}'>{type_label}</span></td><td><code>{action_name}</code></td><td><code>{target}</code></td><td>{details}</td></tr>")

                    html_parts.append("    </table>")

        html_parts.append("  </main>")
        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

    def _get_html_header(self, title: str, cases: list = None) -> list[str]:
        """Get HTML header with styles and sidebar."""
        cases = cases or []

        parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            f"  <title>{self._escape_html(title)} - Test Documentation</title>",
            "  <meta charset='utf-8'>",
            "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
            "  <style>",
            "    * { box-sizing: border-box; }",
            "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; line-height: 1.6; display: flex; }",
            "    /* Sidebar */",
            "    .sidebar { width: 280px; min-width: 280px; height: 100vh; position: fixed; top: 0; left: 0; background: #f8f9fa; border-right: 1px solid #e0e0e0; overflow-y: auto; padding: 20px; }",
            "    .sidebar h2 { font-size: 1em; color: #333; margin: 0 0 15px 0; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0; }",
            "    .sidebar-title { font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }",
            "    .sidebar ul { list-style: none; padding: 0; margin: 0; }",
            "    .sidebar li { margin: 4px 0; }",
            "    .sidebar a { display: flex; align-items: flex-start; padding: 8px 12px; color: #555; text-decoration: none; border-radius: 6px; font-size: 0.9em; transition: all 0.2s; }",
            "    .sidebar a:hover { background: #e9ecef; color: #007AFF; }",
            "    .sidebar a.active { background: #007AFF; color: white; }",
            "    .case-number { flex-shrink: 0; width: 24px; height: 24px; line-height: 24px; text-align: center; background: #e0e0e0; border-radius: 50%; font-size: 0.75em; font-weight: 600; margin-right: 8px; }",
            "    .case-name { flex: 1; word-break: break-word; }",
            "    .sidebar a:hover .case-number { background: #d0d0d0; }",
            "    .sidebar a.active .case-number { background: rgba(255,255,255,0.3); }",
            "    .back-link { display: block; padding: 10px 12px; margin-bottom: 15px; color: #007AFF; font-size: 0.9em; border-bottom: 1px solid #e0e0e0; }",
            "    .back-link:hover { background: #e9ecef; }",
            "    /* Main content */",
            "    .main-content { margin-left: 280px; padding: 30px 40px; max-width: 900px; flex: 1; }",
            "    h1 { color: #333; border-bottom: 2px solid #007AFF; padding-bottom: 10px; margin-top: 0; }",
            "    h2 { color: #555; margin-top: 30px; }",
            "    h3 { color: #666; margin-top: 25px; scroll-margin-top: 20px; }",
            "    table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
            "    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }",
            "    th { background: #f5f5f5; }",
            "    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }",
            "    .info { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }",
            "    .description { color: #666; font-style: italic; margin-bottom: 20px; }",
            "    .action { color: #007AFF; font-weight: 500; }",
            "    .assert { color: #34C759; font-weight: 500; }",
            "    .summary { color: #333; margin-bottom: 10px; }",
            "    .case-name-label { color: #888; font-size: 0.9em; margin: -10px 0 15px 0; }",
            "    .case-name-label code { background: #f5f5f5; color: #666; }",
            "    .test-name-label { color: #888; font-size: 0.9em; margin: -5px 0 15px 0; }",
            "    .test-name-label code { background: #f5f5f5; color: #666; }",
            "    .desc-section { margin: 10px 0; padding-left: 10px; border-left: 3px solid #e0e0e0; }",
            "    .desc-section ul, .desc-section ol { margin: 5px 0; padding-left: 25px; }",
            "    .notes { color: #666; font-style: italic; background: #fffbf0; padding: 10px; border-radius: 5px; }",
            "    a { color: #007AFF; text-decoration: none; }",
            "    a:hover { text-decoration: underline; }",
            "    /* Responsive */",
            "    @media (max-width: 768px) {",
            "      .sidebar { display: none; }",
            "      .main-content { margin-left: 0; padding: 20px; }",
            "    }",
            "  </style>",
            "</head>",
            "<body>",
        ]

        # Sidebar with case navigation
        parts.append("  <nav class='sidebar'>")
        parts.append("    <a href='../index.html' class='back-link'>&larr; Back to Index</a>")
        parts.append(f"    <h2>{self._escape_html(title)}</h2>")

        if cases:
            parts.append("    <div class='sidebar-title'>Test Cases</div>")
            parts.append("    <ul>")
            for i, case in enumerate(cases, 1):
                case_display = case.get("description") or case.get("name", f"Case {i}")
                case_id = f"case-{i}"
                parts.append(f"      <li><a href='#{case_id}'><span class='case-number'>{i}</span><span class='case-name'>{self._escape_html(case_display)}</span></a></li>")
            parts.append("    </ul>")

        parts.append("  </nav>")

        return parts

    def _format_step_details(self, step: dict) -> str:
        """Format step details for display."""
        details = []

        if "value" in step:
            details.append(f"value: \"{step['value']}\"")
        if "direction" in step:
            details.append(f"direction: {step['direction']}")
        if "timeout" in step:
            details.append(f"timeout: {step['timeout']}ms")
        if "ms" in step:
            details.append(f"wait: {step['ms']}ms")
        if "duration" in step:
            details.append(f"duration: {step['duration']}ms")
        if "equals" in step:
            details.append(f"equals: \"{step['equals']}\"")
        if "contains" in step:
            details.append(f"contains: \"{step['contains']}\"")
        if "name" in step and step.get("action") == "screenshot":
            details.append(f"name: \"{step['name']}\"")

        return ", ".join(details) if details else "-"


def generate_schema_reference(output_path: Path | None = None, format: str = "markdown") -> str | None:
    """
    Generate a reference document for the test schema.

    Args:
        output_path: Optional output path
        format: Output format ("markdown" or "html")

    Returns:
        Generated content as string if output_path is None
    """
    if format == "markdown":
        content = _generate_schema_markdown()
    else:
        raise ValueError(f"Unsupported format: {format}")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return None
    else:
        return content


def _generate_schema_markdown() -> str:
    """Generate Markdown schema reference."""
    lines = [
        "# JsonUI Test Schema Reference",
        "",
        "This document describes all supported actions and assertions for JsonUI test files.",
        "",
        "## Actions",
        "",
    ]

    for action, spec in SUPPORTED_ACTIONS.items():
        lines.append(f"### `{action}`")
        lines.append("")
        lines.append(spec["description"])
        lines.append("")

        if spec["required"]:
            lines.append("**Required parameters:**")
            for param in spec["required"]:
                desc = PARAMETER_DESCRIPTIONS.get(param, "")
                lines.append(f"- `{param}`: {desc}")
            lines.append("")

        if spec["optional"]:
            lines.append("**Optional parameters:**")
            for param in spec["optional"]:
                desc = PARAMETER_DESCRIPTIONS.get(param, "")
                lines.append(f"- `{param}`: {desc}")
            lines.append("")

        # Example
        example = _get_action_example(action, spec)
        lines.append("**Example:**")
        lines.append("```json")
        lines.append(json.dumps(example, indent=2))
        lines.append("```")
        lines.append("")

    lines.append("## Assertions")
    lines.append("")

    for assertion, spec in SUPPORTED_ASSERTIONS.items():
        lines.append(f"### `{assertion}`")
        lines.append("")
        lines.append(spec["description"])
        lines.append("")

        if spec["required"]:
            lines.append("**Required parameters:**")
            for param in spec["required"]:
                desc = PARAMETER_DESCRIPTIONS.get(param, "")
                lines.append(f"- `{param}`: {desc}")
            lines.append("")

        if spec["optional"]:
            lines.append("**Optional parameters:**")
            for param in spec["optional"]:
                desc = PARAMETER_DESCRIPTIONS.get(param, "")
                lines.append(f"- `{param}`: {desc}")
            lines.append("")

        # Example
        example = _get_assertion_example(assertion, spec)
        lines.append("**Example:**")
        lines.append("```json")
        lines.append(json.dumps(example, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def _get_action_example(action: str, spec: dict) -> dict:
    """Generate example for an action."""
    example = {"action": action}

    if "id" in spec["required"]:
        example["id"] = "element_id"
    if "ids" in spec["required"]:
        example["ids"] = ["element_1", "element_2"]
    if "value" in spec["required"]:
        example["value"] = "sample text"
    if "direction" in spec["required"]:
        example["direction"] = "down"
    if "ms" in spec["required"]:
        example["ms"] = 1000
    if "name" in spec["required"]:
        example["name"] = "screenshot_name"

    return example


def _get_assertion_example(assertion: str, spec: dict) -> dict:
    """Generate example for an assertion."""
    example = {"assert": assertion}

    if "id" in spec["required"]:
        example["id"] = "element_id"
    if "equals" in spec["required"]:
        example["equals"] = 5

    if assertion == "text":
        example["equals"] = "Expected text"

    return example


def generate_html_directory(
    input_dir: Path,
    output_dir: Path,
    title: str = "JsonUI Test Documentation"
) -> list[dict]:
    """
    Generate HTML documentation for all test files in a directory.

    Creates individual HTML files for each test and an index.html with links.

    Args:
        input_dir: Directory containing .test.json files
        output_dir: Directory to output HTML files
        title: Title for the index page

    Returns:
        List of generated file info dicts with 'name', 'path', 'type', 'cases'
    """
    generator = DocumentGenerator()
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Collect all test files
    test_files = list(input_path.rglob("*.test.json"))

    if not test_files:
        raise ValueError(f"No .test.json files found in {input_dir}")

    generated_files = []

    # Generate HTML for each test file
    for test_file in sorted(test_files):
        try:
            # Validate first
            result = generator.validator.validate_file(test_file)
            if not result.is_valid:
                print(f"  Skipping {test_file} (validation errors)")
                continue

            # Determine relative path structure
            rel_path = test_file.relative_to(input_path)
            html_filename = rel_path.with_suffix('.html').name

            # Create subdirectory structure in output
            test_type = result.test_data.get('type', 'unknown')
            if test_type == 'screen':
                subdir = output_path / 'screens'
            elif test_type == 'flow':
                subdir = output_path / 'flows'
            else:
                subdir = output_path / 'other'

            subdir.mkdir(parents=True, exist_ok=True)
            html_path = subdir / html_filename

            # Generate HTML
            generator._test_file_path = test_file.resolve()
            content = generator._generate_html(result)

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Collect info for index
            metadata = result.test_data.get('metadata', {})
            cases = result.test_data.get('cases', [])
            steps = result.test_data.get('steps', [])

            generated_files.append({
                'name': metadata.get('name', test_file.stem),
                'description': metadata.get('description', ''),
                'path': html_path.relative_to(output_path),
                'type': test_type,
                'case_count': len(cases) if cases else 0,
                'step_count': len(steps) if steps else sum(len(c.get('steps', [])) for c in cases),
                'platform': result.test_data.get('platform', 'all'),
            })

            print(f"  Generated: {html_path}")

        except Exception as e:
            print(f"  Error processing {test_file}: {e}")

    # Generate index.html
    _generate_index_html(output_path, generated_files, title)

    return generated_files


def _generate_index_html(output_dir: Path, files: list[dict], title: str):
    """Generate index.html with links to all test documentation."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        f"  <title>{title}</title>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "  <style>",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; line-height: 1.6; background: #fafafa; }",
        "    h1 { color: #333; border-bottom: 2px solid #007AFF; padding-bottom: 10px; }",
        "    h2 { color: #555; margin-top: 30px; }",
        "    .summary { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }",
        "    .summary-item { display: inline-block; margin-right: 30px; }",
        "    .summary-value { font-size: 2em; font-weight: bold; color: #007AFF; }",
        "    .summary-label { color: #666; }",
        "    .test-list { list-style: none; padding: 0; }",
        "    .test-item { background: #fff; margin: 10px 0; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "    .test-item:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.15); }",
        "    .test-name { font-size: 1.1em; font-weight: 600; color: #333; text-decoration: none; }",
        "    .test-name:hover { color: #007AFF; }",
        "    .test-meta { margin-top: 5px; color: #666; font-size: 0.9em; }",
        "    .test-description { color: #555; margin-top: 5px; }",
        "    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; }",
        "    .badge-screen { background: #e3f2fd; color: #1976d2; }",
        "    .badge-flow { background: #f3e5f5; color: #7b1fa2; }",
        "    .badge-platform { background: #e8f5e9; color: #388e3c; }",
        "    .generated { color: #999; font-size: 0.85em; margin-top: 30px; text-align: center; }",
        "  </style>",
        "</head>",
        "<body>",
        f"  <h1>{title}</h1>",
    ]

    # Summary section
    screen_count = sum(1 for f in files if f['type'] == 'screen')
    flow_count = sum(1 for f in files if f['type'] == 'flow')
    total_cases = sum(f['case_count'] for f in files)
    total_steps = sum(f['step_count'] for f in files)

    html_parts.extend([
        "  <div class='summary'>",
        "    <div class='summary-item'>",
        f"      <div class='summary-value'>{len(files)}</div>",
        "      <div class='summary-label'>Test Files</div>",
        "    </div>",
        "    <div class='summary-item'>",
        f"      <div class='summary-value'>{screen_count}</div>",
        "      <div class='summary-label'>Screen Tests</div>",
        "    </div>",
        "    <div class='summary-item'>",
        f"      <div class='summary-value'>{flow_count}</div>",
        "      <div class='summary-label'>Flow Tests</div>",
        "    </div>",
        "    <div class='summary-item'>",
        f"      <div class='summary-value'>{total_cases}</div>",
        "      <div class='summary-label'>Test Cases</div>",
        "    </div>",
        "    <div class='summary-item'>",
        f"      <div class='summary-value'>{total_steps}</div>",
        "      <div class='summary-label'>Total Steps</div>",
        "    </div>",
        "  </div>",
    ])

    # Screen tests section
    screen_files = [f for f in files if f['type'] == 'screen']
    if screen_files:
        html_parts.append("  <h2>Screen Tests</h2>")
        html_parts.append("  <ul class='test-list'>")
        for f in screen_files:
            html_parts.extend([
                "    <li class='test-item'>",
                f"      <a href='{f['path']}' class='test-name'>{f['name']}</a>",
                "      <div class='test-meta'>",
                f"        <span class='badge badge-screen'>screen</span>",
                f"        <span class='badge badge-platform'>{f['platform']}</span>",
                f"        {f['case_count']} cases, {f['step_count']} steps",
                "      </div>",
            ])
            if f['description']:
                html_parts.append(f"      <div class='test-description'>{f['description']}</div>")
            html_parts.append("    </li>")
        html_parts.append("  </ul>")

    # Flow tests section
    flow_files = [f for f in files if f['type'] == 'flow']
    if flow_files:
        html_parts.append("  <h2>Flow Tests</h2>")
        html_parts.append("  <ul class='test-list'>")
        for f in flow_files:
            html_parts.extend([
                "    <li class='test-item'>",
                f"      <a href='{f['path']}' class='test-name'>{f['name']}</a>",
                "      <div class='test-meta'>",
                f"        <span class='badge badge-flow'>flow</span>",
                f"        <span class='badge badge-platform'>{f['platform']}</span>",
                f"        {f['step_count']} steps",
                "      </div>",
            ])
            if f['description']:
                html_parts.append(f"      <div class='test-description'>{f['description']}</div>")
            html_parts.append("    </li>")
        html_parts.append("  </ul>")

    # Other tests section
    other_files = [f for f in files if f['type'] not in ['screen', 'flow']]
    if other_files:
        html_parts.append("  <h2>Other Tests</h2>")
        html_parts.append("  <ul class='test-list'>")
        for f in other_files:
            html_parts.extend([
                "    <li class='test-item'>",
                f"      <a href='{f['path']}' class='test-name'>{f['name']}</a>",
                "      <div class='test-meta'>",
                f"        <span class='badge'>{f['type']}</span>",
                f"        <span class='badge badge-platform'>{f['platform']}</span>",
                "      </div>",
            ])
            if f['description']:
                html_parts.append(f"      <div class='test-description'>{f['description']}</div>")
            html_parts.append("    </li>")
        html_parts.append("  </ul>")

    # Footer
    html_parts.extend([
        f"  <p class='generated'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        "</body>",
        "</html>",
    ])

    # Write index.html
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_parts))

    print(f"  Generated: {index_path}")
