# JsonUI Test CLI

CLI tool for validating and generating documentation from JsonUI test files.

## Requirements

- Python 3.10 or higher

## Installation

### Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-test-runner/main/test_tools/installer/bootstrap.sh | bash
```

### Install Specific Version

```bash
# Install from a specific tag
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-test-runner/main/test_tools/installer/bootstrap.sh | bash -s -- -v v1.0.0

# Install from a specific branch
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-test-runner/main/test_tools/installer/bootstrap.sh | bash -s -- -v feature-branch
```

### Install with Development Dependencies

```bash
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-test-runner/main/test_tools/installer/bootstrap.sh | bash -s -- --dev
```

### Manual Install

```bash
cd test_tools
pip install -e .
```

### Python Version Setup (if needed)

If you don't have Python 3.10+, use mise (recommended):

```bash
# Install mise (if not installed)
curl https://mise.run | sh

# Install and use Python 3.11
mise install python@3.11
mise use python@3.11

# Verify
python --version
```

Or use pyenv:

```bash
pyenv install 3.11.0
pyenv local 3.11.0
```

## Commands

### validate

Validate `.test.json` files for cross-platform compatibility.

```bash
# Validate single file
jsonui-test validate path/to/test.test.json

# Validate directory (recursive)
jsonui-test validate tests/

# Verbose output (show all details)
jsonui-test validate -v tests/

# Quiet mode (show only errors, hide warnings)
jsonui-test validate -q tests/
```

**Exit codes:**
- `0`: All files valid
- `1`: Validation errors found

### generate

Generate human-readable documentation from test files.

```bash
# Generate markdown documentation
jsonui-test generate -f test.test.json -o docs/test.md

# Generate HTML documentation
jsonui-test generate -f test.test.json -o docs/test.html --format html

# Output to stdout
jsonui-test generate -f test.test.json

# Generate schema reference document
jsonui-test generate --schema -o docs/schema.md
```

## Test File Format

Test files must be valid JSON with `.test.json` extension.

### Screen Test Example

```json
{
  "type": "screen",
  "source": {
    "layout": "layouts/home.json"
  },
  "metadata": {
    "name": "home_screen_test",
    "description": "Tests for home screen"
  },
  "platform": "ios",
  "cases": [
    {
      "name": "initial_display",
      "description": "Verify initial elements",
      "steps": [
        { "action": "waitFor", "id": "root_view", "timeout": 5000 },
        { "assert": "visible", "id": "title_label" }
      ]
    }
  ]
}
```

### Flow Test Example

```json
{
  "type": "flow",
  "metadata": {
    "name": "login_flow",
    "description": "User login flow test"
  },
  "steps": [
    { "action": "waitFor", "id": "login_screen" },
    { "action": "input", "id": "email_field", "value": "test@example.com" },
    { "action": "input", "id": "password_field", "value": "password123" },
    { "action": "tap", "id": "login_button" },
    { "assert": "visible", "id": "home_screen" }
  ]
}
```

## Supported Actions

| Action | Required | Optional | Description |
|--------|----------|----------|-------------|
| tap | id | timeout | Tap on an element |
| doubleTap | id | timeout | Double tap |
| longPress | id | duration, timeout | Long press |
| input | id, value | timeout | Input text |
| clear | id | timeout | Clear text field |
| scroll | id, direction | amount, timeout | Scroll |
| swipe | id, direction | timeout | Swipe gesture |
| waitFor | id | timeout | Wait for element |
| waitForAny | ids | timeout | Wait for any element |
| wait | ms | - | Wait duration |
| back | - | - | Navigate back |
| screenshot | name | - | Take screenshot |

**Direction values:** `up`, `down`, `left`, `right`

## Supported Assertions

| Assert | Required | Optional | Description |
|--------|----------|----------|-------------|
| visible | id | timeout | Element is visible |
| notVisible | id | timeout | Element is not visible |
| enabled | id | timeout | Element is enabled |
| disabled | id | timeout | Element is disabled |
| text | id | equals, contains, timeout | Text matches |
| count | id, equals | timeout | Element count |

## Running Tests

```bash
# Install with dev dependencies
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-test-runner/main/test_tools/installer/bootstrap.sh | bash -s -- --dev

# Run tests
pytest

# Run with coverage
pytest --cov=jsonui_test_cli

# Run specific test file
pytest tests/test_validator.py -v
```

## Project Structure

```
test_tools/
├── installer/
│   ├── bootstrap.sh            # Bootstrap script for curl install
│   ├── install_jsonui_test.sh  # Main installer script
│   └── README.md               # Installer documentation
├── pyproject.toml              # Package configuration
├── README.md                   # This file
├── jsonui-test                 # CLI entry point (development)
├── jsonui_test_cli/
│   ├── __init__.py
│   ├── cli.py                  # CLI commands
│   ├── schema.py               # Action/assertion definitions
│   ├── validator.py            # Test file validator
│   └── generator.py            # Documentation generator
└── tests/
    ├── test_cli.py
    ├── test_validator.py
    └── test_generator.py
```
