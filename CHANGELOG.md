# Changelog

Changes are recorded here with a focus on *why* decisions were made, not just what changed.

---

## [0.2.0] — 2026-02-23

### Documentation

**Why MkDocs with Material theme**

The project had no rendered documentation — users had to read source code or the README to understand the API. MkDocs with Material gives us a searchable, navigable doc site with auto-generated API reference (via mkdocstrings) from existing docstrings. This makes the project accessible to users who aren't reading the source.

**Why mkdocs is capped at <2**

MkDocs 2.0 removes the plugin system and redesigns the theming layer, breaking compatibility with Material for MkDocs and mkdocstrings. Since both are core to our doc setup, we pin to 1.x until the ecosystem settles (likely via Zensical, the Material team's planned MkDocs successor).

---

## [0.1.1] — 2026-02-22

### Bug fixes and hardening

**Why enum is now restricted to string columns**

The `enum` constraint was comparing `str(coerced_value)` against the allowed list. This silently broke for booleans — Python's `str(True)` is `"True"` but the YAML enum list contains `"true"` (lowercase). Rather than adding type-dependent string normalization (which would be fragile), we restricted `enum` to string-only columns. Enum checks are fundamentally about categorical labels, which are strings.

**Why float("nan") and float("inf") are now rejected**

Python's `float()` accepts `"nan"`, `"inf"`, and `"-inf"`. These are IEEE 754 special values, not data. A CSV cell containing `"nan"` would pass validation silently — and worse, `NaN != NaN` means uniqueness checks would treat every NaN as distinct. We now reject non-finite floats at the type check stage.

**Why whitespace is now stripped uniformly**

Boolean coercion was stripping whitespace (`" true "` → `"true"`) but no other type was. This meant `" 42 "` failed integer parsing while `" true "` passed. Since CSV cells often have trailing spaces from cut-and-paste or export tools, all types now strip whitespace before coercion. Whitespace-only cells are treated as null.

**Why load_csv now returns (fieldnames, rows)**

Previously a header-only CSV (correct headers, zero data rows) was treated as "all columns missing" because the header information was discarded when there were no rows. Now `load_csv` returns the fieldnames separately, so schema checks work correctly even on empty data.

**Why we switched to utf-8-sig encoding**

CSV files exported from Excel include a UTF-8 BOM (byte order mark). With plain `utf-8` encoding, the BOM was prepended to the first column name — so `"customer_id"` became `"\ufeffcustomer_id"`, causing a schema violation. `utf-8-sig` strips the BOM transparently and is backward-compatible with BOM-less files.

**Why we removed Click's exists=True**

Click's `exists=True` path validation runs before our code, producing Click-styled error messages that bypass our custom `ContractLoadError`/`DataLoadError` handlers. Removing it gives us consistent error messages and makes the error handling paths actually testable.

---

## [0.1.0] — 2026-02-22

### Initial release

**Why this project exists**

Data pipelines fail silently. A CSV lands in the wrong format, a required column goes missing, or a categorical field gets a new value nobody expected — and the failure surfaces three steps downstream, far from where the bad data entered. This tool makes contracts explicit and checks them at the point of ingestion.

**Why YAML for contracts**

The contract needs to be readable by both engineers and non-engineers (analysts, data owners). YAML is the least noisy format for this — it avoids the verbosity of JSON and the unfamiliarity of TOML for most users in data roles. The contract is meant to be committed to the same repo as the pipeline code, reviewed in PRs, and understood by anyone who opens it.

**Why `csv.DictReader` instead of pandas**

Pandas is the obvious choice but it works against us here. It silently coerces values on load — `"NA"` becomes `NaN`, `"True"` becomes `True`, integers become floats when a column has a missing value. For a validator, silent coercion is the enemy: we need to see exactly what the file contains and decide ourselves whether it's valid. `csv.DictReader` gives us every cell as a raw string, so all type decisions are explicit and auditable.

**Why load everything as strings and coerce later**

The contract is the source of truth for types, not the CSV file. Loading raw strings and coercing to declared types keeps the pipeline simple (one representation throughout) and makes error messages precise — we can say "row 12, column `age`: `'not-a-number'` cannot be coerced to integer" rather than a generic pandas dtype error.

**Why these four rules for v1**

`required`, `type_check`, `enum`, and `unique` were chosen because they cover the most common real-world data quality issues with the least implementation complexity. Most broken data pipelines fail because a column is unexpectedly null, a categorical value changed, a type is wrong, or a supposedly unique key has duplicates. More expressive rules (regex patterns, numeric ranges, cross-column logic) add implementation surface area without covering the majority of cases — they belong in v2 once the core is proven.

**Why violations are all collected before reporting**

Stopping at the first error is tempting but unhelpful. If a file has 20 problems, you want to know all 20 so you can fix them in one pass. The validator runs every check on every row and returns the full list, even when earlier checks fail.

**Why Pydantic for the contract model**

The contract file is user-authored YAML. Without validation, a typo in a field name or an invalid type string would cause a cryptic runtime error deep in the validator. Pydantic gives us a clear, declarative schema for the contract itself — if the contract is malformed, the user gets a structured error message before any data is touched.
