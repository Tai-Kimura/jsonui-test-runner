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


class TestFlowTestFileReferenceValidation:
    """Tests for flow test file reference validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def _make_flow_test(self, steps: list) -> dict:
        return {
            "type": "flow",
            "metadata": {"name": "flow_test"},
            "steps": steps
        }

    def test_valid_file_reference_with_case(self):
        """Test valid file reference with single case."""
        data = self._make_flow_test([
            {"file": "screens/login", "case": "valid_login"}
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_file_reference_with_cases(self):
        """Test valid file reference with multiple cases."""
        data = self._make_flow_test([
            {"file": "screens/login", "cases": ["initial_display", "valid_login"]}
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_valid_file_reference_all_cases(self):
        """Test valid file reference without case (all cases)."""
        data = self._make_flow_test([
            {"file": "screens/login"}
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_file_reference_empty_file(self):
        """Test file reference with empty file fails."""
        data = self._make_flow_test([
            {"file": ""}
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("non-empty string" in str(e) for e in result.errors)

    def test_file_reference_both_case_and_cases(self):
        """Test file reference with both case and cases fails."""
        data = self._make_flow_test([
            {"file": "screens/login", "case": "one", "cases": ["two", "three"]}
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("both 'case' and 'cases'" in str(e) for e in result.errors)

    def test_file_reference_empty_case(self):
        """Test file reference with empty case fails."""
        data = self._make_flow_test([
            {"file": "screens/login", "case": ""}
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_file_reference_empty_cases_array(self):
        """Test file reference with empty cases array fails."""
        data = self._make_flow_test([
            {"file": "screens/login", "cases": []}
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("non-empty array" in str(e) for e in result.errors)

    def test_file_reference_cases_with_empty_string(self):
        """Test file reference with empty string in cases fails."""
        data = self._make_flow_test([
            {"file": "screens/login", "cases": ["valid_login", ""]}
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid

    def test_file_reference_unknown_key_warning(self):
        """Test file reference with unknown key produces warning."""
        data = self._make_flow_test([
            {"file": "screens/login", "case": "valid_login", "unknown_key": "value"}
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid
        assert result.warning_count > 0

    def test_file_reference_not_allowed_in_screen_test(self):
        """Test file reference in screen test fails."""
        data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [
                {"name": "case1", "steps": [{"file": "screens/login"}]}
            ]
        }
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("only allowed in flow tests" in str(e) for e in result.errors)

    def test_mixed_file_ref_and_inline_steps(self):
        """Test flow with mixed file references and inline steps."""
        data = self._make_flow_test([
            {"file": "screens/login", "case": "valid_login"},
            {"action": "waitFor", "id": "home_screen", "timeout": 5000},
            {"file": "screens/home", "cases": ["verify_display", "navigate_to_profile"]},
            {"assert": "visible", "id": "profile_title"}
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid


class TestFlowTestSetupTeardown:
    """Tests for flow test setup and teardown validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def test_flow_with_setup(self):
        """Test flow test with setup section."""
        data = {
            "type": "flow",
            "metadata": {"name": "flow_with_setup"},
            "setup": [
                {"action": "waitFor", "id": "launch_screen", "timeout": 5000}
            ],
            "steps": [
                {"action": "tap", "id": "start_button"}
            ]
        }
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_flow_with_teardown(self):
        """Test flow test with teardown section."""
        data = {
            "type": "flow",
            "metadata": {"name": "flow_with_teardown"},
            "steps": [
                {"action": "tap", "id": "start_button"}
            ],
            "teardown": [
                {"action": "screenshot", "name": "final_state"}
            ]
        }
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_flow_with_checkpoints(self):
        """Test flow test with checkpoints."""
        data = {
            "type": "flow",
            "metadata": {"name": "flow_with_checkpoints"},
            "steps": [
                {"action": "tap", "id": "login_button"},
                {"action": "waitFor", "id": "home_screen", "timeout": 5000}
            ],
            "checkpoints": [
                {"name": "after_login", "afterStep": 1, "screenshot": True}
            ]
        }
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_flow_empty_steps_warning(self):
        """Test flow test with empty steps produces warning."""
        data = {
            "type": "flow",
            "metadata": {"name": "empty_flow"},
            "steps": []
        }
        result = self.validator.validate_data(data)
        assert result.is_valid
        assert result.warning_count > 0


class TestDescriptionFileValidation:
    """Tests for description file validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def test_valid_description_file(self):
        """Test valid description file."""
        import tempfile
        import json

        desc_data = {
            "case_name": "initial_display",
            "summary": "Verify initial screen state",
            "preconditions": ["User is logged in", "App is launched"],
            "test_procedure": ["Open the screen", "Check elements"],
            "expected_results": ["Title is visible", "Button is enabled"],
            "notes": "Additional notes"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(desc_data, f)
            temp_path = Path(f.name)

        try:
            result = self.validator.validate_file(temp_path)
            assert result.is_valid
        finally:
            temp_path.unlink()

    def test_description_missing_case_name(self):
        """Test description file without case_name fails."""
        import tempfile
        import json

        desc_data = {
            "summary": "Some summary"
        }

        # Create in descriptions folder to trigger description validation
        with tempfile.TemporaryDirectory() as temp_dir:
            desc_dir = Path(temp_dir) / "descriptions"
            desc_dir.mkdir()
            desc_file = desc_dir / "test.json"

            with open(desc_file, 'w') as f:
                json.dump(desc_data, f)

            result = self.validator.validate_file(desc_file)
            assert not result.is_valid
            assert any("case_name" in str(e) for e in result.errors)

    def test_description_invalid_preconditions(self):
        """Test description file with invalid preconditions."""
        import tempfile
        import json

        desc_data = {
            "case_name": "test_case",
            "preconditions": "not an array"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            desc_dir = Path(temp_dir) / "descriptions"
            desc_dir.mkdir()
            desc_file = desc_dir / "test.json"

            with open(desc_file, 'w') as f:
                json.dump(desc_data, f)

            result = self.validator.validate_file(desc_file)
            assert not result.is_valid


class TestFlowBlockStepValidation:
    """Tests for flow test block step validation."""

    def setup_method(self):
        self.validator = TestValidator()

    def _make_flow_test(self, steps: list) -> dict:
        return {
            "type": "flow",
            "metadata": {"name": "flow_test"},
            "steps": steps
        }

    def test_valid_block_step(self):
        """Test valid block step in flow test."""
        data = self._make_flow_test([
            {
                "block": "error_handling",
                "description": "Handle login errors",
                "steps": [
                    {"action": "tap", "id": "retry_button"},
                    {"assert": "visible", "id": "error_message"}
                ]
            }
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_block_step_without_description(self):
        """Test block step without description is valid."""
        data = self._make_flow_test([
            {
                "block": "simple_block",
                "steps": [
                    {"action": "tap", "id": "button"}
                ]
            }
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_block_step_empty_name_fails(self):
        """Test block step with empty name fails."""
        data = self._make_flow_test([
            {
                "block": "",
                "steps": [{"action": "tap", "id": "button"}]
            }
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("non-empty string" in str(e) for e in result.errors)

    def test_block_step_missing_steps_fails(self):
        """Test block step without steps array fails."""
        data = self._make_flow_test([
            {
                "block": "my_block",
                "description": "A block"
            }
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("must have 'steps'" in str(e) for e in result.errors)

    def test_block_step_empty_steps_fails(self):
        """Test block step with empty steps array fails."""
        data = self._make_flow_test([
            {
                "block": "my_block",
                "steps": []
            }
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("non-empty array" in str(e) for e in result.errors)

    def test_block_step_with_file_ref_inside_fails(self):
        """Test block step containing file reference fails."""
        data = self._make_flow_test([
            {
                "block": "my_block",
                "steps": [
                    {"file": "screens/login", "case": "test"}
                ]
            }
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("not allowed inside block" in str(e) for e in result.errors)

    def test_nested_block_fails(self):
        """Test nested block step fails."""
        data = self._make_flow_test([
            {
                "block": "outer_block",
                "steps": [
                    {
                        "block": "inner_block",
                        "steps": [{"action": "tap", "id": "btn"}]
                    }
                ]
            }
        ])
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("Nested blocks are not allowed" in str(e) for e in result.errors)

    def test_block_step_not_allowed_in_screen_test(self):
        """Test block step in screen test fails."""
        data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [
                {
                    "name": "case1",
                    "steps": [
                        {
                            "block": "my_block",
                            "steps": [{"action": "tap", "id": "btn"}]
                        }
                    ]
                }
            ]
        }
        result = self.validator.validate_data(data)
        assert not result.is_valid
        assert any("only allowed in flow tests" in str(e) for e in result.errors)

    def test_mixed_blocks_and_file_refs(self):
        """Test flow with mixed blocks, file refs, and inline steps."""
        data = self._make_flow_test([
            {"file": "screens/login", "case": "valid_login"},
            {
                "block": "error_handling",
                "description": "Handle errors",
                "steps": [
                    {"action": "tap", "id": "retry_button"},
                    {"assert": "visible", "id": "success_message"}
                ]
            },
            {"action": "waitFor", "id": "home_screen", "timeout": 5000},
            {"file": "screens/home", "case": "verify_display"}
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid

    def test_block_unknown_key_warning(self):
        """Test block step with unknown key produces warning."""
        data = self._make_flow_test([
            {
                "block": "my_block",
                "unknown_key": "value",
                "steps": [{"action": "tap", "id": "btn"}]
            }
        ])
        result = self.validator.validate_data(data)
        assert result.is_valid
        assert result.warning_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
