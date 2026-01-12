"""Tests for the validator module."""

import pytest
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonui_test_cli.validator import TestValidator, ValidationResult


class TestValidatorBasics:
    """Basic validator tests."""

    def setup_method(self):
        self.validator = TestValidator()

    def test_valid_screen_test(self):
        """Test validation of a valid screen test."""
        data = {
            "type": "screen",
            "source": {"layout": "layouts/test.json"},
            "metadata": {"name": "test", "description": "Test"},
            "platform": "ios",
            "cases": [
                {
                    "name": "test_case",
                    "steps": [
                        {"action": "waitFor", "id": "element_id", "timeout": 5000},
                        {"assert": "visible", "id": "element_id"}
                    ]
                }
            ]
        }

        result = self.validator.validate_data(data)
        assert result.is_valid
        assert result.error_count == 0

    def test_missing_type(self):
        """Test validation fails without type."""
        data = {
            "metadata": {"name": "test"},
            "cases": []
        }

        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert result.error_count > 0

    def test_unknown_type(self):
        """Test validation fails with unknown type."""
        data = {
            "type": "unknown_type",
            "cases": []
        }

        result = self.validator.validate_data(data)
        assert not result.is_valid


class TestActionValidation:
    """Tests for action validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def _make_test(self, steps: list) -> dict:
        return {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"name": "case1", "steps": steps}]
        }

    def test_valid_tap_action(self):
        """Test valid tap action."""
        data = self._make_test([{"action": "tap", "id": "button_id"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_tap_missing_id(self):
        """Test tap action without id fails."""
        data = self._make_test([{"action": "tap"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("Missing required parameter 'id'" in str(e) for e in result.errors)

    def test_valid_input_action(self):
        """Test valid input action."""
        data = self._make_test([{"action": "input", "id": "text_field", "value": "hello"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_input_missing_value(self):
        """Test input action without value fails."""
        data = self._make_test([{"action": "input", "id": "text_field"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_valid_scroll_action(self):
        """Test valid scroll action."""
        data = self._make_test([{"action": "scroll", "id": "list_view", "direction": "down"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_scroll_invalid_direction(self):
        """Test scroll with invalid direction fails."""
        data = self._make_test([{"action": "scroll", "id": "list_view", "direction": "diagonal"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_valid_waitFor_action(self):
        """Test valid waitFor action."""
        data = self._make_test([{"action": "waitFor", "id": "element_id", "timeout": 10000}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_waitForAny_action(self):
        """Test valid waitForAny action."""
        data = self._make_test([{"action": "waitForAny", "ids": ["elem1", "elem2"], "timeout": 5000}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_waitForAny_empty_ids(self):
        """Test waitForAny with empty ids fails."""
        data = self._make_test([{"action": "waitForAny", "ids": []}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_waitForAny_missing_ids(self):
        """Test waitForAny without ids fails."""
        data = self._make_test([{"action": "waitForAny"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_valid_wait_action(self):
        """Test valid wait action."""
        data = self._make_test([{"action": "wait", "ms": 1000}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_wait_negative_ms(self):
        """Test wait with negative ms fails."""
        data = self._make_test([{"action": "wait", "ms": -100}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_valid_screenshot_action(self):
        """Test valid screenshot action."""
        data = self._make_test([{"action": "screenshot", "name": "test_screenshot"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_back_action(self):
        """Test valid back action."""
        data = self._make_test([{"action": "back"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_unsupported_action(self):
        """Test unsupported action fails."""
        data = self._make_test([{"action": "unknown_action", "id": "elem"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_timeout_must_be_positive(self):
        """Test timeout must be positive integer."""
        data = self._make_test([{"action": "waitFor", "id": "elem", "timeout": 0}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_timeout_must_be_integer(self):
        """Test timeout must be integer."""
        data = self._make_test([{"action": "waitFor", "id": "elem", "timeout": "5000"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid


class TestAssertionValidation:
    """Tests for assertion validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def _make_test(self, steps: list) -> dict:
        return {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"name": "case1", "steps": steps}]
        }

    def test_valid_visible_assertion(self):
        """Test valid visible assertion."""
        data = self._make_test([{"assert": "visible", "id": "element_id"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_notVisible_assertion(self):
        """Test valid notVisible assertion."""
        data = self._make_test([{"assert": "notVisible", "id": "element_id"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_enabled_assertion(self):
        """Test valid enabled assertion."""
        data = self._make_test([{"assert": "enabled", "id": "button_id"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_disabled_assertion(self):
        """Test valid disabled assertion."""
        data = self._make_test([{"assert": "disabled", "id": "button_id"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_text_assertion_equals(self):
        """Test valid text assertion with equals."""
        data = self._make_test([{"assert": "text", "id": "label_id", "equals": "Expected"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_text_assertion_contains(self):
        """Test valid text assertion with contains."""
        data = self._make_test([{"assert": "text", "id": "label_id", "contains": "partial"}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_text_assertion_missing_equals_and_contains(self):
        """Test text assertion without equals or contains fails."""
        data = self._make_test([{"assert": "text", "id": "label_id"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_valid_count_assertion(self):
        """Test valid count assertion."""
        data = self._make_test([{"assert": "count", "id": "list_item", "equals": 5}])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_count_assertion_missing_equals(self):
        """Test count assertion without equals fails."""
        data = self._make_test([{"assert": "count", "id": "list_item"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_unsupported_assertion(self):
        """Test unsupported assertion fails."""
        data = self._make_test([{"assert": "unknown_assertion", "id": "elem"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid


class TestStepValidation:
    """Tests for step structure validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def _make_test(self, steps: list) -> dict:
        return {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"name": "case1", "steps": steps}]
        }

    def test_step_must_have_action_or_assert(self):
        """Test step must have action or assert."""
        data = self._make_test([{"id": "element_id"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_step_cannot_have_both_action_and_assert(self):
        """Test step cannot have both action and assert."""
        data = self._make_test([{"action": "tap", "assert": "visible", "id": "elem"}])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_unknown_step_key_warning(self):
        """Test unknown step key produces warning."""
        data = self._make_test([{"action": "tap", "id": "elem", "unknown_key": "value"}])
        result = self.validator.validate_data(data)
        assert result.is_valid  # Should pass with warning
        assert result.warning_count > 0


class TestFlowTestValidation:
    """Tests for flow test validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def test_valid_flow_test(self):
        """Test validation of valid flow test."""
        data = {
            "type": "flow",
            "sources": [{"layout": "layouts/screen1.json", "alias": "screen1"}],
            "metadata": {"name": "flow_test"},
            "steps": [
                {"screen": "screen1", "action": "tap", "id": "button_id"},
                {"screen": "screen1", "assert": "visible", "id": "result_id"}
            ]
        }

        result = self.validator.validate_data(data)
        assert result.is_valid


class TestCaseValidation:
    """Tests for test case validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def test_case_missing_name(self):
        """Test case without name fails."""
        data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"steps": [{"action": "tap", "id": "elem"}]}]
        }

        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_case_empty_steps_warning(self):
        """Test case with empty steps produces warning."""
        data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"name": "empty_case", "steps": []}]
        }

        result = self.validator.validate_data(data)
        assert result.is_valid  # Should pass with warning
        assert result.warning_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
