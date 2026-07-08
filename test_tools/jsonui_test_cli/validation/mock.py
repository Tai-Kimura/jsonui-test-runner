"""Validation for *.mock.json definition files.

Handwritten (mirrors screen.py / flow.py); the CLI does not depend on jsonschema.
schemas/mock.schema.json is an editor/doc asset, not the validation mechanism.
"""

from __future__ import annotations

from .models import ValidationMessage, ValidationResult

VALID_MOCK_KEYS = ["$schema", "source", "activeScenario", "scenarios"]
VALID_SOURCE_KEYS = ["swagger", "operationId", "method", "path"]
VALID_SCENARIO_KEYS = ["status", "headers", "body", "delayMs", "contentType", "bodyFile"]
VALID_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]


class MockValidator:
    """Validates a single mock definition file."""

    def validate(self, data, path: str, result: ValidationResult):
        if not isinstance(data, dict):
            result.errors.append(ValidationMessage(path=path, message="Mock file must be a JSON object"))
            return

        for key in data:
            if key not in VALID_MOCK_KEYS:
                result.warnings.append(ValidationMessage(
                    path=path, message=f"Unknown mock key: {key}", level="warning"))

        source = data.get("source")
        if not isinstance(source, dict):
            result.errors.append(ValidationMessage(path=f"{path}.source", message="'source' is required and must be an object"))
        else:
            for key in source:
                if key not in VALID_SOURCE_KEYS:
                    result.warnings.append(ValidationMessage(
                        path=f"{path}.source", message=f"Unknown source key: {key}", level="warning"))
            method = source.get("method")
            if method and method.upper() not in VALID_METHODS:
                result.errors.append(ValidationMessage(
                    path=f"{path}.source.method", message=f"Invalid method: {method}"))
            if not source.get("path"):
                result.errors.append(ValidationMessage(
                    path=f"{path}.source.path", message="'source.path' is required for routing"))

        scenarios = data.get("scenarios")
        if not isinstance(scenarios, dict) or not scenarios:
            result.errors.append(ValidationMessage(
                path=f"{path}.scenarios", message="'scenarios' is required and must be a non-empty object"))
            return

        for name, scenario in scenarios.items():
            spath = f"{path}.scenarios.{name}"
            if not isinstance(scenario, dict):
                result.errors.append(ValidationMessage(path=spath, message="scenario must be an object"))
                continue
            for key in scenario:
                if key not in VALID_SCENARIO_KEYS:
                    result.warnings.append(ValidationMessage(
                        path=spath, message=f"Unknown scenario key: {key}", level="warning"))
            status = scenario.get("status")
            if not isinstance(status, int) or not (100 <= status <= 599):
                result.errors.append(ValidationMessage(
                    path=f"{spath}.status", message=f"'status' must be an HTTP status int, got: {status!r}"))
            if "delayMs" in scenario and not isinstance(scenario["delayMs"], (int, float)):
                result.errors.append(ValidationMessage(
                    path=f"{spath}.delayMs", message="'delayMs' must be a number"))

        active = data.get("activeScenario", "default")
        if active not in scenarios:
            result.errors.append(ValidationMessage(
                path=f"{path}.activeScenario",
                message=f"activeScenario '{active}' is not among scenarios: {list(scenarios.keys())}"))
