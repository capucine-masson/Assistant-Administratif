# Assistant Administratif

Décris ta situation, l'app s'occupe du reste : elle génère tes démarches administratives, te dit quoi faire et quand, et te guide étape par étape jusqu'au bout.

## Fonctionnalités

- **Un quizz, tes démarches prêtes** — réponds à quelques questions (âge, logement, famille, profession...), l'app génère automatiquement les démarches qui te concernent
- **Jamais perdu dans les papiers** — vue en colonnes par catégorie ou vue calendrier (mois, 6 mois, année), avec filtres par catégorie, personne ou statut
- **Le bon guide, sans y penser** — chaque démarche a ses étapes, ses liens officiels et un guide détaillé généré par IA
- **Dis-le en une phrase** — un assistant conversationnel crée la démarche correspondante à partir d'une simple description
- **Un peu de motivation** — points et niveaux au fil des démarches complétées
- **Ton espace, rien qu'à toi** — un identifiant = un espace privé, aucune donnée partagée entre utilisateurs

## Lancer le projet

```bash
cp .env.example .env
# éditer .env : SECRET_KEY, et éventuellement une clé Groq (voir plus bas)

docker compose up -d --build
```

Ouvrir `http://localhost:9090`, se connecter avec l'identifiant de son choix (aucun mot de passe : la connexion sert uniquement à séparer les espaces de chacun).

Après une modification du code : `docker compose build backend && docker compose up -d backend`.
Pour arrêter : `docker compose down` (les données restent dans `./data/app.db`).

### Clé API Groq (optionnelle)

Sans clé, l'appli reste fonctionnelle avec une estimation par règles simples. Avec une clé gratuite (console.groq.com → API Keys) :

```
LLM_PROVIDER=groq
GROQ_API_KEY=ta_cle
GROQ_MODEL=openai/gpt-oss-20b
```

## Choix techniques

- **Backend** : FastAPI + SQLAlchemy + SQLite, rendu serveur Jinja2 (pas de build JS)
- **Frontend** : Tailwind CSS (CDN) + JS vanilla + FullCalendar (CDN)
- **Reverse proxy** : nginx (`http://localhost:9090`)
- **Conteneurisation** : Docker / docker-compose
- **IA (Groq)** : `openai/gpt-oss-20b` pour le guide de démarche et l'assistant conversationnel, avec repli heuristique si aucune clé n'est fournie
- **Auth** : session signée, pas de vrai mot de passe — volontairement factice
- **Multi-utilisateur** : chaque identifiant a son propre foyer (personnes, démarches, catégories)

## Architecture

```
backend/app/
├── main.py            point d'entrée FastAPI
├── models.py          User, Person, Category, Demarche, Badge
├── catalog.py         matching profil quizz ↔ catalogue de démarches
├── rewards.py         points & badges
├── llm_service.py     appel Groq + repli heuristique
├── routers/           auth, quiz, demarches, categories, people, rewards, calendar_api, chatbot
├── templates/         pages Jinja2
└── static/            css/js
data/demarches_catalog.json   catalogue des démarches officielles
scraper/                       revisite les pages officielles pour détecter les mises à jour
```

Chaque démarche appartient à un utilisateur. Toutes les requêtes sont filtrées par cet utilisateur, y compris l'accès direct à une démarche par son URL.
