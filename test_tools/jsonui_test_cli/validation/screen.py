"""Screen test validation."""

from __future__ import annotations

from pathlib import Path

from .models import ValidationMessage, ValidationResult
from .step import StepValidator
from ..schema import VALID_TOP_LEVEL_KEYS, VALID_CASE_KEYS


class ScreenTestValidator:
    """Validates screen test structure."""

    def __init__(self, step_validator: StepValidator):
        self._step_validator = step_validator
        self._test_file_path: Path | None = None

    def set_test_file_path(self, path: Path | None):
        """Set the test file path for resolving relative paths."""
        self._test_file_path = path
        self._step_validator.set_test_file_path(path)

    def validate(self, data: dict, path: str, result: ValidationResult):
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
                    self._step_validator.validate_step(step, step_path, result)

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
            self._step_validator.validate_step(step, step_path, result)
