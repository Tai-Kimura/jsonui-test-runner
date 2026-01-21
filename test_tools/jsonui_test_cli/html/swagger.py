"""Swagger/OpenAPI documentation page HTML generation with sidebar."""

from __future__ import annotations

import json
from pathlib import Path

from .styles import get_screen_styles, get_toggle_script
from .sidebar import escape_html


def is_swagger_file(file_path: Path) -> bool:
    """
    Check if a file is a Swagger/OpenAPI document.

    Args:
        file_path: Path to the JSON file

    Returns:
        True if the file is a Swagger/OpenAPI document
    """
    if not file_path.exists() or file_path.suffix.lower() != '.json':
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check for OpenAPI 3.x or Swagger 2.0
        return 'openapi' in data or 'swagger' in data
    except Exception:
        return False


def parse_swagger_file(file_path: Path) -> dict | None:
    """
    Parse a Swagger/OpenAPI file and extract relevant information.

    Args:
        file_path: Path to the Swagger/OpenAPI JSON file

    Returns:
        Parsed swagger data dict or None if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _get_relative_root(doc_path: str) -> str:
    """Calculate relative path to root from document path."""
    depth = len(Path(doc_path).parent.parts)
    if depth == 0:
        return "./"
    return "../" * depth


def generate_swagger_sidebar(
    title: str,
    tags: list[dict],
    all_tests_nav: dict | None = None,
    current_doc_path: str | None = None
) -> list[str]:
    """
    Generate sidebar HTML for Swagger documentation pages.

    Args:
        title: Page title
        tags: List of API tags from swagger
        all_tests_nav: Navigation data {'screens': [...], 'flows': [...], 'api_docs': [...]}
        current_doc_path: Current document's relative path

    Returns:
        List of HTML strings for the sidebar
    """
    rel_root = _get_relative_root(current_doc_path) if current_doc_path else "../"

    parts = []
    parts.append("  <nav class='sidebar'>")
    parts.append(f"    <a href='{rel_root}index.html' class='back-link'>&larr; Back to Index</a>")
    parts.append(f"    <h2>{escape_html(title)}</h2>")

    # API Tags section (collapsible, expanded by default)
    if tags:
        parts.append("    <div class='sidebar-section'>")
        parts.append(f"      <div class='sidebar-title api' id='tags-title' onclick=\"toggleSection('tags')\"><span class='arrow'>▼</span> API Tags <span class='count'>{len(tags)}</span></div>")
        parts.append("      <div class='sidebar-list' id='tags-list'>")
        parts.append("        <ul>")
        for tag in tags:
            tag_name = tag.get('name', 'Unknown')
            tag_id = tag_name.lower().replace(' ', '-')
            parts.append(f"          <li><a href='#tag-{tag_id}'>{escape_html(tag_name)}</a></li>")
        parts.append("        </ul>")
        parts.append("      </div>")
        parts.append("    </div>")

    # Flow Tests navigation (collapsible, collapsed by default)
    if all_tests_nav and all_tests_nav.get('flows'):
        flows = all_tests_nav['flows']
        parts.append("    <div class='sidebar-section'>")
        parts.append(f"      <div class='sidebar-title flow collapsed' id='flows-title' onclick=\"toggleSection('flows')\"><span class='arrow'>▼</span> Flow Tests <span class='count'>{len(flows)}</span></div>")
        parts.append("      <div class='sidebar-list collapsed' id='flows-list'>")
        parts.append("        <ul>")
        for f in flows:
            parts.append(f"          <li><a href='{rel_root}{f['path']}' class='nav-link' title='{escape_html(f['name'])}'>{escape_html(f['name'])}</a></li>")
        parts.append("        </ul>")
        parts.append("      </div>")
        parts.append("    </div>")

    # Screen Tests navigation (collapsible, collapsed by default)
    if all_tests_nav and all_tests_nav.get('screens'):
        screens = all_tests_nav['screens']
        parts.append("    <div class='sidebar-section'>")
        parts.append(f"      <div class='sidebar-title collapsed' id='screens-title' onclick=\"toggleSection('screens')\"><span class='arrow'>▼</span> Screen Tests <span class='count'>{len(screens)}</span></div>")
        parts.append("      <div class='sidebar-list collapsed' id='screens-list'>")
        parts.append("        <ul>")
        for s in screens:
            parts.append(f"          <li><a href='{rel_root}{s['path']}' class='nav-link' title='{escape_html(s['name'])}'>{escape_html(s['name'])}</a></li>")
        parts.append("        </ul>")
        parts.append("      </div>")
        parts.append("    </div>")

    # Documents navigation (collapsible, collapsed by default)
    if all_tests_nav and all_tests_nav.get('documents'):
        documents = all_tests_nav['documents']
        parts.append("    <div class='sidebar-section'>")
        parts.append(f"      <div class='sidebar-title doc collapsed' id='documents-title' onclick=\"toggleSection('documents')\"><span class='arrow'>▼</span> Documents <span class='count'>{len(documents)}</span></div>")
        parts.append("      <div class='sidebar-list collapsed' id='documents-list'>")
        parts.append("        <ul>")
        for d in documents:
            parts.append(f"          <li><a href='{rel_root}{d['path']}' class='nav-link' title='{escape_html(d['name'])}'>{escape_html(d['name'])}</a></li>")
        parts.append("        </ul>")
        parts.append("      </div>")
        parts.append("    </div>")

    # API Docs navigation (collapsible, collapsed by default)
    if all_tests_nav and all_tests_nav.get('api_docs'):
        api_docs = all_tests_nav['api_docs']
        parts.append("    <div class='sidebar-section'>")
        parts.append(f"      <div class='sidebar-title api collapsed' id='api-docs-title' onclick=\"toggleSection('api-docs')\"><span class='arrow'>▼</span> API Docs <span class='count'>{len(api_docs)}</span></div>")
        parts.append("      <div class='sidebar-list collapsed' id='api-docs-list'>")
        parts.append("        <ul>")
        for d in api_docs:
            is_current = current_doc_path and d['path'] == current_doc_path
            current_class = " current" if is_current else ""
            parts.append(f"          <li><a href='{rel_root}{d['path']}' class='nav-link{current_class}' title='{escape_html(d['name'])}'>{escape_html(d['name'])}</a></li>")
        parts.append("        </ul>")
        parts.append("      </div>")
        parts.append("    </div>")

    parts.append("  </nav>")
    return parts


def _get_method_class(method: str) -> str:
    """Get CSS class for HTTP method."""
    method_classes = {
        'get': 'method-get',
        'post': 'method-post',
        'put': 'method-put',
        'patch': 'method-patch',
        'delete': 'method-delete',
        'options': 'method-options',
        'head': 'method-head',
    }
    return method_classes.get(method.lower(), 'method-other')


def _render_schema(schema: dict, indent: int = 0, max_depth: int = 5) -> list[str]:
    """
    Render JSON schema as HTML with recursive nested object support.

    Args:
        schema: JSON schema dict
        indent: Current indentation level
        max_depth: Maximum recursion depth to prevent infinite loops
    """
    parts = []
    indent_str = "  " * indent

    if not schema:
        return [f"{indent_str}<span class='schema-type'>any</span>"]

    if max_depth <= 0:
        return [f"{indent_str}<span class='schema-type'>...</span>"]

    schema_type = schema.get('type', '')

    if '$ref' in schema:
        ref = schema['$ref'].split('/')[-1]
        parts.append(f"{indent_str}<span class='schema-ref'>{escape_html(ref)}</span>")
    elif schema_type == 'object':
        props = schema.get('properties', {})
        required = schema.get('required', [])
        if props:
            parts.append(f"{indent_str}<span class='schema-type'>object</span> {{")
            for prop_name, prop_schema in props.items():
                req_marker = '<span class="required">*</span>' if prop_name in required else ''
                nested_type = prop_schema.get('type', 'any')
                desc = prop_schema.get('description', '')
                desc_html = f" <span class='prop-desc'>// {escape_html(desc)}</span>" if desc else ""

                if '$ref' in prop_schema:
                    # Reference type
                    prop_type = prop_schema['$ref'].split('/')[-1]
                    parts.append(f"{indent_str}  <span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-ref'>{escape_html(prop_type)}</span>{desc_html}")
                elif nested_type == 'object' and prop_schema.get('properties'):
                    # Nested object - render recursively
                    parts.append(f"{indent_str}  <span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>object</span> {{{desc_html}")
                    nested_props = prop_schema.get('properties', {})
                    nested_required = prop_schema.get('required', [])
                    for nested_name, nested_schema in nested_props.items():
                        nested_parts = _render_nested_property(nested_name, nested_schema, nested_required, indent + 2, max_depth - 1)
                        parts.extend(nested_parts)
                    parts.append(f"{indent_str}  }}")
                elif nested_type == 'array':
                    # Array type - check for nested items
                    items = prop_schema.get('items', {})
                    item_type = items.get('type', 'any')
                    if '$ref' in items:
                        item_type = items['$ref'].split('/')[-1]
                        parts.append(f"{indent_str}  <span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>array</span>[<span class='schema-ref'>{escape_html(item_type)}</span>]{desc_html}")
                    elif item_type == 'object' and items.get('properties'):
                        # Array of objects - render item structure
                        parts.append(f"{indent_str}  <span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>array</span>[<span class='schema-type'>object</span> {{{desc_html}")
                        item_props = items.get('properties', {})
                        item_required = items.get('required', [])
                        for item_name, item_schema in item_props.items():
                            item_parts = _render_nested_property(item_name, item_schema, item_required, indent + 2, max_depth - 1)
                            parts.extend(item_parts)
                        parts.append(f"{indent_str}  }}]")
                    else:
                        parts.append(f"{indent_str}  <span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>array</span>[<span class='schema-type'>{escape_html(item_type)}</span>]{desc_html}")
                else:
                    # Simple type
                    parts.append(f"{indent_str}  <span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>{escape_html(nested_type)}</span>{desc_html}")
            parts.append(f"{indent_str}}}")
        else:
            parts.append(f"{indent_str}<span class='schema-type'>object</span>")
    elif schema_type == 'array':
        items = schema.get('items', {})
        item_type = items.get('type', 'any')
        if '$ref' in items:
            item_type = items['$ref'].split('/')[-1]
            parts.append(f"{indent_str}<span class='schema-type'>array</span>[<span class='schema-ref'>{escape_html(item_type)}</span>]")
        elif item_type == 'object' and items.get('properties'):
            # Array of objects at top level
            parts.append(f"{indent_str}<span class='schema-type'>array</span>[<span class='schema-type'>object</span> {{")
            item_props = items.get('properties', {})
            item_required = items.get('required', [])
            for item_name, item_schema in item_props.items():
                item_parts = _render_nested_property(item_name, item_schema, item_required, indent + 1, max_depth - 1)
                parts.extend(item_parts)
            parts.append(f"{indent_str}}}]")
        else:
            parts.append(f"{indent_str}<span class='schema-type'>array</span>[<span class='schema-type'>{escape_html(item_type)}</span>]")
    else:
        enum = schema.get('enum')
        if enum:
            enum_str = ' | '.join(f'"{v}"' for v in enum)
            parts.append(f"{indent_str}<span class='schema-enum'>{escape_html(enum_str)}</span>")
        else:
            parts.append(f"{indent_str}<span class='schema-type'>{escape_html(schema_type or 'any')}</span>")

    return parts


def _render_nested_property(prop_name: str, prop_schema: dict, required: list, indent: int, max_depth: int) -> list[str]:
    """Render a nested property within an object schema."""
    parts = []
    indent_str = "  " * indent

    if max_depth <= 0:
        return [f"{indent_str}<span class='prop-name'>{escape_html(prop_name)}</span>: <span class='schema-type'>...</span>"]

    req_marker = '<span class="required">*</span>' if prop_name in required else ''
    prop_type = prop_schema.get('type', 'any')
    desc = prop_schema.get('description', '')
    desc_html = f" <span class='prop-desc'>// {escape_html(desc)}</span>" if desc else ""

    if '$ref' in prop_schema:
        ref_type = prop_schema['$ref'].split('/')[-1]
        parts.append(f"{indent_str}<span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-ref'>{escape_html(ref_type)}</span>{desc_html}")
    elif prop_type == 'object' and prop_schema.get('properties'):
        # Nested object
        parts.append(f"{indent_str}<span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>object</span> {{{desc_html}")
        nested_props = prop_schema.get('properties', {})
        nested_required = prop_schema.get('required', [])
        for nested_name, nested_schema in nested_props.items():
            nested_parts = _render_nested_property(nested_name, nested_schema, nested_required, indent + 1, max_depth - 1)
            parts.extend(nested_parts)
        parts.append(f"{indent_str}}}")
    elif prop_type == 'array':
        items = prop_schema.get('items', {})
        item_type = items.get('type', 'any')
        if '$ref' in items:
            item_type = items['$ref'].split('/')[-1]
            parts.append(f"{indent_str}<span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>array</span>[<span class='schema-ref'>{escape_html(item_type)}</span>]{desc_html}")
        elif item_type == 'object' and items.get('properties'):
            parts.append(f"{indent_str}<span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>array</span>[<span class='schema-type'>object</span> {{{desc_html}")
            item_props = items.get('properties', {})
            item_required = items.get('required', [])
            for item_name, item_schema in item_props.items():
                item_parts = _render_nested_property(item_name, item_schema, item_required, indent + 1, max_depth - 1)
                parts.extend(item_parts)
            parts.append(f"{indent_str}}}]")
        else:
            parts.append(f"{indent_str}<span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>array</span>[<span class='schema-type'>{escape_html(item_type)}</span>]{desc_html}")
    else:
        parts.append(f"{indent_str}<span class='prop-name'>{escape_html(prop_name)}</span>{req_marker}: <span class='schema-type'>{escape_html(prop_type)}</span>{desc_html}")

    return parts


def _render_endpoint(path: str, method: str, operation: dict) -> list[str]:
    """Render a single API endpoint."""
    parts = []

    summary = operation.get('summary', '')
    description = operation.get('description', '')
    operation_id = operation.get('operationId', '')
    parameters = operation.get('parameters', [])
    request_body = operation.get('requestBody', {})
    responses = operation.get('responses', {})

    method_class = _get_method_class(method)

    parts.append(f"      <div class='endpoint'>")
    parts.append(f"        <div class='endpoint-header'>")
    parts.append(f"          <span class='method {method_class}'>{method.upper()}</span>")
    parts.append(f"          <span class='path'>{escape_html(path)}</span>")
    parts.append(f"        </div>")

    if summary:
        parts.append(f"        <div class='endpoint-summary'>{escape_html(summary)}</div>")

    if description:
        parts.append(f"        <div class='endpoint-description'>{escape_html(description)}</div>")

    # Parameters
    if parameters:
        parts.append(f"        <div class='endpoint-section'>")
        parts.append(f"          <div class='section-title'>Parameters</div>")
        parts.append(f"          <table class='params-table'>")
        parts.append(f"            <tr><th>Name</th><th>In</th><th>Type</th><th>Required</th><th>Description</th></tr>")
        for param in parameters:
            p_name = param.get('name', '')
            p_in = param.get('in', '')
            p_schema = param.get('schema', {})
            p_type = p_schema.get('type', 'string')
            p_required = 'Yes' if param.get('required', False) else 'No'
            p_desc = param.get('description', '')
            parts.append(f"            <tr><td><code>{escape_html(p_name)}</code></td><td>{escape_html(p_in)}</td><td>{escape_html(p_type)}</td><td>{p_required}</td><td>{escape_html(p_desc)}</td></tr>")
        parts.append(f"          </table>")
        parts.append(f"        </div>")

    # Request Body
    if request_body:
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        schema = json_content.get('schema', {})
        if schema:
            parts.append(f"        <div class='endpoint-section'>")
            parts.append(f"          <div class='section-title'>Request Body</div>")
            parts.append(f"          <div class='schema-block'>")
            parts.extend(_render_schema(schema, 6))
            parts.append(f"          </div>")
            parts.append(f"        </div>")

    # Responses
    if responses:
        parts.append(f"        <div class='endpoint-section'>")
        parts.append(f"          <div class='section-title'>Responses</div>")
        for status_code, response in responses.items():
            resp_desc = response.get('description', '')
            resp_content = response.get('content', {})
            resp_json = resp_content.get('application/json', {})
            resp_schema = resp_json.get('schema', {})

            status_class = 'status-success' if status_code.startswith('2') else 'status-error' if status_code.startswith('4') or status_code.startswith('5') else 'status-other'
            parts.append(f"          <div class='response'>")
            parts.append(f"            <span class='status-code {status_class}'>{escape_html(status_code)}</span>")
            parts.append(f"            <span class='response-desc'>{escape_html(resp_desc)}</span>")
            if resp_schema:
                parts.append(f"            <div class='schema-block'>")
                parts.extend(_render_schema(resp_schema, 7))
                parts.append(f"            </div>")
            parts.append(f"          </div>")
        parts.append(f"        </div>")

    parts.append(f"      </div>")

    return parts


def generate_swagger_html(
    swagger_data: dict,
    title: str | None = None,
    all_tests_nav: dict | None = None,
    current_doc_path: str | None = None
) -> str:
    """
    Generate HTML documentation page from Swagger/OpenAPI data.

    Args:
        swagger_data: Parsed Swagger/OpenAPI data
        title: Optional title override
        all_tests_nav: Navigation data for sidebar
        current_doc_path: Current document's relative path

    Returns:
        Complete HTML string with sidebar
    """
    # Extract info
    info = swagger_data.get('info', {})
    doc_title = title or info.get('title', 'API Documentation')
    description = info.get('description', '')
    version = info.get('version', '')

    tags = swagger_data.get('tags', [])
    paths = swagger_data.get('paths', {})

    # Group endpoints by tag
    endpoints_by_tag: dict[str, list] = {}
    for tag in tags:
        endpoints_by_tag[tag['name']] = []
    endpoints_by_tag['Other'] = []  # For untagged endpoints

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.lower() in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                op_tags = operation.get('tags', ['Other'])
                for tag in op_tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append((path, method, operation))

    # Build HTML
    html_parts = _get_html_header(doc_title)
    html_parts.extend(generate_swagger_sidebar(doc_title, tags, all_tests_nav, current_doc_path))

    # Main content
    html_parts.append("  <main class='main-content'>")
    html_parts.append(f"    <h1>{escape_html(doc_title)}</h1>")

    if version:
        html_parts.append(f"    <div class='api-version'>Version: {escape_html(version)}</div>")

    if description:
        # Handle newlines in description
        desc_html = escape_html(description).replace('\n', '<br>')
        html_parts.append(f"    <div class='api-description'>{desc_html}</div>")

    # Render endpoints by tag
    for tag in tags:
        tag_name = tag.get('name', 'Unknown')
        tag_desc = tag.get('description', '')
        tag_id = tag_name.lower().replace(' ', '-')
        tag_endpoints = endpoints_by_tag.get(tag_name, [])

        if tag_endpoints:
            html_parts.append(f"    <div class='tag-section' id='tag-{tag_id}'>")
            html_parts.append(f"      <h2>{escape_html(tag_name)}</h2>")
            if tag_desc:
                html_parts.append(f"      <p class='tag-description'>{escape_html(tag_desc)}</p>")

            for path, method, operation in tag_endpoints:
                html_parts.extend(_render_endpoint(path, method, operation))

            html_parts.append(f"    </div>")

    # Render untagged endpoints
    other_endpoints = endpoints_by_tag.get('Other', [])
    if other_endpoints:
        html_parts.append(f"    <div class='tag-section' id='tag-other'>")
        html_parts.append(f"      <h2>Other</h2>")
        for path, method, operation in other_endpoints:
            html_parts.extend(_render_endpoint(path, method, operation))
        html_parts.append(f"    </div>")

    html_parts.append("  </main>")

    # Close HTML
    html_parts.extend(get_toggle_script())
    html_parts.extend([
        "</body>",
        "</html>"
    ])

    return '\n'.join(html_parts)


def _get_html_header(title: str) -> list[str]:
    """Generate HTML header with styles for Swagger documentation."""
    parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"  <title>{escape_html(title)}</title>",
        "  <style>",
    ]
    parts.extend(get_screen_styles())
    # Add Swagger-specific styles
    parts.extend([
        "    /* Swagger-specific styles */",
        "    .api-version { color: #666; margin-bottom: 10px; font-size: 14px; }",
        "    .api-description { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; white-space: pre-line; }",
        "    .tag-section { margin-bottom: 30px; }",
        "    .tag-section h2 { border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 15px; }",
        "    .tag-description { color: #666; margin-bottom: 15px; }",
        "    .endpoint { background: #fff; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 15px; overflow: hidden; }",
        "    .endpoint-header { display: flex; align-items: center; gap: 10px; padding: 12px 15px; background: #f8f9fa; border-bottom: 1px solid #eee; }",
        "    .method { padding: 4px 10px; border-radius: 3px; font-weight: bold; font-size: 12px; color: #fff; text-transform: uppercase; }",
        "    .method-get { background: #61affe; }",
        "    .method-post { background: #49cc90; }",
        "    .method-put { background: #fca130; }",
        "    .method-patch { background: #50e3c2; }",
        "    .method-delete { background: #f93e3e; }",
        "    .method-options { background: #0d5aa7; }",
        "    .method-head { background: #9012fe; }",
        "    .method-other { background: #666; }",
        "    .path { font-family: monospace; font-size: 14px; color: #333; }",
        "    .endpoint-summary { padding: 10px 15px; font-weight: 500; }",
        "    .endpoint-description { padding: 0 15px 10px; color: #666; }",
        "    .endpoint-section { padding: 10px 15px; border-top: 1px solid #eee; }",
        "    .section-title { font-weight: 600; margin-bottom: 10px; color: #333; }",
        "    .params-table { width: 100%; border-collapse: collapse; font-size: 13px; }",
        "    .params-table th, .params-table td { padding: 8px; text-align: left; border-bottom: 1px solid #eee; }",
        "    .params-table th { background: #f8f9fa; font-weight: 600; }",
        "    .params-table code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; }",
        "    .schema-block { background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 13px; overflow-x: auto; }",
        "    .schema-type { color: #d73a49; }",
        "    .schema-ref { color: #6f42c1; }",
        "    .schema-enum { color: #22863a; }",
        "    .prop-name { color: #005cc5; }",
        "    .prop-desc { color: #6a737d; font-style: italic; }",
        "    .required { color: #d73a49; margin-left: 2px; }",
        "    .response { margin-bottom: 10px; }",
        "    .status-code { display: inline-block; padding: 2px 8px; border-radius: 3px; font-weight: bold; font-size: 12px; margin-right: 10px; }",
        "    .status-success { background: #d4edda; color: #155724; }",
        "    .status-error { background: #f8d7da; color: #721c24; }",
        "    .status-other { background: #e2e3e5; color: #383d41; }",
        "    .response-desc { color: #666; }",
        "    .sidebar-title.api::before { content: '📡 '; }",
    ])
    parts.append("  </style>")
    parts.extend([
        "</head>",
        "<body>",
    ])
    return parts
