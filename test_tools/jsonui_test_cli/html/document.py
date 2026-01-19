"""Document page HTML generation with sidebar."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .styles import get_screen_styles, get_toggle_script
from .sidebar import escape_html


def generate_document_sidebar(
    title: str,
    all_tests_nav: dict | None = None,
    current_doc_path: str | None = None
) -> list[str]:
    """
    Generate sidebar HTML for document pages.

    Args:
        title: Page title
        all_tests_nav: Navigation data {'screens': [...], 'flows': [...]}
        current_doc_path: Current document's relative path

    Returns:
        List of HTML strings for the sidebar
    """
    parts = []
    parts.append("  <nav class='sidebar'>")
    parts.append("    <a href='../index.html' class='back-link'>&larr; Back to Index</a>")
    parts.append(f"    <h2>{escape_html(title)}</h2>")

    # Flow Tests navigation (collapsible, collapsed by default)
    if all_tests_nav and all_tests_nav.get('flows'):
        flows = all_tests_nav['flows']
        parts.append("    <div class='sidebar-section'>")
        parts.append(f"      <div class='sidebar-title flow collapsed' id='flows-title' onclick=\"toggleSection('flows')\"><span class='arrow'>▼</span> Flow Tests <span class='count'>{len(flows)}</span></div>")
        parts.append("      <div class='sidebar-list collapsed' id='flows-list'>")
        parts.append("        <ul>")
        for f in flows:
            doc_link = f"<a href='../{f['document']}' class='doc-link' title='View specification document'>📄</a>" if f.get('document') else ""
            parts.append(f"          <li><a href='../{f['path']}' class='nav-link' title='{escape_html(f['name'])}'>{escape_html(f['name'])}</a>{doc_link}</li>")
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
            is_current = current_doc_path and s.get('document') == current_doc_path
            current_class = " current" if is_current else ""
            doc_link = f"<a href='../{s['document']}' class='doc-link{current_class}' title='View specification document'>📄</a>" if s.get('document') else ""
            parts.append(f"          <li><a href='../{s['path']}' class='nav-link' title='{escape_html(s['name'])}'>{escape_html(s['name'])}</a>{doc_link}</li>")
        parts.append("        </ul>")
        parts.append("      </div>")
        parts.append("    </div>")

    parts.append("  </nav>")
    return parts


def _extract_title_from_html(html_content: str) -> str:
    """Extract title from HTML content."""
    # Try to find <title> tag
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()

    # Try to find <h1> tag
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
    if h1_match:
        return h1_match.group(1).strip()

    return "Document"


def _extract_body_content(html_content: str) -> str:
    """Extract body content from HTML, or return as-is if no body tag."""
    # Try to extract content between <body> tags
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.IGNORECASE | re.DOTALL)
    if body_match:
        return body_match.group(1).strip()

    # If no body tag, check if it looks like a full HTML document
    if re.search(r'<html|<!DOCTYPE', html_content, re.IGNORECASE):
        # It's an HTML document but we couldn't find body - return empty
        return html_content

    # It's probably just HTML fragment, return as-is
    return html_content


def _extract_head_styles(html_content: str) -> str:
    """Extract style tags from HTML head."""
    styles = []

    # Find all <style> tags
    style_matches = re.findall(r'<style[^>]*>(.*?)</style>', html_content, re.IGNORECASE | re.DOTALL)
    for style in style_matches:
        styles.append(style)

    # Find <link rel="stylesheet"> tags (we can't inline these, but note them)
    # For now, we skip external stylesheets

    return '\n'.join(styles)


def generate_document_html(
    source_path: Path,
    title: str | None = None,
    all_tests_nav: dict | None = None,
    current_doc_path: str | None = None,
    iframe_src: str | None = None
) -> str:
    """
    Generate HTML documentation page with sidebar from source document.

    Args:
        source_path: Path to the source HTML/MD document
        title: Optional title override
        all_tests_nav: Navigation data {'screens': [...], 'flows': [...]}
        current_doc_path: Current document's relative path
        iframe_src: If provided, embed using iframe with this src (for HTML with scripts/styles)

    Returns:
        Complete HTML string with sidebar
    """
    # Read source document
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            source_content = f.read()
    except Exception as e:
        source_content = f"<p class='error'>Error reading document: {e}</p>"

    # Determine if it's markdown or HTML
    is_markdown = source_path.suffix.lower() in ['.md', '.markdown']

    if is_markdown:
        # Convert markdown to HTML (simple conversion)
        body_content = _convert_markdown_to_html(source_content)
        doc_title = title or source_path.stem.replace('_', ' ').title()
        original_styles = ""
    elif iframe_src:
        # For iframe mode, we only need the title
        doc_title = title or _extract_title_from_html(source_content)
        body_content = ""
        original_styles = ""
    else:
        # Extract parts from HTML for embedding
        doc_title = title or _extract_title_from_html(source_content)
        body_content = _extract_body_content(source_content)
        original_styles = _extract_head_styles(source_content)

    # Build HTML with sidebar
    use_iframe = bool(iframe_src) and not is_markdown
    html_parts = _get_html_header(doc_title, original_styles, use_iframe)
    html_parts.extend(generate_document_sidebar(doc_title, all_tests_nav, current_doc_path))

    # Main content wrapper
    html_parts.append("  <main class='main-content document-content'>")

    if use_iframe:
        # Use iframe to embed the original HTML document (preserves all scripts/styles)
        html_parts.append(f"    <iframe class='document-iframe' src='{iframe_src}' title='{escape_html(doc_title)}'></iframe>")
    else:
        html_parts.append(f"    <div class='document-body'>")
        html_parts.append(body_content)
        html_parts.append("    </div>")

    html_parts.append("  </main>")

    # Close HTML
    html_parts.extend(get_toggle_script())
    html_parts.extend([
        "</body>",
        "</html>"
    ])

    return '\n'.join(html_parts)


def _convert_markdown_to_html(md_content: str) -> str:
    """Simple markdown to HTML conversion."""
    import html as html_module

    lines = md_content.split('\n')
    html_lines = []
    in_code_block = False
    in_list = False
    list_type = None

    for line in lines:
        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                lang = line[3:].strip()
                html_lines.append(f'<pre><code class="language-{lang}">' if lang else '<pre><code>')
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(html_module.escape(line))
            continue

        # Close list if line is empty or not a list item
        if in_list and (not line.strip() or not (line.strip().startswith('- ') or line.strip().startswith('* ') or re.match(r'^\d+\.\s', line.strip()))):
            html_lines.append(f'</{list_type}>')
            in_list = False
            list_type = None

        # Headers
        if line.startswith('######'):
            html_lines.append(f'<h6>{html_module.escape(line[6:].strip())}</h6>')
        elif line.startswith('#####'):
            html_lines.append(f'<h5>{html_module.escape(line[5:].strip())}</h5>')
        elif line.startswith('####'):
            html_lines.append(f'<h4>{html_module.escape(line[4:].strip())}</h4>')
        elif line.startswith('###'):
            html_lines.append(f'<h3>{html_module.escape(line[3:].strip())}</h3>')
        elif line.startswith('##'):
            html_lines.append(f'<h2>{html_module.escape(line[2:].strip())}</h2>')
        elif line.startswith('#'):
            html_lines.append(f'<h1>{html_module.escape(line[1:].strip())}</h1>')
        # Unordered list
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list or list_type != 'ul':
                if in_list:
                    html_lines.append(f'</{list_type}>')
                html_lines.append('<ul>')
                in_list = True
                list_type = 'ul'
            content = line.strip()[2:]
            html_lines.append(f'<li>{_process_inline_markdown(content)}</li>')
        # Ordered list
        elif re.match(r'^\d+\.\s', line.strip()):
            if not in_list or list_type != 'ol':
                if in_list:
                    html_lines.append(f'</{list_type}>')
                html_lines.append('<ol>')
                in_list = True
                list_type = 'ol'
            content = re.sub(r'^\d+\.\s', '', line.strip())
            html_lines.append(f'<li>{_process_inline_markdown(content)}</li>')
        # Horizontal rule
        elif line.strip() in ['---', '***', '___']:
            html_lines.append('<hr>')
        # Paragraph
        elif line.strip():
            html_lines.append(f'<p>{_process_inline_markdown(line)}</p>')
        else:
            html_lines.append('')

    # Close any open list
    if in_list:
        html_lines.append(f'</{list_type}>')

    return '\n'.join(html_lines)


def _process_inline_markdown(text: str) -> str:
    """Process inline markdown (bold, italic, code, links)."""
    import html as html_module

    # Escape HTML first
    text = html_module.escape(text)

    # Code (backticks) - do this first to avoid processing markdown inside code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)

    # Italic
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    return text


def _get_html_header(title: str, additional_styles: str = "", use_iframe: bool = False) -> list[str]:
    """Generate HTML header with styles."""
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
    # Add document-specific styles
    parts.extend([
        "    /* Document content styles */",
        "    .document-content { padding: 30px 40px; }",
        "    .document-body { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "    .document-body h1 { color: #333; border-bottom: 2px solid #007AFF; padding-bottom: 10px; margin-top: 0; }",
        "    .document-body h2 { color: #444; margin-top: 25px; }",
        "    .document-body h3 { color: #555; margin-top: 20px; }",
        "    .document-body p { line-height: 1.6; color: #333; }",
        "    .document-body ul, .document-body ol { padding-left: 25px; }",
        "    .document-body li { margin: 5px 0; line-height: 1.5; }",
        "    .document-body code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; }",
        "    .document-body pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }",
        "    .document-body pre code { background: none; padding: 0; }",
        "    .document-body a { color: #007AFF; text-decoration: none; }",
        "    .document-body a:hover { text-decoration: underline; }",
        "    .document-body table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
        "    .document-body th, .document-body td { border: 1px solid #ddd; padding: 10px; text-align: left; }",
        "    .document-body th { background: #f5f5f5; }",
        "    .document-body img { max-width: 100%; height: auto; }",
        "    .error { color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 5px; }",
    ])
    # Add iframe styles if needed
    if use_iframe:
        parts.extend([
            "    /* Iframe styles for embedded documents */",
            "    .document-content { padding: 0; height: calc(100vh - 20px); }",
            "    .document-iframe { width: 100%; height: 100%; border: none; background: #fff; }",
        ])
    if additional_styles:
        parts.append(f"    /* Original document styles */")
        parts.append(f"    {additional_styles}")
    parts.append("  </style>")
    parts.extend([
        "</head>",
        "<body>",
    ])
    return parts
