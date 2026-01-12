"""Tests for the generator module."""

import pytest
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonui_test_cli.generator import DocumentGenerator, generate_schema_reference


class TestDocumentGenerator:
    """Tests for DocumentGenerator."""

    def setup_method(self):
        self.generator = DocumentGenerator()

    def test_generate_markdown_basic(self):
        """Test basic markdown generation."""
        # Create a temp test file
        test_data = {
            "type": "screen",
            "source": {"layout": "layouts/test.json"},
            "metadata": {
                "name": "Sample Test",
                "description": "A sample test for documentation"
            },
            "platform": "ios",
            "cases": [
                {
                    "name": "initial_display",
                    "description": "Verify initial elements",
                    "steps": [
                        {"action": "waitFor", "id": "root_view", "timeout": 5000},
                        {"assert": "visible", "id": "title_label"}
                    ]
                }
            ]
        }

        # Write temp file
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            content = self.generator.generate(temp_path, format="markdown")

            assert "# Sample Test" in content
            assert "A sample test for documentation" in content
            assert "initial_display" in content
            assert "`waitFor`" in content
            assert "`visible`" in content
            assert "root_view" in content
        finally:
            temp_path.unlink()

    def test_generate_html_basic(self):
        """Test basic HTML generation."""
        test_data = {
            "type": "screen",
            "metadata": {"name": "HTML Test"},
            "cases": [
                {
                    "name": "test_case",
                    "steps": [{"action": "tap", "id": "button"}]
                }
            ]
        }

        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            content = self.generator.generate(temp_path, format="html")

            assert "<!DOCTYPE html>" in content
            assert "<title>HTML Test" in content
            assert "<code>tap</code>" in content
            assert "<code>button</code>" in content
        finally:
            temp_path.unlink()

    def test_generate_fails_on_invalid_file(self):
        """Test generation fails on invalid test file."""
        test_data = {
            "type": "screen",
            "cases": [
                {
                    "name": "bad_case",
                    "steps": [{"action": "unknown_action"}]
                }
            ]
        }

        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError):
                self.generator.generate(temp_path)
        finally:
            temp_path.unlink()

    def test_generate_with_output_file(self):
        """Test generation writes to output file."""
        test_data = {
            "type": "screen",
            "metadata": {"name": "Output Test"},
            "cases": [
                {"name": "case1", "steps": [{"action": "back"}]}
            ]
        }

        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            input_path = Path(f.name)

        output_path = Path(tempfile.mktemp(suffix='.md'))

        try:
            result = self.generator.generate(input_path, output_path, format="markdown")

            assert result is None  # Returns None when writing to file
            assert output_path.exists()

            content = output_path.read_text()
            assert "# Output Test" in content
        finally:
            input_path.unlink()
            if output_path.exists():
                output_path.unlink()

    def test_step_details_formatting(self):
        """Test step details are formatted correctly."""
        test_data = {
            "type": "screen",
            "metadata": {"name": "Details Test"},
            "cases": [
                {
                    "name": "case1",
                    "steps": [
                        {"action": "input", "id": "field", "value": "test text"},
                        {"action": "scroll", "id": "list", "direction": "down"},
                        {"action": "waitFor", "id": "elem", "timeout": 10000},
                        {"assert": "text", "id": "label", "equals": "Expected"}
                    ]
                }
            ]
        }

        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            content = self.generator.generate(temp_path, format="markdown")

            assert 'value: "test text"' in content
            assert "direction: down" in content
            assert "timeout: 10000ms" in content
            assert 'equals: "Expected"' in content
        finally:
            temp_path.unlink()


class TestSchemaReference:
    """Tests for schema reference generation."""

    def test_generate_schema_markdown(self):
        """Test schema reference markdown generation."""
        content = generate_schema_reference(format="markdown")

        # Check header
        assert "# JsonUI Test Schema Reference" in content

        # Check actions are documented
        assert "## Actions" in content
        assert "### `tap`" in content
        assert "### `waitFor`" in content
        assert "### `waitForAny`" in content

        # Check assertions are documented
        assert "## Assertions" in content
        assert "### `visible`" in content
        assert "### `text`" in content

        # Check examples are included
        assert "```json" in content
        assert '"action": "tap"' in content

    def test_generate_schema_to_file(self):
        """Test schema reference writes to file."""
        import tempfile

        output_path = Path(tempfile.mktemp(suffix='.md'))

        try:
            result = generate_schema_reference(output_path, format="markdown")

            assert result is None
            assert output_path.exists()

            content = output_path.read_text()
            assert "JsonUI Test Schema Reference" in content
        finally:
            if output_path.exists():
                output_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
