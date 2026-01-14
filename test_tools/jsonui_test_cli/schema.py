"""Schema definitions for JsonUI test files."""

# Cross-platform supported actions and their required/optional parameters
SUPPORTED_ACTIONS = {
    "tap": {
        "description": "Tap on an element",
        "required": ["id"],
        "optional": ["text", "timeout"]
    },
    "doubleTap": {
        "description": "Double tap on an element",
        "required": ["id"],
        "optional": ["timeout"]
    },
    "longPress": {
        "description": "Long press on an element",
        "required": ["id"],
        "optional": ["duration", "timeout"]
    },
    "input": {
        "description": "Input text into a field",
        "required": ["id", "value"],
        "optional": ["timeout"]
    },
    "clear": {
        "description": "Clear text from an input field",
        "required": ["id"],
        "optional": ["timeout"]
    },
    "scroll": {
        "description": "Scroll within an element",
        "required": ["id", "direction"],
        "optional": ["amount", "timeout"]
    },
    "swipe": {
        "description": "Swipe gesture on an element",
        "required": ["id", "direction"],
        "optional": ["timeout"]
    },
    "waitFor": {
        "description": "Wait for an element to appear",
        "required": ["id"],
        "optional": ["timeout"]
    },
    "waitForAny": {
        "description": "Wait for any of multiple elements to appear",
        "required": ["ids"],
        "optional": ["timeout"]
    },
    "wait": {
        "description": "Wait for a specified duration",
        "required": ["ms"],
        "optional": []
    },
    "back": {
        "description": "Navigate back",
        "required": [],
        "optional": []
    },
    "screenshot": {
        "description": "Take a screenshot",
        "required": ["name"],
        "optional": []
    },
    "alertTap": {
        "description": "Tap a button in a native alert dialog",
        "required": ["button"],
        "optional": ["timeout"]
    },
    "selectOption": {
        "description": "Select an option from a select/dropdown element (Web: standard select, iOS: SelectBox picker)",
        "required": ["id"],
        "optional": ["value", "label", "index", "timeout"]
    }
}

# Cross-platform supported assertions and their required/optional parameters
SUPPORTED_ASSERTIONS = {
    "visible": {
        "description": "Assert element is visible",
        "required": ["id"],
        "optional": ["timeout"]
    },
    "notVisible": {
        "description": "Assert element is not visible",
        "required": ["id"],
        "optional": ["timeout"]
    },
    "enabled": {
        "description": "Assert element is enabled",
        "required": ["id"],
        "optional": ["timeout"]
    },
    "disabled": {
        "description": "Assert element is disabled",
        "required": ["id"],
        "optional": ["timeout"]
    },
    "text": {
        "description": "Assert element text matches",
        "required": ["id"],
        "optional": ["equals", "contains", "timeout"]
    },
    "count": {
        "description": "Assert element count",
        "required": ["id", "equals"],
        "optional": ["timeout"]
    }
}

# Valid direction values
VALID_DIRECTIONS = ["up", "down", "left", "right"]

# Valid top-level keys in test file
VALID_TOP_LEVEL_KEYS = [
    "type", "source", "metadata", "platform", "initialState",
    "setup", "teardown", "cases", "sources", "steps", "checkpoints"
]

# Valid keys in test case
VALID_CASE_KEYS = ["name", "description", "skip", "platform", "initialState", "steps"]

# Valid keys in test step
VALID_STEP_KEYS = [
    "action", "assert", "id", "ids", "value", "direction",
    "duration", "timeout", "ms", "name", "equals", "contains",
    "path", "amount", "screen", "text", "button", "label", "index"
]

# Parameter descriptions
PARAMETER_DESCRIPTIONS = {
    "id": "Element identifier (accessibilityIdentifier on iOS, resource-id on Android, data-testid on Web)",
    "ids": "Array of element identifiers for waitForAny",
    "value": "Text value for input actions",
    "direction": "Direction for scroll/swipe: up, down, left, right",
    "duration": "Duration in milliseconds (for longPress)",
    "timeout": "Maximum wait time in milliseconds (default: 5000)",
    "ms": "Wait duration in milliseconds",
    "name": "Name for screenshot file",
    "equals": "Exact value to match",
    "contains": "Substring to match",
    "amount": "Scroll amount (platform-specific)",
    "screen": "Screen identifier (for flow tests)",
    "text": "Specific text portion to tap within element (for tap action)",
    "button": "Button text to tap in alert dialog (for alertTap action)",
    "label": "Option label (visible text) to select (for selectOption action)",
    "index": "Option index to select, 0-based (for selectOption action)"
}
