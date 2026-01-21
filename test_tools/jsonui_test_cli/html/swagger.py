"""Swagger/OpenAPI documentation page HTML generation using Redoc."""

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
    all_tests_nav: dict | None = None,
    current_doc_path: str | None = None
) -> list[str]:
    """
    Generate sidebar HTML for Swagger documentation pages.

    Args:
        title: Page title
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


def generate_swagger_html(
    swagger_data: dict,
    title: str | None = None,
    all_tests_nav: dict | None = None,
    current_doc_path: str | None = None
) -> str:
    """
    Generate HTML documentation page from Swagger/OpenAPI data using Redoc.

    Args:
        swagger_data: Parsed Swagger/OpenAPI data
        title: Optional title override
        all_tests_nav: Navigation data for sidebar
        current_doc_path: Current document's relative path

    Returns:
        Complete HTML string with sidebar and embedded Redoc
    """
    # Extract info
    info = swagger_data.get('info', {})
    doc_title = title or info.get('title', 'API Documentation')

    # Convert swagger data to JSON string for embedding
    swagger_json = json.dumps(swagger_data, ensure_ascii=False)

    # Build HTML
    html_parts = _get_html_header(doc_title)
    html_parts.extend(generate_swagger_sidebar(doc_title, all_tests_nav, current_doc_path))

    # Main content with Redoc
    html_parts.extend([
        "  <main class='main-content redoc-container'>",
        "    <div id='redoc-container'></div>",
        "  </main>",
        "",
        "  <!-- Redoc -->",
        "  <script src='https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js'></script>",
        "  <script>",
        f"    const spec = {swagger_json};",
        "    Redoc.init(spec, {",
        "      scrollYOffset: 0,",
        "      hideDownloadButton: false,",
        "      expandResponses: '200,201',",
        "      pathInMiddlePanel: true,",
        "      hideHostname: true,",
        "      nativeScrollbars: true,",
        "    }, document.getElementById('redoc-container'));",
        "  </script>",
    ])

    # Close HTML
    html_parts.extend(get_toggle_script())
    html_parts.extend([
        "</body>",
        "</html>"
    ])

    return '\n'.join(html_parts)


def _get_html_header(title: str) -> list[str]:
    """Generate HTML header with styles for Swagger documentation with Redoc."""
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
    # Add Redoc container styles
    parts.extend([
        "    /* Redoc container styles */",
        "    .redoc-container { padding: 0; }",
        "    #redoc-container { min-height: calc(100vh - 40px); }",
        "    .sidebar-title.api::before { content: '📡 '; }",
    ])
    parts.append("  </style>")
    parts.extend([
        "</head>",
        "<body>",
    ])
    return parts
