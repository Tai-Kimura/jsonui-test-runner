# jsonui-test CLI — moved to jsonui-cli

The `jsonui-test` CLI (validate / generate / report / mock) **no longer lives
here.** It moved to the [`jsonui-cli`](https://github.com/Tai-Kimura/jsonui-cli)
monorepo as a self-contained package under `test_tools/`, alongside `jui` and
`jsonui-doc`.

## Install

```bash
# standalone (just the jsonui-test CLI)
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-cli/main/test_tools/installer/bootstrap.sh | bash

# or as part of a full jsonui-cli install (also installs jui / jsonui-doc)
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-cli/main/installer/bootstrap.sh | bash
```

`installer/bootstrap.sh` in this directory is a thin compatibility redirect to
the jsonui-cli installer above, so old commands keep working.

## What stays in jsonui-test-runner

This repository remains the source of truth for:

- **`schemas/`** — the canonical JSON Schemas for test files
  (`screen-test`, `flow-test`, `actions`, `results`, `description`, `mock`).
- **`drivers/`** — the iOS (XCUITest), Android (UIAutomator), and Web (Playwright)
  execution engines.
- **`examples/`** — sample test files and mocks.

The validator that mirrors these schemas as Python constants lives with the CLI
in jsonui-cli (`test_tools/jsonui_test_cli/`); a drift-guard test there keeps the
two in sync.
