# 📋 Assistant de préparation administrative

Application web locale qui centralise mes démarches administratives (impôts, identité,
permis/véhicule, CAF/APL, scolarité, santé, emploi...) : quizz de personnalisation à la
première connexion, vue en colonnes par catégorie ou vue calendrier (mois / 6 mois /
année), filtres par catégorie/personne/statut, guides détaillés générés par IA,
assistant conversationnel pour créer une démarche en une phrase, et un petit système de
points/récompenses.

## Fonctionnalités

- **Connexion factice** : un nom d'utilisateur suffit, pas de mot de passe.
- **Quizz de première connexion** génère automatiquement les démarches pertinentes
  (âge, situation familiale, logement, profession, permis/véhicule...).
- **Vue liste** : démarches en colonnes par catégorie, tâches terminées repliées en bas
  de chaque colonne.
- **Vue calendrier** (FullCalendar) : mois, 6 mois, année ou liste, avec filtres.
- **Catégories et personnes du foyer** : modifiables, pour trier/filtrer les démarches.
- **Assistant IA** (bouton en bas à droite) : décrire une tâche en langage naturel crée
  la démarche correspondante.
- **Fiche démarche** : difficulté, temps estimé, deadline, étapes à cocher, liens
  officiels, guide généré par IA.
- **Récompenses** : points et niveaux selon les démarches complétées.

## Stack technique

- **Backend** : Python / FastAPI + SQLAlchemy + SQLite, rendu serveur Jinja2 (pas de build JS)
- **Frontend** : Tailwind CSS (CDN) + JS vanilla + FullCalendar (CDN)
- **Reverse proxy** : nginx, exposé sur `http://localhost:9090`
- **Conteneurisation** : Docker / docker-compose
- **IA** : Groq (cloud, gratuit) via `.env` — ou aucune IA (repli sur des règles simples)

## Démarrage rapide

```bash
cp .env.example .env
# éditez .env : SECRET_KEY, et éventuellement une clé Groq (voir ci-dessous)

docker compose up -d --build
```

Ouvrez **http://localhost:9090**. Après une modification des templates/static/code
Python, il faut rebuilder l'image backend :

```bash
docker compose build backend && docker compose up -d backend
```

Pour arrêter : `docker compose down` (les données restent dans `./data/app.db`).

## Clé API Groq (optionnelle)

Sans clé (`LLM_PROVIDER=none` dans `.env`), l'appli reste pleinement fonctionnelle avec
une estimation par règles simples pour la difficulté/le temps/le guide.

Avec une clé (gratuite) : créer un compte sur https://console.groq.com/ → **API Keys**
→ **Create API Key**, puis dans `.env` :
```
LLM_PROVIDER=groq
GROQ_API_KEY=la_clé_copiée
GROQ_MODEL=openai/gpt-oss-20b
```
Si `GROQ_MODEL` n'existe plus (erreur `model_not_found` dans `docker compose logs backend`),
lister les modèles disponibles :
```bash
curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer VOTRE_CLE" | grep '"id"'
```

## Rafraîchir le catalogue de démarches (scraper)

`data/demarches_catalog.json` référence des pages officielles (service-public.fr,
ants.gouv.fr, caf.fr, impots.gouv.fr, ameli.fr...). Le scraper revisite ces pages et
signale celles dont le contenu a changé (procédure potentiellement mise à jour) :

```bash
docker compose --profile tools run --rm scraper
```

Il ne modifie jamais le contenu métier du catalogue (titres, catégories, étapes,
guides) — uniquement les infos de veille (`scraped_info`).

## Structure du projet

```
.
├── docker-compose.yml
├── .env.example / .env (secrets, non commité)
├── data/demarches_catalog.json   # catalogue des démarches officielles
├── nginx/templates/              # config nginx (reverse proxy → backend:8000)
├── backend/app/
│   ├── main.py                   # point d'entrée FastAPI
│   ├── models.py                 # User, Person, Category, Demarche, Badge
│   ├── catalog.py                # matching profil quizz ↔ catalogue
│   ├── rewards.py                # points & badges
│   ├── llm_service.py            # appel Groq + repli heuristique
│   ├── routers/                  # auth, quiz, demarches, categories, people, rewards, calendar_api, chatbot
│   ├── templates/                # pages Jinja2
│   └── static/                   # css/js
└── scraper/
    ├── scrape_demarches.py
    └── Dockerfile
```

## Notes importantes

- **Authentification factice** : aucune vérification de mot de passe, ne pas exposer
  tel quel sur internet.
- **Secrets** : tout est dans `.env` (jamais commité). Ne jamais mettre de vraie clé
  dans `.env.example`.
- Les données sont en SQLite dans `./data/app.db` (volume Docker persistant entre
  rebuilds).
