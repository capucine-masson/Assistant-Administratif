"""
Abstraction sur le fournisseur LLM utilisé pour :
  - estimer la difficulté / le temps estimé d'une démarche personnalisée
  - générer un guide détaillé (étapes + explications) pour une démarche
  - transformer un message en langage naturel (chatbot) en démarche structurée

Le fournisseur est choisi via LLM_PROVIDER dans .env : "groq" ou "none". Si
l'appel échoue ou si le fournisseur est "none", on retombe sur une
heuristique simple afin que l'application reste utilisable sans clé API.
"""

import datetime
import json
import re

import httpx

from .config import settings

SYSTEM_PROMPT = (
    "Tu es un assistant expert des démarches administratives françaises. "
    "Réponds uniquement en JSON valide, sans texte autour, avec les clés : "
    '"difficulty" (facile|moyen|difficile), "estimated_minutes" (entier), '
    '"guide" (texte des étapes, avec sauts de ligne).'
)

CHATBOT_SYSTEM_PROMPT_TEMPLATE = (
    "Tu es un assistant qui transforme la demande en langage naturel d'un utilisateur "
    "en une démarche administrative structurée. Réponds uniquement en JSON valide, sans "
    'texte autour, avec les clés : "title" (titre court et clair), "category" (choisis '
    "la plus proche parmi cette liste : {categories} — sinon \"Autre\"), "
    '"difficulty" (facile|moyen|difficile), "estimated_minutes" (entier), '
    '"guide" (étapes numérotées séparées par des sauts de ligne), '
    '"deadline" (date au format AAAA-MM-JJ si une échéance est mentionnée ou clairement '
    'déductible, sinon null). Nous sommes le {today}.'
)


def _heuristic_estimate(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()
    hard_keywords = ["préfecture", "titre de séjour", "permis", "parcoursup", "urssaf"]
    easy_keywords = ["mise à jour", "vérifier", "consulter", "signaler"]

    if any(k in text for k in hard_keywords):
        difficulty, minutes = "difficile", 120
    elif any(k in text for k in easy_keywords):
        difficulty, minutes = "facile", 20
    else:
        difficulty, minutes = "moyen", 45

    guide = (
        f"Étapes suggérées pour « {title} » :\n"
        "1. Rassemblez les documents nécessaires (pièce d'identité, justificatif de domicile...).\n"
        "2. Identifiez le site officiel correspondant (service-public.fr en cas de doute).\n"
        "3. Effectuez la démarche en ligne ou prenez rendez-vous si nécessaire.\n"
        "4. Conservez une preuve (accusé de réception, capture d'écran, email de confirmation)."
    )
    return {"difficulty": difficulty, "estimated_minutes": minutes, "guide": guide}


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _call_groq(prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str | None:
    if not settings.GROQ_API_KEY:
        return None
    try:
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as exc:
        print(f"[llm_service] Groq API error: HTTP {exc.response.status_code} — {exc.response.text[:200]}")
        return None
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        print(f"[llm_service] Groq call failed: {exc!r}")
        return None


def estimate_and_generate_guide(title: str, description: str) -> dict:
    prompt = (
        f"Démarche : {title}\n"
        f"Description : {description or 'aucune description fournie'}\n"
        "Donne la difficulté, le temps estimé en minutes et un guide étape par étape."
    )

    raw: str | None = None
    if settings.LLM_PROVIDER == "groq":
        raw = _call_groq(prompt)

    if raw:
        parsed = _extract_json(raw)
        if parsed and "difficulty" in parsed:
            return {
                "difficulty": parsed.get("difficulty", "moyen"),
                "estimated_minutes": int(parsed.get("estimated_minutes", 45) or 45),
                "guide": parsed.get("guide", ""),
            }
        print(f"[llm_service] Could not parse JSON from LLM response, falling back. Raw (200c): {raw[:200]!r}")
    elif settings.LLM_PROVIDER != "none":
        print(f"[llm_service] No response from provider '{settings.LLM_PROVIDER}', falling back to heuristic.")

    return _heuristic_estimate(title, description)


def extract_task_from_message(message: str, category_names: list[str]) -> dict:
    """Utilisé par le chatbot : transforme un message libre en démarche structurée."""
    system_prompt = CHATBOT_SYSTEM_PROMPT_TEMPLATE.format(
        categories=", ".join(category_names) or "Autre",
        today=datetime.date.today().isoformat(),
    )

    raw: str | None = None
    if settings.LLM_PROVIDER == "groq":
        raw = _call_groq(message, system_prompt=system_prompt)

    if raw:
        parsed = _extract_json(raw)
        if parsed and "title" in parsed:
            return {
                "title": (parsed.get("title") or message[:80]).strip(),
                "category": parsed.get("category") or "Autre",
                "difficulty": parsed.get("difficulty", "moyen"),
                "estimated_minutes": int(parsed.get("estimated_minutes", 45) or 45),
                "guide": parsed.get("guide", ""),
                "deadline": parsed.get("deadline"),
            }
        print(f"[llm_service] Could not parse chatbot JSON, falling back. Raw (200c): {raw[:200]!r}")
    elif settings.LLM_PROVIDER != "none":
        print(f"[llm_service] No chatbot response from provider '{settings.LLM_PROVIDER}', falling back.")

    base = _heuristic_estimate(message, "")
    return {
        "title": message.strip()[:80] or "Nouvelle démarche",
        "category": "Autre",
        "difficulty": base["difficulty"],
        "estimated_minutes": base["estimated_minutes"],
        "guide": base["guide"],
        "deadline": None,
    }
