# Forces et faiblesses

État au 19 novembre 2026. Source : 806 parties standard du 2 août au 18 novembre 2026, plus un échantillon de 100 parties passé à Stockfish 16, profondeur 12. Le détail est dans [le bilan](../analyses/2026-11-19-bilan-initial.md).

À remplacer lors du prochain bilan, en gardant la date de ce constat.

## Forces

- **Le système blanc est déjà là.** 402 parties sur 403 avec les Blancs commencent par `1.d4`. Le schéma fou f4, cavalier f3, puis e3 et c3, revient tout le temps. Score avec les Blancs : 52 %. Plusieurs lignes habituelles (`...d5`, fou f4, cavalier f3) sont entre 60 et 75 % sur 12 à 22 parties. Des parties de cette structure passent l'échantillon sans gaffe de 3 points, avec un ACPL plafonné entre 14 et 23.
- **La conversion suit, une fois la pièce gardée.** Quand Zoliandru est le premier à conserver au moins une pièce d'avance après la réponse adverse : 262 parties, score 84 %. Pour un avantage d'au moins 5 points (tour, ou mieux) : 205 parties, score 91 %.
- **Le temps est un outil, pas le trou.** 81 gains au temps, 8 pertes au temps. 17 parties seulement descendent sous 10 secondes, et aucune perte au temps avec encore une pièce d'avance à la fin. Les coups 1 à 8 sont joués en une seconde environ : l'habitude bullet est là, et ces coups rapides ne sont presque pas les gaffes (1 gaffe sur 593 coups d'ouverture joués en moins de 2 secondes dans l'échantillon).
- **Le roque se fait.** Dans les parties d'au moins 15 coups complets, le roque a lieu dans 87 % des cas, vers le coup 10.
- **Les puzzles sont au-dessus des parties.** Fourchette publique 1489-1659, pour un blitz autour de 1030. Le calcul existe à côté de la partie. Le transfert vers le blitz est le sujet.

## Faiblesses

- **La pièce tombe au milieu, avec du temps.** 476 coups perdent au moins 2 points de matériel net (cavalier contre pion, ou pire) : 0,59 par partie, dans 42 % des parties. 304 de ces coups perdent au moins une pièce entière (0,38 par partie). 76 % arrivent au milieu de jeu, 18 % dans l'ouverture, 6 % en finale. 463 sur 476 arrivent avec encore 20 secondes ou plus. Dans l'échantillon, ces coups coûtent en moyenne 293 centipions plafonnés, contre 78 pour les autres.
- **C'est toi qui la donnes le plus souvent, et tu la récupères rarement.** L'adversaire est le premier à garder une pièce : 397 parties, ton score ensuite 24 %. Toi d'abord : 262 parties, score 84 %. Médiane : coup 20. Dans les défaites, 54 % des parties contiennent au moins une perte nette ≥ 2, contre 30 % des victoires.
- **Les Noirs contre `1.e4`.** 246 parties en `1...e5`, score 46 %. La ligne `1.e4 e5 2.Nf3 Nc6 3.d4 exd4` : 37 parties, score 34 %. L'italienne `3.Bc4 Nf6` : 87 parties, score 46 %, et 0,21 perte nette de matériel dans les dix premiers coups, par partie — le plus haut taux des lignes courantes. Contre `1.d4`, `1...Nf6` (souvent `...g6`) : 110 parties, score 53 %.
- **Le roi entre dans le mat alors que la position est tenable.** L'échantillon compte 31 erreurs où le coup autorise un mat, souvent avec encore une ou deux minutes. Ce n'est pas le gros des effectifs (la pièce l'est), mais ce sont des parties perdues d'un coup.
- **La glissade de septembre montre le volume sans revue.** D'environ 1130 fin août à environ 930 fin septembre, en continuant à jouer beaucoup. Le rebond de novembre (43 parties, 63 %) est trop court pour le prendre comme acquis.

## Ce qui n'est pas le sujet, pour l'instant

- Le zeitnot. Il est rare, et mauvais quand il arrive (score 21 % sous 10 secondes). Ce n'est pas là que part le classement.
- Apprendre une nouvelle ouverture blanche.
- Un cycle de finales. Une fois la pièce d'avance confirmée, le score est déjà de 84 %. La finale arrive peu dans les pertes de matériel (27 coups sur 476).
- Le bullet. Historique massif, pratique actuelle marginale, et il entretient le coup d'ouverture en une seconde.
