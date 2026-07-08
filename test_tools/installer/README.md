# jsonui-test CLI installer — moved to jsonui-cli

The jsonui-test CLI installer now lives in the
[`jsonui-cli`](https://github.com/Tai-Kimura/jsonui-cli) repo
(`test_tools/installer/`). The `bootstrap.sh` next to this file is a thin
compatibility redirect that forwards to it, so old install commands keep working:

```bash
curl -fsSL https://raw.githubusercontent.com/Tai-Kimura/jsonui-cli/main/test_tools/installer/bootstrap.sh | bash
```

See `../README.md` for details on what moved and what stays in this repo.
