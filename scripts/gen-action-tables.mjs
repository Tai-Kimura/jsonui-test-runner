#!/usr/bin/env node
// Regenerates the action/assertion tables in README.md and CLAUDE.md from
// schemas/actions.schema.json — the canonical step inventory. The tables used
// to be maintained by hand in several places and drifted (24 documented vs 37+
// defined); this script makes the schema the only place a step is described.
//
//   node scripts/gen-action-tables.mjs           rewrite the tables in place
//   node scripts/gen-action-tables.mjs --check   exit 1 if any table is stale
//   node scripts/gen-action-tables.mjs --json    machine-readable dump (stdout)
//
// Each step definition must carry `x-doc`: { "ja": <説明>, "platforms": <注記>? }.
// A missing x-doc is a hard error so a new schema entry cannot ship
// undocumented. Optional params render with `?`, schema defaults with `=`.

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SCHEMA_PATH = join(ROOT, "schemas", "actions.schema.json");
const TARGETS = ["README.md", "CLAUDE.md"].map((f) => join(ROOT, f));

// Shared step attributes documented in their own section, not per-row.
const COMMON = new Set(["action", "assert", "label", "optional", "when", "screen"]);

const defs = JSON.parse(readFileSync(SCHEMA_PATH, "utf8")).definitions;

function defaultOf(prop) {
  if (prop.default !== undefined) return prop.default;
  const ref = prop.$ref?.split("/").pop();
  return ref ? defs[ref]?.default : undefined;
}

function steps(group, discriminator) {
  return defs[group].oneOf.map(({ $ref }) => {
    const key = $ref.split("/").pop();
    const def = defs[key];
    const xdoc = def["x-doc"];
    if (!xdoc?.ja) {
      throw new Error(
        `${key}: missing x-doc.ja in actions.schema.json — every step must document itself`,
      );
    }
    const params = Object.entries(def.properties)
      .filter(([name]) => !COMMON.has(name))
      .map(([name, prop]) => ({
        name,
        required: (def.required ?? []).includes(name),
        default: defaultOf(prop),
      }));
    return { name: def.properties[discriminator].const, ja: xdoc.ja, platforms: xdoc.platforms ?? null, params };
  });
}

function paramCell(params) {
  if (params.length === 0) return "-";
  return params
    .map((p) => `\`${p.name}${p.required ? "" : "?"}${p.default !== undefined ? `=${p.default}` : ""}\``)
    .join(", ");
}

function table(header, rows) {
  const lines = [`| ${header} | 説明 | パラメータ | プラットフォーム |`, "|---|---|---|---|"];
  for (const s of rows) {
    lines.push(`| \`${s.name}\` | ${s.ja} | ${paramCell(s.params)} | ${s.platforms ?? "-"} |`);
  }
  return lines.join("\n");
}

const actions = steps("action", "action");
const assertions = steps("assertion", "assert");
const blocks = {
  actions: table("アクション", actions),
  assertions: table("アサーション", assertions),
};

if (process.argv.includes("--json")) {
  process.stdout.write(
    JSON.stringify({ generatedFrom: "schemas/actions.schema.json", actions, assertions }, null, 2) + "\n",
  );
  process.exit(0);
}

const check = process.argv.includes("--check");
let stale = [];
for (const path of TARGETS) {
  const before = readFileSync(path, "utf8");
  let after = before;
  for (const [kind, body] of Object.entries(blocks)) {
    const re = new RegExp(`(<!-- generated:${kind} -->\\n)[\\s\\S]*?(<!-- /generated:${kind} -->)`);
    if (!re.test(after)) throw new Error(`${path}: marker pair for "${kind}" not found`);
    after = after.replace(re, `$1${body}\n$2`);
  }
  if (after !== before) {
    if (check) stale.push(path);
    else {
      writeFileSync(path, after);
      console.log(`updated ${path}`);
    }
  }
}

if (check) {
  if (stale.length > 0) {
    console.error(`stale generated tables (run \`npm run docs\`): ${stale.join(", ")}`);
    process.exit(1);
  }
  console.log(`tables up to date (${actions.length} actions, ${assertions.length} assertions)`);
} else {
  console.log(`${actions.length} actions, ${assertions.length} assertions`);
}
