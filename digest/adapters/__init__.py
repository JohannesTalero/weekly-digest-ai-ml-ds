"""Capa adapters: fuentes (RSS, HN, Reddit, manual), LLM y email."""

from digest.adapters.fetch_all import fetch_all_items
from digest.adapters.input_hacker_news import fetch_hacker_news_items
from digest.adapters.input_manual import fetch_manual_items
from digest.adapters.input_reddit import fetch_reddit_items
from digest.adapters.input_rss import fetch_rss_items

__all__ = [
    "fetch_all_items",
    "fetch_hacker_news_items",
    "fetch_manual_items",
    "fetch_reddit_items",
    "fetch_rss_items",
]
