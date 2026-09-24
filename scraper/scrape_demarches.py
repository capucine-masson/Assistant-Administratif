#!/usr/bin/env python3
"""
Script de rafraîchissement des données officielles sur les démarches
administratives.

Ce script NE remplace PAS le catalogue métier (titres, catégories,
conditions d'éligibilité, étapes) : il va simplement visiter les URLs
officielles déjà référencées dans data/demarches_catalog.json (service-
public.fr, ants.gouv.fr, impots.gouv.fr, caf.fr, ameli.fr, etc.), en
extraire le titre de page et la meta-description, et les stocker dans le
champ "scraped_info" de chaque démarche avec un horodatage.

Cela permet de détecter si une page officielle a changé de contenu depuis
le dernier passage (utile car les démarches administratives évoluent).

Utilisation :
    python scrape_demarches.py
    python scrape_demarches.py --catalog ../data/demarches_catalog.json
    python scrape_demarches.py --dry-run

Le script est volontairement simple et ne fait AUCUNE authentification :
il lit des pages publiques uniquement. Respecte un délai entre requêtes
pour ne pas surcharger les sites officiels.
"""

import argparse
import datetime
import hashlib
import json
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "demarches_catalog.json"
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (compatible; AssistantAdministratifBot/1.0; "
    "usage personnel, met a jour un catalogue local de demarches)"
)


def fetch_page_summary(url: str) -> dict:
    """Récupère titre + meta description d'une page publique."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return {"url": url, "error": str(exc), "fetched_at": _now_iso()}

    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_description = None
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_description = meta_tag["content"].strip()

    text_sample = " ".join(soup.get_text(" ", strip=True).split())[:2000]
    content_hash = hashlib.sha256(text_sample.encode("utf-8")).hexdigest()

    return {
        "url": url,
        "title": title,
        "meta_description": meta_description,
        "content_hash": content_hash,
        "fetched_at": _now_iso(),
    }


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def refresh_catalog(catalog_path: Path, dry_run: bool = False) -> None:
    if not catalog_path.exists():
        print(f"[ERREUR] Catalogue introuvable : {catalog_path}", file=sys.stderr)
        sys.exit(1)

    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)

    changes_detected = []

    for entry in catalog.get("demarches", []):
        official_urls = entry.get("official_urls", [])
        if not official_urls:
            continue

        previous_hashes = {
            info["url"]: info.get("content_hash")
            for info in entry.get("scraped_info", [])
        }

        scraped_info = []
        for link in official_urls:
            url = link.get("url")
            if not url:
                continue
            print(f"  → {entry['id']}: {url}")
            summary = fetch_page_summary(url)
            scraped_info.append(summary)

            old_hash = previous_hashes.get(url)
            new_hash = summary.get("content_hash")
            if old_hash and new_hash and old_hash != new_hash:
                changes_detected.append((entry["id"], url))

            time.sleep(REQUEST_DELAY_SECONDS)

        entry["scraped_info"] = scraped_info

    catalog["last_updated"] = _now_iso()

    if dry_run:
        print("\n[--dry-run] Aucune écriture effectuée.")
    else:
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Catalogue mis à jour : {catalog_path}")

    if changes_detected:
        print("\n⚠️  Changements détectés sur les pages officielles suivantes :")
        for demarche_id, url in changes_detected:
            print(f"   - {demarche_id}: {url}")
        print("   Vérifiez si la procédure ou les informations ont changé.")
    else:
        print("\nAucun changement de contenu détecté depuis le dernier passage.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help="Chemin vers demarches_catalog.json (par défaut: data/demarches_catalog.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="N'écrit pas le fichier, affiche seulement ce qui serait fait.",
    )
    args = parser.parse_args()

    print(f"🔄 Rafraîchissement des données officielles depuis : {args.catalog}\n")
    refresh_catalog(args.catalog, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
