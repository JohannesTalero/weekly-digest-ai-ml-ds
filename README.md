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

## Next steps

1. Configure [GitHub secrets](docs/configuracion.md#secrets) (email, send API, LLM API).
2. Edit [config/sources.yaml](docs/configuracion.md#fuentes) and [config/links.md](docs/configuracion.md#enlaces-manuales).
3. Run the workflow (manually the first time or wait for the weekly schedule).

See [Configuration](docs/configuracion.md) for details.
