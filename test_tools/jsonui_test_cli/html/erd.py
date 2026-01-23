"""ER Diagram HTML generation from OpenAPI schema files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .sidebar import escape_html


def generate_erd_html(
    schema_files: list[dict],
    title: str = "ER Diagram",
    current_doc_path: str = "db/erd.html",
    category_docs: list[dict] | None = None
) -> str:
    """
    Generate HTML page with Mermaid ER diagram from schema files.

    Args:
        schema_files: List of schema file dicts with 'name', 'swagger_data', 'path'
        title: Page title
        current_doc_path: Current document path for navigation
        category_docs: List of docs in the same category for sidebar

    Returns:
        Complete HTML string with ER diagram
    """
    # Build Mermaid ER diagram definition
    mermaid_code = _build_mermaid_erd(schema_files)

    html_parts = _get_html_header(title)

    rel_root = _get_relative_root(current_doc_path)

    # Sidebar
    html_parts.extend(_generate_sidebar(category_docs, current_doc_path, rel_root))

    # Main content
    html_parts.extend([
        "  <main class='main-content'>",
        f"    <h1>{escape_html(title)}</h1>",
        "    <p class='description'>Database table relationships visualized from schema definitions.</p>",
        "    <div class='diagram-container'>",
        "      <pre class='mermaid'>",
        mermaid_code,
        "      </pre>",
        "    </div>",
        "    <div class='legend'>",
        "      <h3>Legend</h3>",
        "      <ul>",
        "        <li><strong>PK</strong> - Primary Key</li>",
        "        <li><strong>FK</strong> - Foreign Key</li>",
        "        <li><strong>UK</strong> - Unique Key</li>",
        "        <li><code>||--o{</code> - One to Many relationship</li>",
        "        <li><code>||--||</code> - One to One relationship</li>",
        "      </ul>",
        "    </div>",
        "  </main>",
        "  <script src='https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'></script>",
        "  <script>",
        "    mermaid.initialize({",
        "      startOnLoad: true,",
        "      theme: 'default',",
        "      er: {",
        "        useMaxWidth: true,",
        "        layoutDirection: 'TB'",
        "      }",
        "    });",
        "  </script>",
        "</body>",
        "</html>",
    ])

    return '\n'.join(html_parts)


def _build_mermaid_erd(schema_files: list[dict]) -> str:
    """
    Build Mermaid ER diagram code from schema files.

    Args:
        schema_files: List of schema file dicts

    Returns:
        Mermaid erDiagram code
    """
    lines = ["erDiagram"]

    # Collect all tables and relationships
    tables: dict[str, dict] = {}  # table_name -> {fields, pk, fks}
    relationships: list[tuple[str, str, str, str]] = []  # (from_table, to_table, rel_type, label)

    for schema_file in schema_files:
        swagger_data = schema_file.get('swagger_data', {})
        if not swagger_data:
            continue

        info = swagger_data.get('info', {})
        table_name = info.get('x-table-name', '')

        if not table_name:
            # Try to extract from schema name
            schemas = swagger_data.get('components', {}).get('schemas', {})
            for schema_name, schema_def in schemas.items():
                # Skip enum schemas
                if schema_def.get('type') == 'string' and 'enum' in schema_def:
                    continue
                # Use first non-enum schema name as table name (snake_case)
                table_name = _to_snake_case(schema_name)
                break

        if not table_name:
            continue

        schemas = swagger_data.get('components', {}).get('schemas', {})

        for schema_name, schema_def in schemas.items():
            # Skip enum schemas
            if schema_def.get('type') == 'string' and 'enum' in schema_def:
                continue

            properties = schema_def.get('properties', {})
            required_fields = schema_def.get('required', [])

            fields = []
            pk_field = None
            fk_relations = []

            for prop_name, prop_def in properties.items():
                prop_type = prop_def.get('type', 'string')
                mermaid_type = _map_type_to_mermaid(prop_type, prop_def.get('format', ''))

                # Check for keys
                key_markers = []
                if prop_def.get('x-primary-key'):
                    key_markers.append('PK')
                    pk_field = prop_name
                if prop_def.get('x-unique'):
                    key_markers.append('UK')
                if prop_def.get('x-foreign-key'):
                    key_markers.append('FK')
                    # Extract FK reference
                    fk = prop_def['x-foreign-key']
                    if isinstance(fk, dict):
                        ref_table = fk.get('table', '')
                        ref_column = fk.get('column', 'id')
                    else:
                        # String format: "table.column"
                        parts = str(fk).split('.')
                        ref_table = parts[0] if parts else ''
                        ref_column = parts[1] if len(parts) > 1 else 'id'

                    if ref_table:
                        fk_relations.append((ref_table, prop_name))

                key_str = ','.join(key_markers) if key_markers else ''
                comment = f'"{prop_def.get("description", "")}"' if prop_def.get('description') else ''

                fields.append({
                    'name': prop_name,
                    'type': mermaid_type,
                    'key': key_str,
                    'comment': comment
                })

            tables[table_name] = {
                'fields': fields,
                'pk': pk_field,
                'fks': fk_relations
            }

            # Add relationships
            for ref_table, fk_field in fk_relations:
                relationships.append((ref_table, table_name, '||--o{', fk_field))

    # Generate Mermaid code for tables
    for table_name, table_info in tables.items():
        # Sanitize table name for Mermaid (replace special chars)
        safe_table_name = _sanitize_mermaid_name(table_name)
        lines.append(f"    {safe_table_name} {{")
        for field in table_info['fields']:
            field_line = f"        {field['type']} {field['name']}"
            if field['key']:
                field_line += f" {field['key']}"
            lines.append(field_line)
        lines.append("    }")

    # Generate relationships
    for from_table, to_table, rel_type, label in relationships:
        safe_from = _sanitize_mermaid_name(from_table)
        safe_to = _sanitize_mermaid_name(to_table)
        # Check if from_table exists in our tables
        if from_table in tables:
            lines.append(f"    {safe_from} {rel_type} {safe_to} : \"{label}\"")
        else:
            # External reference - still show relationship but table won't have fields
            lines.append(f"    {safe_from} {rel_type} {safe_to} : \"{label}\"")

    return '\n'.join(lines)


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _sanitize_mermaid_name(name: str) -> str:
    """Sanitize name for Mermaid diagram (remove special characters)."""
    # Replace non-alphanumeric chars with underscore
    import re
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def _map_type_to_mermaid(json_type: str, format: str = '') -> str:
    """Map JSON Schema type to Mermaid ER diagram type."""
    type_mapping = {
        'integer': 'int',
        'number': 'float',
        'string': 'string',
        'boolean': 'bool',
        'array': 'array',
        'object': 'json',
    }

    base_type = type_mapping.get(json_type, 'string')

    # Handle specific formats
    if format == 'date-time':
        return 'datetime'
    elif format == 'date':
        return 'date'
    elif format == 'uuid':
        return 'uuid'
    elif format == 'email':
        return 'string'

    return base_type


def _get_relative_root(doc_path: str) -> str:
    """Calculate relative path to root from document path."""
    depth = len(Path(doc_path).parent.parts)
    if depth == 0:
        return "./"
    return "../" * depth


def _generate_sidebar(
    category_docs: list[dict] | None,
    current_doc_path: str | None,
    rel_root: str
) -> list[str]:
    """Generate sidebar with navigation links."""
    parts = [
        "  <aside class='sidebar'>",
        "    <div class='sidebar-header'>",
        f"      <a href='{rel_root}index.html' class='sidebar-title'>&larr; Back to Index</a>",
        "    </div>",
        "    <nav class='sidebar-nav'>",
        "      <div class='nav-section'>",
        "        <div class='nav-section-title'>ER Diagram</div>",
        "        <ul class='nav-list'>",
        "          <li class='active'><a href='erd.html'>ER Diagram</a></li>",
        "        </ul>",
        "      </div>",
    ]

    if category_docs:
        parts.extend([
            "      <div class='nav-section'>",
            "        <div class='nav-section-title'>Tables</div>",
            "        <ul class='nav-list'>",
        ])
        for doc in category_docs:
            doc_name = doc.get('name', '')
            doc_path = doc.get('path', '')
            doc_filename = Path(doc_path).name if doc_path else ''
            parts.append(f"          <li><a href='{doc_filename}'>{escape_html(doc_name)}</a></li>")
        parts.extend([
            "        </ul>",
            "      </div>",
        ])

    parts.extend([
        "    </nav>",
        "  </aside>",
    ])
    return parts


def _get_html_header(title: str) -> list[str]:
    """Generate HTML header with styles for ER diagram page."""
    parts = [
        "<!DOCTYPE html>",
        "<html lang='ja'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"  <title>{escape_html(title)}</title>",
        "  <style>",
        "    * { margin: 0; padding: 0; box-sizing: border-box; }",
        "    body {",
        "      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;",
        "      background: #f5f5f5;",
        "      color: #333;",
        "      line-height: 1.6;",
        "      display: flex;",
        "    }",
        "    .sidebar {",
        "      width: 280px;",
        "      min-width: 280px;",
        "      height: 100vh;",
        "      position: fixed;",
        "      top: 0;",
        "      left: 0;",
        "      background: #f8f9fa;",
        "      border-right: 1px solid #e0e0e0;",
        "      overflow-y: auto;",
        "      padding: 20px;",
        "    }",
        "    .sidebar-header {",
        "      padding-bottom: 15px;",
        "      margin-bottom: 15px;",
        "      border-bottom: 1px solid #e0e0e0;",
        "    }",
        "    .sidebar-title {",
        "      color: #007AFF;",
        "      text-decoration: none;",
        "      font-size: 0.9em;",
        "    }",
        "    .sidebar-title:hover {",
        "      text-decoration: underline;",
        "    }",
        "    .sidebar-nav {",
        "      padding: 0;",
        "    }",
        "    .nav-section {",
        "      margin-bottom: 20px;",
        "    }",
        "    .nav-section-title {",
        "      font-size: 0.75em;",
        "      font-weight: 600;",
        "      color: #888;",
        "      text-transform: uppercase;",
        "      letter-spacing: 0.5px;",
        "      margin-bottom: 8px;",
        "    }",
        "    .nav-list {",
        "      list-style: none;",
        "    }",
        "    .nav-list li {",
        "      margin: 2px 0;",
        "    }",
        "    .nav-list li.active a {",
        "      background: #007AFF;",
        "      color: white;",
        "    }",
        "    .nav-list li a {",
        "      display: block;",
        "      padding: 6px 12px;",
        "      color: #555;",
        "      text-decoration: none;",
        "      border-radius: 4px;",
        "      font-size: 0.85em;",
        "    }",
        "    .nav-list li a:hover {",
        "      background: #e9ecef;",
        "      color: #007AFF;",
        "    }",
        "    .main-content {",
        "      margin-left: 280px;",
        "      flex: 1;",
        "      padding: 30px 40px;",
        "      min-width: 0;",
        "    }",
        "    h1 {",
        "      color: #333;",
        "      border-bottom: 2px solid #007AFF;",
        "      padding-bottom: 10px;",
        "      margin-top: 0;",
        "      margin-bottom: 10px;",
        "    }",
        "    .description {",
        "      color: #666;",
        "      margin-bottom: 30px;",
        "    }",
        "    .diagram-container {",
        "      background: white;",
        "      border-radius: 8px;",
        "      padding: 30px;",
        "      margin-bottom: 30px;",
        "      box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
        "      overflow-x: auto;",
        "    }",
        "    .mermaid {",
        "      text-align: center;",
        "    }",
        "    .legend {",
        "      background: #f8f9fa;",
        "      border-radius: 8px;",
        "      padding: 20px;",
        "      border: 1px solid #e0e0e0;",
        "    }",
        "    .legend h3 {",
        "      font-size: 14px;",
        "      color: #666;",
        "      margin-bottom: 10px;",
        "    }",
        "    .legend ul {",
        "      list-style: none;",
        "      display: flex;",
        "      flex-wrap: wrap;",
        "      gap: 20px;",
        "    }",
        "    .legend li {",
        "      font-size: 13px;",
        "      color: #555;",
        "    }",
        "    .legend code {",
        "      background: #e9ecef;",
        "      padding: 2px 6px;",
        "      border-radius: 3px;",
        "      font-family: 'SF Mono', Monaco, Consolas, monospace;",
        "      font-size: 12px;",
        "    }",
        "    /* Responsive */",
        "    @media (max-width: 768px) {",
        "      .sidebar { display: none; }",
        "      .main-content { margin-left: 0; padding: 20px; }",
        "      .legend ul { flex-direction: column; gap: 8px; }",
        "    }",
        "  </style>",
        "</head>",
        "<body>",
    ]
    return parts
