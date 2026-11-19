# Parties

Exports **publics** Chess.com, en lecture seule. Les PGN contiennent les pseudos des deux joueurs, les coups, les pendules et le lien de la partie. Rien d'autre : pas de jeton, pas de cookie, pas de mot de passe.

| Fichier | Contenu |
| --- | --- |
| `pgn/2026-08.pgn` … `2026-11.pgn` | Échecs standard, blitz et rapide, avec trois en-têtes ajoutés : `TimeClass`, `Rated`, `Rules` |
| `index.jsonl` | Une ligne par partie de ces PGN (lien, cadence, résultat, ECO) |
| `manifest.json` | Ce qui a été écrit, et quand |
| `source/profile.json` | Profil public au moment du téléchargement |
| `source/stats.json` | Classements publics |
| `source/archive-census.json` | Nombre de parties par mois et par cadence, sans garder les PGN anciens |

Le bullet, le quotidien et les parties « odds » ne sont pas dans les PGN. Leur volume est dans le recensement, pour savoir ce qui est vraiment joué en ce moment.

Pour mettre à jour : `python3 scripts/fetch_pubapi.py`.
