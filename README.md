# Auto Learning Space — Weekly AI/ML/DS Digest

Project to stay up to date with **AI, Machine Learning and Data Science** via a **weekly email digest**: articles from your sources, trends on Hacker News and Reddit, with short summaries and a top pick of the most interesting ones.

## What it does

- **Aggregates** content from RSS, manual links, Hacker News and Reddit (r/MachineLearning, r/artificial).
- **Generates** a short summary per article with an LLM (in Spanish).
- **Selects** a top 3–5 most relevant articles (also with LLM).
- **Sends** a weekly email with that top; you decide which ones to read.

Everything runs on **GitHub Actions**; no own server required.

## Documentation

| Document | Description |
|----------|-------------|
| [Documentation index](docs/README.md) | Links to all project documentation |
| [Architecture](docs/arquitectura.md) | Components, data flow and design decisions |
| [Configuration](docs/configuracion.md) | How to configure sources, manual links and secrets |
| [Usage guide](docs/guia-uso.md) | How to add sources, what to expect in the email and best practices |
| [Requirements](docs/requisitos-digest-semanal.md) | Functional and non-functional requirements |

## Repo structure

```
repo_auto_learning/
├── .github/workflows/
│   └── weekly-digest.yml    # Weekly digest execution (Phase 7)
├── config/
│   ├── sources.yaml        # RSS + HN + Reddit sources
│   └── links.md            # Manual links
├── data/
│   ├── sent-urls.json      # History of URLs already sent (persistence)
│   └── README.md           # Usage and first run
├── digest/                 # Python package (layers: domain, use_cases, adapters)
│   ├── domain/
│   ├── use_cases/
│   └── adapters/
├── scripts/
│   └── build_digest.py     # Main script (Phase 7)
├── docs/
│   ├── README.md
│   ├── arquitectura.md
│   ├── configuracion.md
│   ├── guia-uso.md
│   ├── tareas.md
│   └── requisitos-digest-semanal.md
├── pyproject.toml          # Dependencies and project configuration
└── README.md
```

## Prerequisites

- A GitHub repository with the digest code.
- An account with an email provider (e.g. [SendGrid](https://sendgrid.com)) to send the digest.
- An LLM API key (OpenAI, Anthropic or compatible) for summaries and ranking.
- (Optional) Reddit app to use the API (client id + secret).

## Local development (virtual environment)

Use a virtual environment so dependencies stay isolated from the system Python.

**Create and activate the venv:**

```bash
# Create (from repo root)
python -m venv .venv

# Activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate
```

**Install the project in editable mode (with dev tools):**

```bash
pip install -e ".[dev]"
```

Then run scripts from the repo root. The `.venv/` folder is already in [.gitignore](.gitignore), so it is not committed.

**Run tests:**

```bash
pytest
```

Use `pytest -v` for verbose output, or `pytest tests/domain/` / `pytest tests/config/` to run only certain test modules.

## Run the digest locally

Set the required environment variables and run the script from the repo root:

```bash
# Required
export DIGEST_EMAIL_TO="tu@email.com"
export DIGEST_EMAIL_FROM="digest@tudominio.com"
export SENDGRID_API_KEY="SG.xxx..."
export LLM_API_KEY="sk-..."

# Optional (defaults: LLM_PROVIDER=openai, LLM_MODEL=gpt-4o-mini)
export LLM_PROVIDER="openai"        # or "anthropic"
export LLM_MODEL="gpt-4o-mini"      # or "claude-3-haiku-20240307"

python scripts/build_digest.py
```

On Windows PowerShell, use `$env:VAR = "value"` instead of `export`.

The script reads `config/sources.yaml` and `config/links.md`, fetches articles, generates summaries with the LLM, sends the email via SendGrid, and updates `data/sent-urls.json`.

## Next steps

1. Configure [GitHub secrets](docs/configuracion.md#secrets) (email, SendGrid, LLM).
2. Edit [config/sources.yaml](docs/configuracion.md#fuentes) and [config/links.md](docs/configuracion.md#enlaces-manuales).
3. Run the workflow (manually the first time or wait for the weekly schedule).

See [Configuration](docs/configuracion.md) for details.
