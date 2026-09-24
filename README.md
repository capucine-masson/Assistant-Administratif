# 📋 Assistant de préparation administrative

Application web locale qui centralise vos démarches administratives
(impôts, identité, permis/véhicule, CAF/APL, scolarité, santé, emploi...),
avec quizz de personnalisation, vue liste/calendrier, catégories et
personnes filtrables, guides détaillés générés par IA, et un petit
système de récompenses.

## Stack technique

- **Backend** : Python / FastAPI + SQLAlchemy + SQLite, rendu serveur avec Jinja2 (pas de build JS)
- **Frontend** : Tailwind CSS (CDN) + JS vanilla + FullCalendar (CDN) pour la vue calendrier
- **Reverse proxy** : nginx, exposé sur `http://localhost:9090`
- **Conteneurisation** : Docker / docker-compose
- **IA** : Groq (gratuit, cloud) via `.env` — ou aucune IA (repli sur des règles simples)

## Démarrage rapide

```bash
cp .env.example .env
# éditez .env : générez un SECRET_KEY, et configurez éventuellement un fournisseur LLM (voir plus bas)

docker compose up -d --build
```

Ouvrez ensuite **http://localhost:9090**.

La "connexion" est **factice** : entrez n'importe quel nom d'utilisateur, aucun mot de passe
n'est demandé. À la première connexion, un quizz rapide (âge, situation familiale,
logement, profession, permis/véhicule...) permet de générer automatiquement les
démarches qui vous concernent.

Pour arrêter : `docker compose down` (les données restent dans `./data/app.db`).

## Obtenir une clé API LLM gratuite (Groq)

L'IA sert à estimer la difficulté/le temps d'une démarche que vous ajoutez vous-même,
et à générer un guide d'étapes. **Ce n'est pas obligatoire** : sans clé (`LLM_PROVIDER=none`),
l'appli utilise une estimation par règles simples et reste pleinement fonctionnelle.

1. Allez sur https://console.groq.com/ et créez un compte gratuit (email ou Google/GitHub).
2. Dans le menu de gauche, allez dans **API Keys**.
3. Cliquez sur **Create API Key**, donnez-lui un nom, copiez la clé (elle ne sera plus affichée après).
4. Dans votre `.env` :
   ```
   LLM_PROVIDER=groq
   GROQ_API_KEY=la_clé_copiée
   GROQ_MODEL=openai/gpt-oss-20b
   ```
5. Redémarrez : `docker compose up -d --build backend`.

Le tier gratuit de Groq est largement suffisant pour cet usage (quelques appels par
démarche ajoutée). ⚠️ Les modèles disponibles chez Groq changent régulièrement
(certains sont retirés). Si vous voyez une erreur `model_not_found` dans les logs
(`docker compose logs backend`), listez les modèles actuellement disponibles avec
votre clé :

```bash
curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer VOTRE_CLE" | grep '"id"'
```
et mettez à jour `GROQ_MODEL` en conséquence.

## Rafraîchir les données officielles (scraper)

Les démarches du catalogue (`data/demarches_catalog.json`) référencent des pages
officielles (service-public.fr, ants.gouv.fr, caf.fr, impots.gouv.fr, ameli.fr...).
Comme ces démarches évoluent, un script dédié permet de revisiter ces pages à tout
moment et de détecter si leur contenu a changé :

```bash
docker compose --profile tools run --rm scraper
```

Le script :
- visite chaque URL officielle référencée,
- enregistre titre / meta-description / empreinte du contenu dans `scraped_info`,
- compare avec le passage précédent et **signale les pages dont le contenu a changé**
  (signe qu'une procédure a peut-être évolué et qu'il faut vérifier/mettre à jour le
  catalogue manuellement).

Vous pouvez aussi le lancer en local (hors Docker) si vous avez Python :
```bash
cd scraper
pip install -r requirements.txt
python scrape_demarches.py --dry-run   # pour un aperçu sans écrire le fichier
```

Le catalogue métier (titres, catégories, conditions d'éligibilité, étapes, guide)
reste éditable à la main dans `data/demarches_catalog.json` — le scraper ne fait
qu'ajouter les infos de veille, il ne réécrit jamais ces champs.

## Structure du projet

```
.
├── docker-compose.yml
├── .env.example / .env (secrets, non commité)
├── data/demarches_catalog.json   # catalogue des démarches officielles
├── nginx/templates/              # config nginx (reverse proxy → backend:8000)
├── backend/
│   └── app/
│       ├── main.py               # point d'entrée FastAPI
│       ├── models.py             # User, Person, Category, Demarche, Badge
│       ├── catalog.py            # matching profil quizz ↔ catalogue
│       ├── rewards.py            # points & badges
│       ├── llm_service.py        # appel Groq + repli heuristique
│       ├── routers/              # routes (auth, quiz, demarches, categories, people, rewards, calendar_api)
│       ├── templates/            # pages Jinja2
│       └── static/               # css/js
└── scraper/
    ├── scrape_demarches.py
    └── Dockerfile
```

## Notes importantes

- **Authentification factice** : aucune vérification de mot de passe, ne pas exposer
  tel quel sur internet.
- **Secrets** : tout est dans `.env` (jamais commité, voir `.gitignore`). Ne mettez
  jamais de vraie clé dans `.env.example`.
- Les données sont stockées en SQLite dans `./data/app.db`, dans le même volume Docker
  que le catalogue (`./data`), donc persistant entre redémarrages et rebuilds de l'image.
