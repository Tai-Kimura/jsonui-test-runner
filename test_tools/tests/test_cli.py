"""Tests for the CLI module."""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonui_test_cli.cli import main, cmd_validate, cmd_generate


class TestCLIValidate:
    """Tests for validate command."""

    def test_validate_valid_file(self):
        """Test validating a valid file."""
        test_data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [
                {"name": "case1", "steps": [{"action": "tap", "id": "btn"}]}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with patch('sys.argv', ['jsonui-test', 'validate', temp_path]):
                result = main()
                assert result == 0
        finally:
            Path(temp_path).unlink()

    def test_validate_invalid_file(self):
        """Test validating an invalid file."""
        test_data = {
            "type": "screen",
            "cases": [
                {"name": "case1", "steps": [{"action": "invalid_action"}]}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with patch('sys.argv', ['jsonui-test', 'validate', temp_path]):
                result = main()
                assert result == 1
        finally:
            Path(temp_path).unlink()

    def test_validate_directory(self):
        """Test validating a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid test file
            test_data = {
                "type": "screen",
                "metadata": {"name": "test"},
                "cases": [{"name": "case1", "steps": [{"action": "back"}]}]
            }

            test_file = Path(temp_dir) / "sample.test.json"
            with open(test_file, 'w') as f:
                json.dump(test_data, f)

            with patch('sys.argv', ['jsonui-test', 'validate', temp_dir]):
                result = main()
                assert result == 0

    def test_validate_nonexistent_file(self):
        """Test validating nonexistent file."""
        with patch('sys.argv', ['jsonui-test', 'validate', '/nonexistent/path.test.json']):
            result = main()
            assert result == 1

    def test_validate_verbose(self):
        """Test verbose output."""
        test_data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"name": "case1", "steps": [{"action": "back"}]}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with patch('sys.argv', ['jsonui-test', 'validate', '-v', temp_path]):
                result = main()
                assert result == 0
        finally:
            Path(temp_path).unlink()


class TestCLIGenerate:
    """Tests for generate command."""

    def test_generate_markdown(self):
        """Test generating markdown documentation."""
        test_data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"name": "case1", "steps": [{"action": "back"}]}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            input_path = f.name

        output_path = tempfile.mktemp(suffix='.md')

        try:
            with patch('sys.argv', ['jsonui-test', 'generate', '-f', input_path, '-o', output_path]):
                result = main()
                assert result == 0
                assert Path(output_path).exists()
        finally:
            Path(input_path).unlink()
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_generate_html(self):
        """Test generating HTML documentation."""
        test_data = {
            "type": "screen",
            "metadata": {"name": "test"},
            "cases": [{"name": "case1", "steps": [{"action": "back"}]}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.test.json', delete=False) as f:
            json.dump(test_data, f)
            input_path = f.name

        output_path = tempfile.mktemp(suffix='.html')

        try:
            with patch('sys.argv', ['jsonui-test', 'generate', '-f', input_path, '-o', output_path, '--format', 'html']):
                result = main()
                assert result == 0
                assert Path(output_path).exists()

                content = Path(output_path).read_text()
                assert "<!DOCTYPE html>" in content
        finally:
            Path(input_path).unlink()
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_generate_schema(self):
        """Test generating schema reference."""
        output_path = tempfile.mktemp(suffix='.md')

        try:
            with patch('sys.argv', ['jsonui-test', 'generate', '--schema', '-o', output_path]):
                result = main()
                assert result == 0
                assert Path(output_path).exists()

                content = Path(output_path).read_text()
                assert "JsonUI Test Schema Reference" in content
        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_generate_schema_stdout(self):
        """Test generating schema to stdout."""
        with patch('sys.argv', ['jsonui-test', 'generate', '--schema']):
            result = main()
            assert result == 0

    def test_generate_no_file_or_schema(self):
        """Test generate without file or schema fails."""
        with patch('sys.argv', ['jsonui-test', 'generate']):
            result = main()
            assert result == 1


class TestCLIHelp:
    """Tests for help and version."""

    def test_no_command_shows_help(self):
        """Test no command shows help."""
        with patch('sys.argv', ['jsonui-test']):
            result = main()
            assert result == 0

    def test_version(self):
        """Test version flag."""
        with patch('sys.argv', ['jsonui-test', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
