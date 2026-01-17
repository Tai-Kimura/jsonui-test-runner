"""Validator for JsonUI test files."""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from .schema import (
    SUPPORTED_ACTIONS,
    SUPPORTED_ASSERTIONS,
    VALID_DIRECTIONS,
    VALID_TOP_LEVEL_KEYS,
    VALID_CASE_KEYS,
    VALID_STEP_KEYS,
    VALID_DESCRIPTION_KEYS,
)


@dataclass
class ValidationMessage:
    """Represents a validation error or warning."""
    path: str
    message: str
    level: str = "error"  # "error" or "warning"

    def __str__(self):
        prefix = "ERROR" if self.level == "error" else "WARN"
        return f"  [{prefix}] {self.path}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validating a test file."""
    file_path: Path
    errors: list[ValidationMessage] = field(default_factory=list)
    warnings: list[ValidationMessage] = field(default_factory=list)
    test_data: dict | None = None

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


class TestValidator:
    """Validates JsonUI test files."""

    def __init__(self):
        self._test_file_path: Path | None = None

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single test or description file."""
        self._test_file_path = Path(file_path).resolve()
        result = ValidationResult(file_path=file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result.test_data = data
        except json.JSONDecodeError as e:
            result.errors.append(ValidationMessage(
                path=str(file_path),
                message=f"Invalid JSON: {e}"
            ))
            return result
        except Exception as e:
            result.errors.append(ValidationMessage(
                path=str(file_path),
                message=f"Cannot read file: {e}"
            ))
            return result

        # Determine file type by extension or content
        file_name = file_path.name
        if file_name.endswith('.test.json'):
            self._validate_test(data, str(file_path), result)
        elif 'case_name' in data or (file_path.parent.name == 'descriptions'):
            # Description file (has case_name or is in descriptions folder)
            self._validate_description(data, str(file_path), result)
        elif 'type' in data and data['type'] in ['screen', 'flow']:
            # Test file without .test.json extension
            self._validate_test(data, str(file_path), result)
        else:
            result.errors.append(ValidationMessage(
                path=str(file_path),
                message="Unknown file type: expected test file (.test.json) or description file"
            ))

        return result

    def validate_data(self, data: dict, name: str = "test") -> ValidationResult:
        """Validate test data directly (for testing)."""
        result = ValidationResult(file_path=Path(name))
        result.test_data = data
        self._validate_test(data, name, result)
        return result

    def _validate_test(self, data: dict, path: str, result: ValidationResult):
        """Validate test structure."""
        test_type = data.get("type")

        if test_type == "screen":
            self._validate_screen_test(data, path, result)
        elif test_type == "flow":
            self._validate_flow_test(data, path, result)
        else:
            result.errors.append(ValidationMessage(
                path=path,
                message=f"Unknown or missing test type: {test_type}"
            ))

    def _validate_screen_test(self, data: dict, path: str, result: ValidationResult):
        """Validate screen test structure."""
        # Check for unknown top-level keys
        for key in data.keys():
            if key not in VALID_TOP_LEVEL_KEYS:
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Unknown top-level key: {key}",
                    level="warning"
                ))

        # Check required fields
        if "metadata" not in data:
            result.warnings.append(ValidationMessage(
                path=path,
                message="Missing 'metadata' field",
                level="warning"
            ))

        # Validate cases
        cases = data.get("cases", [])
        if not cases:
            result.warnings.append(ValidationMessage(
                path=path,
                message="No test cases defined",
                level="warning"
            ))

        for i, case in enumerate(cases):
            case_path = f"{path}.cases[{i}]"
            self._validate_case(case, case_path, result)

        # Validate setup/teardown if present
        for section in ["setup", "teardown"]:
            if section in data:
                for i, step in enumerate(data[section]):
                    step_path = f"{path}.{section}[{i}]"
                    self._validate_step(step, step_path, result)

    def _validate_flow_test(self, data: dict, path: str, result: ValidationResult):
        """Validate flow test structure."""
        # Validate steps
        steps = data.get("steps", [])
        if not steps:
            result.warnings.append(ValidationMessage(
                path=path,
                message="No steps defined in flow test",
                level="warning"
            ))

        for i, step in enumerate(steps):
            step_path = f"{path}.steps[{i}]"
            self._validate_step(step, step_path, result, is_flow=True)

    def _validate_case(self, case: dict, path: str, result: ValidationResult):
        """Validate a test case."""
        # Check required fields
        if "name" not in case:
            result.errors.append(ValidationMessage(
                path=path,
                message="Test case missing 'name' field"
            ))

        # Warn if description is missing (recommended for HTML sidebar display)
        if "description" not in case:
            case_name = case.get("name", "unknown")
            result.warnings.append(ValidationMessage(
                path=path,
                message=f"Test case '{case_name}' missing 'description' field (recommended for HTML documentation)",
                level="warning"
            ))

        # Check for unknown keys
        for key in case.keys():
            if key not in VALID_CASE_KEYS:
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Unknown case key: {key}",
                    level="warning"
                ))

        # Validate descriptionFile if present
        if "descriptionFile" in case and self._test_file_path:
            desc_file_path = case["descriptionFile"]
            # Resolve relative to test file location
            if not Path(desc_file_path).is_absolute():
                desc_file_path = self._test_file_path.parent / desc_file_path

            desc_path = Path(desc_file_path)
            if not desc_path.exists():
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Description file not found: {case['descriptionFile']}",
                    level="warning"
                ))

        # Validate steps
        steps = case.get("steps", [])
        if not steps:
            result.warnings.append(ValidationMessage(
                path=path,
                message="Test case has no steps",
                level="warning"
            ))

        for i, step in enumerate(steps):
            step_path = f"{path}.steps[{i}]"
            self._validate_step(step, step_path, result)

    def _validate_step(self, step: dict, path: str, result: ValidationResult, is_flow: bool = False):
        """Validate a test step."""
        # Check for file reference step (flow tests only)
        if "file" in step:
            if not is_flow:
                result.errors.append(ValidationMessage(
                    path=path,
                    message="File reference steps are only allowed in flow tests"
                ))
                return
            self._validate_file_step(step, path, result)
            return

        # Check for block step (flow tests only)
        if "block" in step:
            if not is_flow:
                result.errors.append(ValidationMessage(
                    path=path,
                    message="Block steps are only allowed in flow tests"
                ))
                return
            self._validate_block_step(step, path, result)
            return

        # Check for unknown keys
        for key in step.keys():
            if key not in VALID_STEP_KEYS:
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Unknown step key: {key}",
                    level="warning"
                ))

        action = step.get("action")
        assertion = step.get("assert")

        if action and assertion:
            result.errors.append(ValidationMessage(
                path=path,
                message="Step cannot have both 'action' and 'assert'"
            ))
        elif action:
            self._validate_action(step, path, result)
        elif assertion:
            self._validate_assertion(step, path, result)
        else:
            result.errors.append(ValidationMessage(
                path=path,
                message="Step must have either 'action' or 'assert'"
            ))

    def _validate_file_step(self, step: dict, path: str, result: ValidationResult):
        """Validate a file reference step in flow tests."""
        file_ref = step["file"]

        # Validate file reference format
        if not isinstance(file_ref, str) or not file_ref.strip():
            result.errors.append(ValidationMessage(
                path=path,
                message="'file' must be a non-empty string"
            ))
            return

        # Check for valid keys in file step
        valid_file_step_keys = {"file", "case", "cases"}
        for key in step.keys():
            if key not in valid_file_step_keys:
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Unknown key in file step: {key}",
                    level="warning"
                ))

        # Cannot have both 'case' and 'cases'
        if "case" in step and "cases" in step:
            result.errors.append(ValidationMessage(
                path=path,
                message="File step cannot have both 'case' and 'cases'"
            ))

        # Validate 'case' is a string
        if "case" in step:
            if not isinstance(step["case"], str) or not step["case"].strip():
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'case' must be a non-empty string"
                ))

        # Validate 'cases' is a non-empty list of strings
        if "cases" in step:
            cases = step["cases"]
            if not isinstance(cases, list) or len(cases) == 0:
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'cases' must be a non-empty array"
                ))
            elif not all(isinstance(c, str) and c.strip() for c in cases):
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'cases' must be an array of non-empty strings"
                ))

        # Try to resolve the file path and validate it exists
        if self._test_file_path:
            resolved_path = self._resolve_file_reference(file_ref)
            if resolved_path and not resolved_path.exists():
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Referenced test file not found: {file_ref} (looked for {resolved_path})",
                    level="warning"
                ))

    def _resolve_file_reference(self, file_ref: str) -> Path | None:
        """Resolve a file reference to an actual path."""
        if not self._test_file_path:
            return None

        base_dir = self._test_file_path.parent

        # Try different file extensions
        candidates = [
            base_dir / f"{file_ref}.test.json",
            base_dir / f"{file_ref}.json",
            base_dir / file_ref,
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        # Return first candidate for error message
        return candidates[0]

    def _validate_block_step(self, step: dict, path: str, result: ValidationResult):
        """Validate a block step in flow tests."""
        block_name = step["block"]

        # Validate block name is non-empty string
        if not isinstance(block_name, str) or not block_name.strip():
            result.errors.append(ValidationMessage(
                path=path,
                message="'block' must be a non-empty string"
            ))
            return

        # Check for valid keys in block step
        valid_block_step_keys = {"block", "description", "descriptionFile", "steps"}
        for key in step.keys():
            if key not in valid_block_step_keys:
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Unknown key in block step: {key}",
                    level="warning"
                ))

        # Validate steps is required and non-empty
        if "steps" not in step:
            result.errors.append(ValidationMessage(
                path=path,
                message="Block step must have 'steps' array"
            ))
            return

        steps = step["steps"]
        if not isinstance(steps, list) or len(steps) == 0:
            result.errors.append(ValidationMessage(
                path=path,
                message="Block 'steps' must be a non-empty array"
            ))
            return

        # Validate each step in the block (inline steps only, no nested blocks/files)
        for i, inner_step in enumerate(steps):
            inner_step_path = f"{path}.steps[{i}]"
            # Block steps can only contain action/assert steps, not file references or nested blocks
            if "file" in inner_step:
                result.errors.append(ValidationMessage(
                    path=inner_step_path,
                    message="File references are not allowed inside block steps"
                ))
            elif "block" in inner_step:
                result.errors.append(ValidationMessage(
                    path=inner_step_path,
                    message="Nested blocks are not allowed inside block steps"
                ))
            else:
                self._validate_step(inner_step, inner_step_path, result, is_flow=False)

        # Validate descriptionFile if present
        if "descriptionFile" in step and self._test_file_path:
            desc_file_path = step["descriptionFile"]
            # Resolve relative to test file location
            if not Path(desc_file_path).is_absolute():
                desc_file_path = self._test_file_path.parent / desc_file_path

            desc_path = Path(desc_file_path)
            if not desc_path.exists():
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Description file not found: {step['descriptionFile']}",
                    level="warning"
                ))

    def _validate_action(self, step: dict, path: str, result: ValidationResult):
        """Validate an action step."""
        action = step["action"]

        if action not in SUPPORTED_ACTIONS:
            result.errors.append(ValidationMessage(
                path=path,
                message=f"Unsupported action: {action}"
            ))
            return

        spec = SUPPORTED_ACTIONS[action]

        # Check required parameters
        for param in spec["required"]:
            if param not in step:
                result.errors.append(ValidationMessage(
                    path=path,
                    message=f"Missing required parameter '{param}' for action '{action}'"
                ))

        # Validate direction if present
        if "direction" in step and step["direction"] not in VALID_DIRECTIONS:
            result.errors.append(ValidationMessage(
                path=path,
                message=f"Invalid direction: {step['direction']}. Must be one of: {VALID_DIRECTIONS}"
            ))

        # Validate timeout is positive
        if "timeout" in step:
            timeout = step["timeout"]
            if not isinstance(timeout, int) or timeout <= 0:
                result.errors.append(ValidationMessage(
                    path=path,
                    message=f"Timeout must be a positive integer (ms), got: {timeout}"
                ))

        # Validate ms is positive
        if "ms" in step:
            ms = step["ms"]
            if not isinstance(ms, int) or ms <= 0:
                result.errors.append(ValidationMessage(
                    path=path,
                    message=f"ms must be a positive integer, got: {ms}"
                ))

        # Validate ids is a non-empty list
        if "ids" in step:
            ids = step["ids"]
            if not isinstance(ids, list) or len(ids) == 0:
                result.errors.append(ValidationMessage(
                    path=path,
                    message="ids must be a non-empty array"
                ))


    def _validate_assertion(self, step: dict, path: str, result: ValidationResult):
        """Validate an assertion step."""
        assertion = step["assert"]

        if assertion not in SUPPORTED_ASSERTIONS:
            result.errors.append(ValidationMessage(
                path=path,
                message=f"Unsupported assertion: {assertion}"
            ))
            return

        spec = SUPPORTED_ASSERTIONS[assertion]

        # Check required parameters
        for param in spec["required"]:
            if param not in step:
                result.errors.append(ValidationMessage(
                    path=path,
                    message=f"Missing required parameter '{param}' for assertion '{assertion}'"
                ))

        # For text assertion, must have equals or contains
        if assertion == "text":
            if "equals" not in step and "contains" not in step:
                result.errors.append(ValidationMessage(
                    path=path,
                    message="Text assertion must have 'equals' or 'contains'"
                ))

    def _validate_description(self, data: dict, path: str, result: ValidationResult):
        """Validate a description file."""
        # Check required field
        if "case_name" not in data:
            result.errors.append(ValidationMessage(
                path=path,
                message="Description file missing required 'case_name' field"
            ))

        # Check for unknown keys
        for key in data.keys():
            if key not in VALID_DESCRIPTION_KEYS:
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Unknown description key: {key}",
                    level="warning"
                ))

        # Validate case_name is non-empty string
        if "case_name" in data:
            case_name = data["case_name"]
            if not isinstance(case_name, str) or not case_name.strip():
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'case_name' must be a non-empty string"
                ))

        # Validate summary is string if present
        if "summary" in data and not isinstance(data["summary"], str):
            result.errors.append(ValidationMessage(
                path=path,
                message="'summary' must be a string"
            ))

        # Validate preconditions is array of strings if present
        if "preconditions" in data:
            preconditions = data["preconditions"]
            if not isinstance(preconditions, list):
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'preconditions' must be an array"
                ))
            elif not all(isinstance(item, str) for item in preconditions):
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'preconditions' must be an array of strings"
                ))

        # Validate test_procedure is array of strings if present
        if "test_procedure" in data:
            test_procedure = data["test_procedure"]
            if not isinstance(test_procedure, list):
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'test_procedure' must be an array"
                ))
            elif not all(isinstance(item, str) for item in test_procedure):
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'test_procedure' must be an array of strings"
                ))

        # Validate expected_results is array of strings if present
        if "expected_results" in data:
            expected_results = data["expected_results"]
            if not isinstance(expected_results, list):
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'expected_results' must be an array"
                ))
            elif not all(isinstance(item, str) for item in expected_results):
                result.errors.append(ValidationMessage(
                    path=path,
                    message="'expected_results' must be an array of strings"
                ))

        # Validate notes is string if present
        if "notes" in data and not isinstance(data["notes"], str):
            result.errors.append(ValidationMessage(
                path=path,
                message="'notes' must be a string"
            ))
