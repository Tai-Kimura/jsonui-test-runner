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

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single test file."""
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

        self._validate_test(data, str(file_path), result)
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

        # Check for unknown keys
        for key in case.keys():
            if key not in VALID_CASE_KEYS:
                result.warnings.append(ValidationMessage(
                    path=path,
                    message=f"Unknown case key: {key}",
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

        # Warn about selectOption with index on iOS
        if action == "selectOption" and "index" in step:
            # Check if test is targeting iOS
            test_data = result.test_data
            platform = test_data.get("platform") if test_data else None
            is_ios_only = platform == "ios" or (isinstance(platform, list) and platform == ["ios"])

            result.warnings.append(ValidationMessage(
                path=path,
                message="selectOption with 'index' is not supported on iOS. Use 'label' or 'value' instead for iOS compatibility.",
                level="warning"
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
