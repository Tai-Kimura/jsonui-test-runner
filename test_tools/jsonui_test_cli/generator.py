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
                case_desc = case.get("description", "")

                lines.append(f"### {i}. {case_name}")
                lines.append("")
                if case_desc:
                    lines.append(f"{case_desc}")
                    lines.append("")

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

    def _generate_html(self, result: ValidationResult) -> str:
        """Generate HTML documentation."""
        data = result.test_data
        metadata = data.get("metadata", {})
        title = metadata.get("name", result.file_path.stem)
        description = metadata.get("description", "")

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            f"  <title>{title} - Test Documentation</title>",
            "  <meta charset='utf-8'>",
            "  <style>",
            "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
            "    h1 { color: #333; border-bottom: 2px solid #007AFF; padding-bottom: 10px; }",
            "    h2 { color: #555; margin-top: 30px; }",
            "    h3 { color: #666; }",
            "    table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
            "    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }",
            "    th { background: #f5f5f5; }",
            "    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }",
            "    .info { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }",
            "    .description { color: #666; font-style: italic; margin-bottom: 20px; }",
            "    .action { color: #007AFF; }",
            "    .assert { color: #34C759; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{title}</h1>",
        ]

        if description:
            html_parts.append(f"  <p class='description'>{description}</p>")

        # Test info
        html_parts.append("  <div class='info'>")
        html_parts.append(f"    <strong>Type:</strong> {data.get('type', 'unknown')}<br>")
        html_parts.append(f"    <strong>Platform:</strong> {data.get('platform', 'all')}<br>")
        if "source" in data:
            html_parts.append(f"    <strong>Layout:</strong> <code>{data['source'].get('layout', 'N/A')}</code><br>")
        html_parts.append(f"    <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        html_parts.append("  </div>")

        # Test cases
        cases = data.get("cases", [])
        if cases:
            html_parts.append("  <h2>Test Cases</h2>")

            for i, case in enumerate(cases, 1):
                case_name = case.get("name", f"Case {i}")
                case_desc = case.get("description", "")

                html_parts.append(f"  <h3>{i}. {case_name}</h3>")
                if case_desc:
                    html_parts.append(f"  <p>{case_desc}</p>")

                steps = case.get("steps", [])
                if steps:
                    html_parts.append("  <table>")
                    html_parts.append("    <tr><th>#</th><th>Type</th><th>Action/Assert</th><th>Target</th><th>Details</th></tr>")

                    for j, step in enumerate(steps, 1):
                        step_type = "action" if "action" in step else "assert"
                        type_label = "Action" if step_type == "action" else "Assert"
                        action_name = step.get("action") or step.get("assert", "?")
                        target = step.get("id") or ", ".join(step.get("ids", [])) or "-"
                        details = self._format_step_details(step)
                        html_parts.append(f"    <tr><td>{j}</td><td><span class='{step_type}'>{type_label}</span></td><td><code>{action_name}</code></td><td><code>{target}</code></td><td>{details}</td></tr>")

                    html_parts.append("  </table>")

        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

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
