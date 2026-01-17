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
        test_type = data.get("type", "screen")

        # Route to appropriate generator based on test type
        if test_type == "flow":
            return self._generate_flow_html(result)
        else:
            return self._generate_screen_html(result)

    def _generate_screen_html(self, result: ValidationResult) -> str:
        """Generate HTML documentation for screen tests."""
        data = result.test_data
        metadata = data.get("metadata", {})
        name = metadata.get("name", result.file_path.stem)
        description = metadata.get("description", "")
        title = description or name
        cases = data.get("cases", [])

        # Pre-compute case display names for sidebar
        case_displays = []
        for case in cases:
            case_name = case.get("name", "Case")
            case_desc = self._resolve_description(case)
            if isinstance(case_desc, dict) and case_desc.get("summary"):
                case_displays.append(case_desc["summary"])
            else:
                case_displays.append(case.get("description") or case_name)

        html_parts = self._get_html_header(title, case_displays)

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
                case_desc = self._resolve_description(case)
                # Use description from descriptionFile (summary) or inline description
                if isinstance(case_desc, dict) and case_desc.get("summary"):
                    case_display = case_desc["summary"]
                else:
                    case_display = case.get("description") or case_name
                case_id = f"case-{i}"

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

    def _generate_flow_html(self, result: ValidationResult) -> str:
        """Generate HTML documentation for flow tests."""
        data = result.test_data
        metadata = data.get("metadata", {})
        name = metadata.get("name", result.file_path.stem)
        description = metadata.get("description", "")
        title = description or name
        steps = data.get("steps", [])
        setup_steps = data.get("setup", [])
        teardown_steps = data.get("teardown", [])
        checkpoints = data.get("checkpoints", [])

        # Build sidebar data
        sidebar_steps = []
        for i, step in enumerate(steps, 1):
            if "file" in step:
                # File reference
                file_ref = step.get("file", "")
                case_info = step.get("case") or step.get("cases") or "all cases"
                if isinstance(case_info, list):
                    case_info = f"[{len(case_info)} cases]"
                sidebar_steps.append({
                    "num": i,
                    "type": "file",
                    "label": file_ref.split("/")[-1] if "/" in file_ref else file_ref,
                    "detail": case_info
                })
            else:
                # Inline step
                action_or_assert = step.get("action") or step.get("assert", "?")
                step_type = "action" if "action" in step else "assert"
                sidebar_steps.append({
                    "num": i,
                    "type": step_type,
                    "label": action_or_assert,
                    "detail": step.get("id", "")
                })

        html_parts = self._get_flow_html_header(title, name, sidebar_steps, checkpoints)

        # Main content wrapper
        html_parts.append("  <main class='main-content'>")
        html_parts.append(f"    <h1>{self._escape_html(title)}</h1>")
        html_parts.append(f"    <p class='test-name-label'><strong>Flow Name:</strong> <code>{self._escape_html(name)}</code></p>")

        # Test info
        html_parts.append("    <div class='info'>")
        html_parts.append(f"      <strong>Type:</strong> flow<br>")
        html_parts.append(f"      <strong>Platform:</strong> {data.get('platform', 'all')}<br>")
        html_parts.append(f"      <strong>Steps:</strong> {len(steps)}<br>")
        if setup_steps:
            html_parts.append(f"      <strong>Setup:</strong> {len(setup_steps)} steps<br>")
        if teardown_steps:
            html_parts.append(f"      <strong>Teardown:</strong> {len(teardown_steps)} steps<br>")
        if checkpoints:
            html_parts.append(f"      <strong>Checkpoints:</strong> {len(checkpoints)}<br>")
        html_parts.append(f"      <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        html_parts.append("    </div>")

        # Setup section
        if setup_steps:
            html_parts.append("    <h2>Setup</h2>")
            html_parts.append("    <div class='setup-teardown'>")
            for i, step in enumerate(setup_steps, 1):
                html_parts.extend(self._render_flow_step(i, step, "setup"))
            html_parts.append("    </div>")

        # Flow Steps
        html_parts.append("    <h2>Flow Steps</h2>")
        for i, step in enumerate(steps, 1):
            html_parts.extend(self._render_flow_step(i, step, "step"))

        # Teardown section
        if teardown_steps:
            html_parts.append("    <h2>Teardown</h2>")
            html_parts.append("    <div class='setup-teardown'>")
            for i, step in enumerate(teardown_steps, 1):
                html_parts.extend(self._render_flow_step(i, step, "teardown"))
            html_parts.append("    </div>")

        # Checkpoints section
        if checkpoints:
            html_parts.append("    <h2>Checkpoints</h2>")
            html_parts.append("    <ul class='checkpoint-list'>")
            for cp in checkpoints:
                cp_name = cp.get("name", "unnamed")
                after_step = cp.get("afterStep", 0)
                has_screenshot = cp.get("screenshot", False)
                screenshot_icon = " 📷" if has_screenshot else ""
                html_parts.append(f"      <li><strong>{self._escape_html(cp_name)}</strong> (after step {after_step + 1}){screenshot_icon}</li>")
            html_parts.append("    </ul>")

        html_parts.append("  </main>")
        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

    def _render_flow_step(self, num: int, step: dict, context: str = "step") -> list[str]:
        """Render a single flow step as HTML."""
        parts = []
        step_id = f"{context}-{num}"

        if "file" in step:
            # File reference step
            file_ref = step.get("file", "")
            case_name = step.get("case")
            cases = step.get("cases")

            parts.append(f"    <div class='flow-step file-ref' id='{step_id}'>")
            parts.append(f"      <div class='step-header'>")
            parts.append(f"        <span class='step-number'>{num}</span>")
            parts.append(f"        <span class='step-type-badge file'>📁 File Reference</span>")
            parts.append(f"      </div>")
            parts.append(f"      <div class='step-content'>")
            parts.append(f"        <div class='step-detail'><strong>File:</strong> <code>{self._escape_html(file_ref)}</code></div>")

            if case_name:
                parts.append(f"        <div class='step-detail'><strong>Case:</strong> <code>{self._escape_html(case_name)}</code></div>")
            elif cases:
                cases_str = ", ".join(cases)
                parts.append(f"        <div class='step-detail'><strong>Cases:</strong> <code>{self._escape_html(cases_str)}</code></div>")
            else:
                parts.append(f"        <div class='step-detail'><strong>Cases:</strong> <em>all cases</em></div>")

            parts.append(f"      </div>")
            parts.append(f"    </div>")

        elif "action" in step:
            # Inline action
            action = step.get("action", "?")
            target = step.get("id") or ", ".join(step.get("ids", [])) or "-"
            details = self._format_step_details(step)

            parts.append(f"    <div class='flow-step inline-action' id='{step_id}'>")
            parts.append(f"      <div class='step-header'>")
            parts.append(f"        <span class='step-number'>{num}</span>")
            parts.append(f"        <span class='step-type-badge action'>⚡ Action</span>")
            parts.append(f"      </div>")
            parts.append(f"      <div class='step-content'>")
            parts.append(f"        <div class='step-detail'><strong>Action:</strong> <code>{self._escape_html(action)}</code></div>")
            if target != "-":
                parts.append(f"        <div class='step-detail'><strong>Target:</strong> <code>{self._escape_html(target)}</code></div>")
            if details != "-":
                parts.append(f"        <div class='step-detail'><strong>Details:</strong> {self._escape_html(details)}</div>")
            parts.append(f"      </div>")
            parts.append(f"    </div>")

        elif "assert" in step:
            # Inline assertion
            assertion = step.get("assert", "?")
            target = step.get("id") or ", ".join(step.get("ids", [])) or "-"
            details = self._format_step_details(step)

            parts.append(f"    <div class='flow-step inline-assert' id='{step_id}'>")
            parts.append(f"      <div class='step-header'>")
            parts.append(f"        <span class='step-number'>{num}</span>")
            parts.append(f"        <span class='step-type-badge assert'>✓ Assert</span>")
            parts.append(f"      </div>")
            parts.append(f"      <div class='step-content'>")
            parts.append(f"        <div class='step-detail'><strong>Assert:</strong> <code>{self._escape_html(assertion)}</code></div>")
            if target != "-":
                parts.append(f"        <div class='step-detail'><strong>Target:</strong> <code>{self._escape_html(target)}</code></div>")
            if details != "-":
                parts.append(f"        <div class='step-detail'><strong>Details:</strong> {self._escape_html(details)}</div>")
            parts.append(f"      </div>")
            parts.append(f"    </div>")

        return parts

    def _get_flow_html_header(self, title: str, name: str, steps: list, checkpoints: list) -> list[str]:
        """Get HTML header with styles and sidebar for flow tests."""
        parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            f"  <title>{self._escape_html(title)} - Flow Test Documentation</title>",
            "  <meta charset='utf-8'>",
            "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
            "  <style>",
            "    * { box-sizing: border-box; }",
            "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; line-height: 1.6; display: flex; }",
            "    /* Sidebar */",
            "    .sidebar { width: 280px; min-width: 280px; height: 100vh; position: fixed; top: 0; left: 0; background: #f8f9fa; border-right: 1px solid #e0e0e0; overflow-y: auto; padding: 20px; }",
            "    .sidebar h2 { font-size: 1em; color: #333; margin: 0 0 15px 0; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0; }",
            "    .sidebar-section { margin-bottom: 20px; }",
            "    .sidebar-title { font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }",
            "    .sidebar ul { list-style: none; padding: 0; margin: 0; }",
            "    .sidebar li { margin: 4px 0; }",
            "    .sidebar a { display: flex; align-items: center; padding: 8px 12px; color: #555; text-decoration: none; border-radius: 6px; font-size: 0.85em; transition: all 0.2s; }",
            "    .sidebar a:hover { background: #e9ecef; color: #007AFF; }",
            "    .step-num { flex-shrink: 0; width: 22px; height: 22px; line-height: 22px; text-align: center; background: #e0e0e0; border-radius: 50%; font-size: 0.7em; font-weight: 600; margin-right: 8px; }",
            "    .step-icon { margin-right: 6px; font-size: 0.9em; }",
            "    .step-icon.file { color: #1976d2; }",
            "    .step-icon.action { color: #007AFF; }",
            "    .step-icon.assert { color: #34C759; }",
            "    .step-label { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }",
            "    .back-link { display: block; padding: 10px 12px; margin-bottom: 15px; color: #007AFF; font-size: 0.9em; border-bottom: 1px solid #e0e0e0; }",
            "    .back-link:hover { background: #e9ecef; }",
            "    .checkpoint-item { padding: 6px 12px; color: #666; font-size: 0.85em; display: flex; align-items: center; }",
            "    .checkpoint-item::before { content: '🏁'; margin-right: 8px; }",
            "    /* Main content */",
            "    .main-content { margin-left: 280px; padding: 30px 40px; max-width: 900px; flex: 1; }",
            "    h1 { color: #333; border-bottom: 2px solid #7b1fa2; padding-bottom: 10px; margin-top: 0; }",
            "    h2 { color: #555; margin-top: 30px; }",
            "    .info { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }",
            "    .test-name-label { color: #888; font-size: 0.9em; margin: -5px 0 15px 0; }",
            "    .test-name-label code { background: #f5f5f5; color: #666; }",
            "    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }",
            "    /* Flow steps */",
            "    .flow-step { background: #fff; border-radius: 8px; margin: 12px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }",
            "    .flow-step.file-ref { border-left: 4px solid #1976d2; }",
            "    .flow-step.inline-action { border-left: 4px solid #007AFF; }",
            "    .flow-step.inline-assert { border-left: 4px solid #34C759; }",
            "    .step-header { display: flex; align-items: center; padding: 12px 15px; background: #f8f9fa; border-bottom: 1px solid #eee; }",
            "    .step-number { width: 28px; height: 28px; line-height: 28px; text-align: center; background: #7b1fa2; color: white; border-radius: 50%; font-size: 0.85em; font-weight: 600; margin-right: 12px; }",
            "    .step-type-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }",
            "    .step-type-badge.file { background: #e3f2fd; color: #1976d2; }",
            "    .step-type-badge.action { background: #e3f2fd; color: #007AFF; }",
            "    .step-type-badge.assert { background: #e8f5e9; color: #34C759; }",
            "    .step-content { padding: 15px; }",
            "    .step-detail { margin: 6px 0; }",
            "    .step-detail strong { color: #555; }",
            "    /* Setup/Teardown */",
            "    .setup-teardown { background: #fffbf0; border-radius: 8px; padding: 10px; margin: 10px 0; }",
            "    .setup-teardown .flow-step { margin: 8px 0; box-shadow: none; border: 1px solid #eee; }",
            "    /* Checkpoints */",
            "    .checkpoint-list { list-style: none; padding: 0; }",
            "    .checkpoint-list li { padding: 10px 15px; background: #f3e5f5; border-radius: 6px; margin: 8px 0; }",
            "    /* Responsive */",
            "    @media (max-width: 768px) {",
            "      .sidebar { display: none; }",
            "      .main-content { margin-left: 0; padding: 20px; }",
            "    }",
            "  </style>",
            "</head>",
            "<body>",
        ]

        # Sidebar
        parts.append("  <nav class='sidebar'>")
        parts.append("    <a href='../index.html' class='back-link'>&larr; Back to Index</a>")
        parts.append(f"    <h2>{self._escape_html(name)}</h2>")

        # Steps section
        if steps:
            parts.append("    <div class='sidebar-section'>")
            parts.append("      <div class='sidebar-title'>Steps</div>")
            parts.append("      <ul>")
            for step in steps:
                step_num = step["num"]
                step_type = step["type"]
                label = step["label"]

                if step_type == "file":
                    icon_class = "file"
                    icon = "📁"
                elif step_type == "action":
                    icon_class = "action"
                    icon = "⚡"
                else:
                    icon_class = "assert"
                    icon = "✓"

                parts.append(f"        <li><a href='#step-{step_num}'><span class='step-num'>{step_num}</span><span class='step-icon {icon_class}'>{icon}</span><span class='step-label'>{self._escape_html(label)}</span></a></li>")
            parts.append("      </ul>")
            parts.append("    </div>")

        # Checkpoints section
        if checkpoints:
            parts.append("    <div class='sidebar-section'>")
            parts.append("      <div class='sidebar-title'>Checkpoints</div>")
            for cp in checkpoints:
                cp_name = cp.get("name", "unnamed")
                parts.append(f"      <div class='checkpoint-item'>{self._escape_html(cp_name)}</div>")
            parts.append("    </div>")

        parts.append("  </nav>")

        return parts

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
            for i, case_display in enumerate(cases, 1):
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


def _escape_html_index(text: str) -> str:
    """Escape HTML special characters for index page."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _generate_index_html(output_dir: Path, files: list[dict], title: str):
    """Generate index.html with collapsible categories and sidebar navigation."""
    screen_files = [f for f in files if f['type'] == 'screen']
    flow_files = [f for f in files if f['type'] == 'flow']
    other_files = [f for f in files if f['type'] not in ['screen', 'flow']]

    screen_count = len(screen_files)
    flow_count = len(flow_files)
    total_cases = sum(f['case_count'] for f in files)
    total_steps = sum(f['step_count'] for f in files)

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        f"  <title>{_escape_html_index(title)}</title>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "  <style>",
        "    * { box-sizing: border-box; }",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; line-height: 1.6; display: flex; background: #fafafa; }",
        "    /* Sidebar */",
        "    .sidebar { width: 260px; min-width: 260px; height: 100vh; position: fixed; top: 0; left: 0; background: #fff; border-right: 1px solid #e0e0e0; overflow-y: auto; padding: 20px; }",
        "    .sidebar h2 { font-size: 1.1em; color: #333; margin: 0 0 20px 0; padding-bottom: 10px; border-bottom: 2px solid #007AFF; }",
        "    .sidebar-section { margin-bottom: 20px; }",
        "    .sidebar-title { font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; background: #f5f5f5; border-radius: 6px; }",
        "    .sidebar-title:hover { background: #e9ecef; }",
        "    .sidebar-title .count { background: #007AFF; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; }",
        "    .sidebar-title.flow .count { background: #7b1fa2; }",
        "    .sidebar ul { list-style: none; padding: 0; margin: 0; }",
        "    .sidebar li { margin: 2px 0; }",
        "    .sidebar a { display: block; padding: 6px 12px; color: #555; text-decoration: none; border-radius: 4px; font-size: 0.85em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }",
        "    .sidebar a:hover { background: #e9ecef; color: #007AFF; }",
        "    /* Main content */",
        "    .main-content { margin-left: 260px; padding: 30px 40px; flex: 1; max-width: 900px; }",
        "    h1 { color: #333; border-bottom: 2px solid #007AFF; padding-bottom: 10px; margin-top: 0; }",
        "    .summary { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; display: flex; flex-wrap: wrap; gap: 20px; }",
        "    .summary-item { text-align: center; min-width: 80px; }",
        "    .summary-value { font-size: 2em; font-weight: bold; color: #007AFF; }",
        "    .summary-label { color: #666; font-size: 0.9em; }",
        "    /* Collapsible category */",
        "    .category { margin-bottom: 25px; }",
        "    .category-header { display: flex; align-items: center; justify-content: space-between; background: #fff; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: pointer; user-select: none; }",
        "    .category-header:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.15); }",
        "    .category-header h2 { margin: 0; color: #333; font-size: 1.2em; display: flex; align-items: center; gap: 10px; }",
        "    .category-header .arrow { transition: transform 0.3s; font-size: 0.8em; color: #666; }",
        "    .category-header.collapsed .arrow { transform: rotate(-90deg); }",
        "    .category-badge { padding: 4px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 600; }",
        "    .category-badge.screen { background: #e3f2fd; color: #1976d2; }",
        "    .category-badge.flow { background: #f3e5f5; color: #7b1fa2; }",
        "    .category-content { max-height: 2000px; overflow: hidden; transition: max-height 0.3s ease-out; }",
        "    .category-content.collapsed { max-height: 0; }",
        "    .test-list { list-style: none; padding: 0; margin: 10px 0 0 0; }",
        "    .test-item { background: #fff; margin: 8px 0; padding: 15px 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid transparent; }",
        "    .test-item:hover { box-shadow: 0 2px 6px rgba(0,0,0,0.12); }",
        "    .test-item.screen { border-left-color: #1976d2; }",
        "    .test-item.flow { border-left-color: #7b1fa2; }",
        "    .test-name { font-size: 1.05em; font-weight: 600; color: #333; text-decoration: none; }",
        "    .test-name:hover { color: #007AFF; }",
        "    .test-meta { margin-top: 5px; color: #666; font-size: 0.85em; }",
        "    .test-description { color: #555; margin-top: 5px; font-size: 0.9em; }",
        "    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; margin-right: 5px; }",
        "    .badge-screen { background: #e3f2fd; color: #1976d2; }",
        "    .badge-flow { background: #f3e5f5; color: #7b1fa2; }",
        "    .badge-platform { background: #e8f5e9; color: #388e3c; }",
        "    .generated { color: #999; font-size: 0.85em; margin-top: 30px; text-align: center; }",
        "    /* Responsive */",
        "    @media (max-width: 768px) {",
        "      .sidebar { display: none; }",
        "      .main-content { margin-left: 0; padding: 20px; }",
        "    }",
        "  </style>",
        "  <script>",
        "    function toggleCategory(id) {",
        "      const header = document.getElementById(id + '-header');",
        "      const content = document.getElementById(id + '-content');",
        "      header.classList.toggle('collapsed');",
        "      content.classList.toggle('collapsed');",
        "    }",
        "  </script>",
        "</head>",
        "<body>",
    ]

    # Sidebar
    html_parts.append("  <nav class='sidebar'>")
    html_parts.append(f"    <h2>{_escape_html_index(title)}</h2>")

    # Sidebar - Screen Tests
    if screen_files:
        html_parts.append("    <div class='sidebar-section'>")
        html_parts.append(f"      <div class='sidebar-title' onclick=\"toggleCategory('screens')\">Screen Tests <span class='count'>{screen_count}</span></div>")
        html_parts.append("      <ul>")
        for f in screen_files:
            html_parts.append(f"        <li><a href='{f['path']}' title='{_escape_html_index(f['name'])}'>{_escape_html_index(f['name'])}</a></li>")
        html_parts.append("      </ul>")
        html_parts.append("    </div>")

    # Sidebar - Flow Tests
    if flow_files:
        html_parts.append("    <div class='sidebar-section'>")
        html_parts.append(f"      <div class='sidebar-title flow' onclick=\"toggleCategory('flows')\">Flow Tests <span class='count'>{flow_count}</span></div>")
        html_parts.append("      <ul>")
        for f in flow_files:
            html_parts.append(f"        <li><a href='{f['path']}' title='{_escape_html_index(f['name'])}'>{_escape_html_index(f['name'])}</a></li>")
        html_parts.append("      </ul>")
        html_parts.append("    </div>")

    html_parts.append("  </nav>")

    # Main content
    html_parts.append("  <main class='main-content'>")
    html_parts.append(f"    <h1>{_escape_html_index(title)}</h1>")

    # Summary section
    html_parts.extend([
        "    <div class='summary'>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{len(files)}</div>",
        "        <div class='summary-label'>Test Files</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{screen_count}</div>",
        "        <div class='summary-label'>Screen Tests</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{flow_count}</div>",
        "        <div class='summary-label'>Flow Tests</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{total_cases}</div>",
        "        <div class='summary-label'>Test Cases</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{total_steps}</div>",
        "        <div class='summary-label'>Total Steps</div>",
        "      </div>",
        "    </div>",
    ])

    # Screen Tests category (collapsible)
    if screen_files:
        html_parts.extend([
            "    <div class='category'>",
            "      <div class='category-header' id='screens-header' onclick=\"toggleCategory('screens')\">",
            f"        <h2><span class='arrow'>▼</span> Screen Tests <span class='category-badge screen'>{screen_count}</span></h2>",
            "      </div>",
            "      <div class='category-content' id='screens-content'>",
            "        <ul class='test-list'>",
        ])
        for f in screen_files:
            html_parts.extend([
                "          <li class='test-item screen'>",
                f"            <a href='{f['path']}' class='test-name'>{_escape_html_index(f['name'])}</a>",
                "            <div class='test-meta'>",
                f"              <span class='badge badge-platform'>{f['platform']}</span>",
                f"              {f['case_count']} cases, {f['step_count']} steps",
                "            </div>",
            ])
            if f['description']:
                html_parts.append(f"            <div class='test-description'>{_escape_html_index(f['description'])}</div>")
            html_parts.append("          </li>")
        html_parts.extend([
            "        </ul>",
            "      </div>",
            "    </div>",
        ])

    # Flow Tests category (collapsible)
    if flow_files:
        html_parts.extend([
            "    <div class='category'>",
            "      <div class='category-header' id='flows-header' onclick=\"toggleCategory('flows')\">",
            f"        <h2><span class='arrow'>▼</span> Flow Tests <span class='category-badge flow'>{flow_count}</span></h2>",
            "      </div>",
            "      <div class='category-content' id='flows-content'>",
            "        <ul class='test-list'>",
        ])
        for f in flow_files:
            html_parts.extend([
                "          <li class='test-item flow'>",
                f"            <a href='{f['path']}' class='test-name'>{_escape_html_index(f['name'])}</a>",
                "            <div class='test-meta'>",
                f"              <span class='badge badge-platform'>{f['platform']}</span>",
                f"              {f['step_count']} steps",
                "            </div>",
            ])
            if f['description']:
                html_parts.append(f"            <div class='test-description'>{_escape_html_index(f['description'])}</div>")
            html_parts.append("          </li>")
        html_parts.extend([
            "        </ul>",
            "      </div>",
            "    </div>",
        ])

    # Other Tests category (collapsible)
    if other_files:
        html_parts.extend([
            "    <div class='category'>",
            "      <div class='category-header' id='other-header' onclick=\"toggleCategory('other')\">",
            f"        <h2><span class='arrow'>▼</span> Other Tests <span class='category-badge'>{len(other_files)}</span></h2>",
            "      </div>",
            "      <div class='category-content' id='other-content'>",
            "        <ul class='test-list'>",
        ])
        for f in other_files:
            html_parts.extend([
                "          <li class='test-item'>",
                f"            <a href='{f['path']}' class='test-name'>{_escape_html_index(f['name'])}</a>",
                "            <div class='test-meta'>",
                f"              <span class='badge'>{f['type']}</span>",
                f"              <span class='badge badge-platform'>{f['platform']}</span>",
                "            </div>",
            ])
            if f['description']:
                html_parts.append(f"            <div class='test-description'>{_escape_html_index(f['description'])}</div>")
            html_parts.append("          </li>")
        html_parts.extend([
            "        </ul>",
            "      </div>",
            "    </div>",
        ])

    # Footer
    html_parts.extend([
        f"    <p class='generated'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        "  </main>",
        "</body>",
        "</html>",
    ])

    # Write index.html
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_parts))

    print(f"  Generated: {index_path}")
