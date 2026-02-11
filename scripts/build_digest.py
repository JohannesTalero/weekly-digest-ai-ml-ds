#!/usr/bin/env python3
"""
Script principal del digest: fetch → dedup → filter → resumen → ranking → email → persistir historial.

Credenciales y email desde variables de entorno (RF-17). Ejecutar desde la raíz del repo
o definir REPO_ROOT.
"""

import logging
import os
import sys
from pathlib import Path

# Asegurar que el paquete digest está en el path (cuando se ejecuta como script)
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from digest.adapters.email_sendgrid import SendGridEmail, build_and_send_digest
from digest.adapters.llm_openai import OpenAILLM
from digest.config.history import load_sent_urls, save_sent_urls
from digest.config.sources import load_sources
from digest.domain.urls import normalize_url
from digest.use_cases.build_digest import build_digest

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Rutas por defecto respecto al repo
REPO_ROOT = Path(os.environ.get("REPO_ROOT", _repo_root))
SOURCES_PATH = REPO_ROOT / "config" / "sources.yaml"
LINKS_PATH = REPO_ROOT / "config" / "links.md"
HISTORY_PATH = REPO_ROOT / "data" / "sent-urls.json"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value or not value.strip():
        logger.error("Falta la variable de entorno: %s", name)
        sys.exit(1)
    return value.strip()


def main() -> None:
    to_email = _require_env("DIGEST_EMAIL_TO")
    _require_env("SENDGRID_API_KEY")
    _require_env("DIGEST_EMAIL_FROM")
    _require_env("LLM_API_KEY")

    sources_config = load_sources(SOURCES_PATH)
    llm = OpenAILLM()
    email = SendGridEmail()

    top_items = build_digest(
        sources_config,
        LINKS_PATH,
        HISTORY_PATH,
        llm,
        prefilter_limit=30,
        top_n=5,
    )

    if not top_items:
        logger.info("No hay candidatos para el digest; no se envía email.")
        return

    build_and_send_digest(email, top_items, to=to_email)
    logger.info("Email enviado a %s con %d ítems.", to_email, len(top_items))

    # Persistir URLs enviadas (RF-03b, Flujo paso 10)
    sent_urls = load_sent_urls(HISTORY_PATH)
    for x in top_items:
        sent_urls.add(normalize_url(x.item.url))
    save_sent_urls(HISTORY_PATH, sent_urls)
    logger.info("Historial actualizado en %s", HISTORY_PATH)


if __name__ == "__main__":
    main()
