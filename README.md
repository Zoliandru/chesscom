# Entraînement échecs — Zoliandru

Espace de travail pour analyser les parties publiques Chess.com de **Zoliandru** et en tirer un plan d'entraînement. Lecture seule : aucun mot de passe, aucun cookie, aucune action sur le compte.

## Par où commencer

1. [AGENTS.md](AGENTS.md) — rôle de l'agent, règles, méthode.
2. [context/profile.md](context/profile.md) — qui joue, à quelle cadence, avec quels objectifs proposés.
3. [context/strengths-weaknesses.md](context/strengths-weaknesses.md) — ce que les parties montrent aujourd'hui.
4. [analyses/2026-11-19-bilan-initial.md](analyses/2026-11-19-bilan-initial.md) — premier bilan, 2 août – 18 novembre 2026.
5. [plans/2026-11-19-plan-2-semaines.md](plans/2026-11-19-plan-2-semaines.md) — plan courant, du 20 novembre au 3 décembre 2026.

## Données

Les PGN blitz et rapides standard d'août à novembre 2026 sont dans [`games/pgn/`](games/pgn/). L'index et l'instantané public (profil, classements, recensement des archives) sont dans [`games/`](games/).

Rafraîchir, sans identifiant :

```bash
python3 scripts/fetch_pubapi.py --username zoliandru --pgn-months 2026/08 2026/09 2026/10 2026/11
python3 scripts/analyze_games.py --sample 100 --depth 12
```

Stockfish doit être disponible (`/usr/games/stockfish` ou la variable `STOCKFISH`). Dépendance Python : `requirements.txt` (`chess`).

Les dates du bilan sont en heure de Bruxelles.
