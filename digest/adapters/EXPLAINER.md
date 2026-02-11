# EXPLAINER — Adapters (LLM & Email)

> Reasoning documentation for the adapter layer. Each section captures the
> decision path behind a significant implementation.

---

## Add Anthropic LLM Adapter and Provider Selection (T5.3)

### Technical Logic

Two adapter classes implement the same `LLMPort` protocol defined in
`digest/domain/llm_port.py`:

| Adapter | File | Default model |
|---------|------|---------------|
| `OpenAILLM` | `llm_openai.py` | `gpt-4o-mini` |
| `AnthropicLLM` | `llm_anthropic.py` | `claude-3-haiku-20240307` |

Both expose `summarize(title, snippet) -> str` and
`rank(items, top_n) -> list[ItemWithSummary]`.

Selection happens at runtime in `scripts/build_digest.py` via the `_make_llm()`
factory, driven by the `LLM_PROVIDER` environment variable (`openai` by default,
`anthropic` if set). The same `LLM_API_KEY` and `LLM_MODEL` env vars are reused
regardless of provider.

The Anthropic adapter creates the client once in `__init__` (unlike the OpenAI
adapter which creates it per call) because `anthropic.Anthropic` is lightweight
and thread-safe.

### Decision Log

| Decision | Reason | Alternatives Considered |
|----------|--------|------------------------|
| Separate adapter files per provider | Keeps each adapter self-contained; no runtime import of unused SDK | Single file with `if/else` blocks (harder to maintain) |
| Selection via env var (`LLM_PROVIDER`) | Consistent with existing config pattern (`LLM_API_KEY`, `LLM_MODEL`); zero-code change to switch providers | Config in `sources.yaml` (mixes infra secrets with content config) |
| Same prompt text for both providers | Ensures identical digest quality regardless of backend; easier to compare results | Provider-specific prompt tuning (premature optimisation at this stage) |
| `anthropic` as a required dependency | Simplifies install; the package is lightweight (~2 MB) | Optional dependency with lazy import (adds complexity for marginal saving) |

### Step-by-Step for Humans

1. **Setup**: `pip install -e .` (installs both `openai` and `anthropic`).
2. **Switch provider**: `export LLM_PROVIDER=anthropic` and `export LLM_API_KEY=sk-ant-...`.
3. **Execute**: `python scripts/build_digest.py` — the log line `Usando proveedor LLM: Anthropic` confirms the selection.
4. **Verify**: The email content should have the same structure (title, URL, summary, source) regardless of provider.

### Edge Cases & Logic Gaps

| Scenario | How It's Handled | Severity |
|----------|-----------------|----------|
| Unknown `LLM_PROVIDER` value (e.g. `gemini`) | Falls through to OpenAI (default branch) | Low — logged as "OpenAI" |
| Missing `LLM_API_KEY` | Both adapters raise `ValueError` immediately at init | Medium — fail-fast is desired |
| Anthropic API returns unexpected content blocks | Only `text`-type blocks are joined; others are silently ignored | Low |
| Rank response not parseable (neither provider) | Unparseable indices are skipped; unmentioned items appended at end | Low |

---

## Add Ruff Linter Job to CI Workflow (T8.4)

### Technical Logic

A new `lint` job was added to `.github/workflows/weekly-digest.yml` that runs
before the `digest` job (`needs: lint`). It installs dev dependencies
(`pip install -e ".[dev]"`) and runs:

1. `ruff check .` — static analysis (pyflakes, pycodestyle, isort, etc.).
2. `ruff format --check .` — verifies code formatting without modifying files.

If either step fails the workflow stops before executing the digest, preventing
broken code from sending emails.

### Decision Log

| Decision | Reason | Alternatives Considered |
|----------|--------|------------------------|
| `ruff` over `flake8` + `black` | Single tool, much faster, already in `pyproject.toml [dev]` | `flake8` + `black` (two tools, slower, more config) |
| Lint as a separate job (not step) | Runs in parallel with nothing; clearer failure signal in Actions UI | Step inside the digest job (blocks digest even if lint is slow) |
| `needs: lint` on digest job | Ensures broken code never runs the pipeline | Independent jobs (could send malformed emails) |

### Step-by-Step for Humans

1. Push any commit or trigger `workflow_dispatch`.
2. In the Actions tab, the `lint` job should show green.
3. If it fails, run `ruff check . --fix && ruff format .` locally and push.

### Edge Cases & Logic Gaps

| Scenario | How It's Handled | Severity |
|----------|-----------------|----------|
| Lint fails on schedule run (no human watching) | Digest is skipped; no email sent that week | Medium — monitor Actions notifications |
| New dependency breaks ruff | `pip install -e ".[dev]"` pins ruff `>=0.1.0`; unlikely to break | Low |
