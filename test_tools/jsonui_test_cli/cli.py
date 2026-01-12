#!/usr/bin/env python3
"""
JsonUI Test CLI

Command-line interface for validating and generating documentation
from JsonUI test files.
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .validator import TestValidator
from .generator import DocumentGenerator, generate_schema_reference


def cmd_validate(args):
    """Handle validate command."""
    validator = TestValidator()
    total_errors = 0
    total_warnings = 0
    files_checked = 0

    # Collect files
    files_to_validate = []
    for path in args.files:
        p = Path(path)
        if p.is_dir():
            files_to_validate.extend(p.rglob("*.test.json"))
        elif p.exists():
            files_to_validate.append(p)
        else:
            print(f"Warning: Path not found: {path}", file=sys.stderr)

    if not files_to_validate:
        print("No .test.json files found")
        return 1

    # Validate each file
    for file_path in sorted(files_to_validate):
        files_checked += 1
        result = validator.validate_file(file_path)

        if args.verbose or result.errors or result.warnings:
            print(f"\n{file_path}")

        if result.errors:
            for error in result.errors:
                print(error)
            total_errors += len(result.errors)

        if result.warnings and not args.quiet:
            for warning in result.warnings:
                print(warning)
            total_warnings += len(result.warnings)

        if result.is_valid and not result.warnings and args.verbose:
            print("  OK")

    # Summary
    print(f"\n{'='*50}")
    status = "PASSED" if total_errors == 0 else "FAILED"
    print(f"Result: {status}")
    print(f"Files: {files_checked}, Errors: {total_errors}, Warnings: {total_warnings}")

    return 1 if total_errors > 0 else 0


def cmd_generate(args):
    """Handle generate command."""
    generator = DocumentGenerator()

    # Determine output format
    output_format = args.format
    if args.output and not output_format:
        # Infer from extension
        ext = Path(args.output).suffix.lower()
        if ext == ".html":
            output_format = "html"
        else:
            output_format = "markdown"
    elif not output_format:
        output_format = "markdown"

    # Handle schema reference
    if args.schema:
        content = generate_schema_reference(format=output_format)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Schema reference written to: {output_path}")
        else:
            print(content)
        return 0

    # Handle test file documentation
    if not args.file:
        print("Error: Either --file or --schema is required", file=sys.stderr)
        return 1

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        output_path = Path(args.output) if args.output else None
        content = generator.generate(file_path, output_path, format=output_format)

        if content:  # No output file specified
            print(content)
        else:
            print(f"Documentation written to: {output_path}")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="jsonui-test",
        description="JsonUI Test CLI - Validate and generate documentation for test files"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate test files"
    )
    validate_parser.add_argument(
        "files",
        nargs="+",
        help="Files or directories to validate"
    )
    validate_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show all files, including valid ones"
    )
    validate_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Hide warnings, show only errors"
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate documentation from test files"
    )
    generate_parser.add_argument(
        "-f", "--file",
        help="Test file to generate documentation for"
    )
    generate_parser.add_argument(
        "-o", "--output",
        help="Output file path"
    )
    generate_parser.add_argument(
        "--format",
        choices=["markdown", "html"],
        help="Output format (default: inferred from output or markdown)"
    )
    generate_parser.add_argument(
        "--schema",
        action="store_true",
        help="Generate schema reference instead of test documentation"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "generate":
        return cmd_generate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
