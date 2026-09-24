Je veux coder une interface qui me permet de faciliter mes démarches administratives. Ce sera un Assistant de préparation administrative

Tu es un développeur full stack et PO en même temps.

Développe moi cette interface selon ces contraintes :

# contraintes métier
- Page de connexion (factice pour le moment)
- Si c est la premiere connexion il y a un quizz pour situer un peu le client (age, sexe, profession, pays etc etc pour savoir quelles autres questions poser et quelles demarches sont à faire)
- Page d'accueil où sont visibles les démarches en cours --> deux visions possibles : vision calendrier ou vision liste (l utilisateur choisit)
- Un calendrier qui récapitule toutes les deadlines à respecter, ce que soit scolaire, administratif permis/voiture, impots, passeport, APL/CAF, etc.
- Possibilité (un bouton) d'ajouter une nouvelle démarche si c est nous qui l entreprenons
- les demarches doivent etre triées par catégories (modifiables pas l utilisateur s'il veut)
- possibilité de filtrer selon la catégorie, la personne de la demarche (exemple si on est parent et qu on doit faire une demarche pour un de ses enfants)
- possibilité d ajouter une note/difficulté/temps estimé (trouvé par l ia) pour chaque tache
- Pour chaque tache, quand on clique dessus il faut y voir l avancée et la possibilité de voir une explication détaillée de comment faire avec les bons urls
- statut pour chaque tache si elle est a faire, commencée, terminée
- systeme de récompenses quand on fait bein et vite ses démarches

# contraintes techniques
- mets tous les secrets dans un fichier .env et créer un .gitignore où sera écrit ce .env
- aucun secrets en dur, tout dans le .env
- utilise nginx, python, docker
- docker : je veux un conteneur pour cette webapp à lancer en local sur le port 9090
- tu auras besoin d'une clé API d'un LLM pour pouvoir faire ce projet. Explique moi exactement comment m'en procurer une. Je veux que ce soit gratuit, ou alors cherche moi une alternative sur hugging face pour faire tourner un mini modele sur mon PC (qui fera l affaire)
- tu vas checker des la creation de la web app toutes les demarches obligatoires et tout ce qu'il y a à savoir sur chacune d'elle mais il peut y avoir des changements donc je veux un script qui rescrappe toutes les données officielles que je peux lancer à tout moment qui permet de recup les infos mises à jour.
