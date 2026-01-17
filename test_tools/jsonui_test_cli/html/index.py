"""Index page HTML generation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .styles import get_index_styles, get_index_scripts
from .sidebar import generate_index_sidebar, escape_html


def generate_index_html(
    output_dir: Path,
    files: list[dict],
    title: str,
    has_mermaid_diagram: bool = False
) -> None:
    """
    Generate index.html with collapsible categories and sidebar navigation.

    Args:
        output_dir: Output directory path
        files: List of generated file info dicts
        title: Page title
        has_mermaid_diagram: Whether a Mermaid diagram was generated
    """
    screen_files = [f for f in files if f['type'] == 'screen']
    flow_files = [f for f in files if f['type'] == 'flow']
    other_files = [f for f in files if f['type'] not in ['screen', 'flow']]

    screen_count = len(screen_files)
    flow_count = len(flow_files)
    total_cases = sum(f['case_count'] for f in files)
    total_steps = sum(f['step_count'] for f in files)

    html_parts = _get_html_header(title)
    html_parts.extend(generate_index_sidebar(title, flow_files, screen_files, has_mermaid_diagram))

    # Main content
    html_parts.append("  <main class='main-content'>")
    html_parts.append(f"    <h1>{escape_html(title)}</h1>")

    # Flow Diagram link (if available)
    if has_mermaid_diagram:
        html_parts.extend([
            "    <div class='diagram-link-container'>",
            "      <a href='diagram.html' class='diagram-link'>",
            "        <span class='diagram-icon'>📊</span>",
            "        <span class='diagram-text'>View Flow Diagram</span>",
            "        <span class='diagram-desc'>Screen transition visualization</span>",
            "      </a>",
            "    </div>",
        ])

    # Summary section
    html_parts.extend([
        "    <div class='summary'>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{len(files)}</div>",
        "        <div class='summary-label'>Test Files</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{screen_count}</div>",
        "        <div class='summary-label'>Screen Tests</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{flow_count}</div>",
        "        <div class='summary-label'>Flow Tests</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{total_cases}</div>",
        "        <div class='summary-label'>Test Cases</div>",
        "      </div>",
        "      <div class='summary-item'>",
        f"        <div class='summary-value'>{total_steps}</div>",
        "        <div class='summary-label'>Total Steps</div>",
        "      </div>",
        "    </div>",
    ])

    # Flow Tests category first (collapsible, starts collapsed)
    if flow_files:
        html_parts.extend([
            "    <div class='category'>",
            "      <div class='category-header collapsed' id='flows-header' onclick=\"toggleCategory('flows')\">",
            f"        <h2><span class='arrow'>▼</span> Flow Tests <span class='category-badge flow'>{flow_count}</span></h2>",
            "      </div>",
            "      <div class='category-content collapsed' id='flows-content'>",
            "        <ul class='test-list'>",
        ])
        for f in flow_files:
            html_parts.extend([
                "          <li class='test-item flow'>",
                f"            <a href='{f['path']}' class='test-name'>{escape_html(f['name'])}</a>",
                "            <div class='test-meta'>",
                f"              <span class='badge badge-platform'>{f['platform']}</span>",
                f"              {f['step_count']} steps",
                "            </div>",
            ])
            if f['description']:
                html_parts.append(f"            <div class='test-description'>{escape_html(f['description'])}</div>")
            html_parts.append("          </li>")
        html_parts.extend([
            "        </ul>",
            "      </div>",
            "    </div>",
        ])

    # Screen Tests category (collapsible, starts collapsed)
    if screen_files:
        html_parts.extend([
            "    <div class='category'>",
            "      <div class='category-header collapsed' id='screens-header' onclick=\"toggleCategory('screens')\">",
            f"        <h2><span class='arrow'>▼</span> Screen Tests <span class='category-badge screen'>{screen_count}</span></h2>",
            "      </div>",
            "      <div class='category-content collapsed' id='screens-content'>",
            "        <ul class='test-list'>",
        ])
        for f in screen_files:
            html_parts.extend([
                "          <li class='test-item screen'>",
                f"            <a href='{f['path']}' class='test-name'>{escape_html(f['name'])}</a>",
                "            <div class='test-meta'>",
                f"              <span class='badge badge-platform'>{f['platform']}</span>",
                f"              {f['case_count']} cases, {f['step_count']} steps",
                "            </div>",
            ])
            if f['description']:
                html_parts.append(f"            <div class='test-description'>{escape_html(f['description'])}</div>")
            html_parts.append("          </li>")
        html_parts.extend([
            "        </ul>",
            "      </div>",
            "    </div>",
        ])

    # Other Tests category (collapsible, starts collapsed)
    if other_files:
        html_parts.extend([
            "    <div class='category'>",
            "      <div class='category-header collapsed' id='other-header' onclick=\"toggleCategory('other')\">",
            f"        <h2><span class='arrow'>▼</span> Other Tests <span class='category-badge'>{len(other_files)}</span></h2>",
            "      </div>",
            "      <div class='category-content collapsed' id='other-content'>",
            "        <ul class='test-list'>",
        ])
        for f in other_files:
            html_parts.extend([
                "          <li class='test-item'>",
                f"            <a href='{f['path']}' class='test-name'>{escape_html(f['name'])}</a>",
                "            <div class='test-meta'>",
                f"              <span class='badge'>{f['type']}</span>",
                f"              <span class='badge badge-platform'>{f['platform']}</span>",
                "            </div>",
            ])
            if f['description']:
                html_parts.append(f"            <div class='test-description'>{escape_html(f['description'])}</div>")
            html_parts.append("          </li>")
        html_parts.extend([
            "        </ul>",
            "      </div>",
            "    </div>",
        ])

    # Footer
    html_parts.extend([
        f"    <p class='generated'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        "  </main>",
        "</body>",
        "</html>",
    ])

    # Write index.html
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_parts))

    print(f"  Generated: {index_path}")


def _get_html_header(title: str) -> list[str]:
    """Get HTML header with styles for index page."""
    parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        f"  <title>{escape_html(title)}</title>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "  <style>",
    ]
    parts.extend(get_index_styles())
    parts.append("  </style>")
    parts.extend(get_index_scripts())
    parts.extend([
        "</head>",
        "<body>",
    ])
    return parts
