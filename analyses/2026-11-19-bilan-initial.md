# Bilan du 19 novembre 2026

Fenêtre : parties publiques de Zoliandru du **2 août au 18 novembre 2026** (heure de Bruxelles). Échecs standard uniquement.

## En bref

Tu joues du blitz **3+2**, autour de **1030**. Ton score est celui que les classements prédisent. Le blitz d'août, vers 1100-1130, est redescendu jusqu'aux 930 en septembre-octobre. Novembre remonte, sur peu de parties.

Les parties se décident par une **pièce qui tombe au milieu de jeu**, le plus souvent avec encore une ou deux minutes au pendule. Quand cette pièce reste à toi, tu gagnes la partie (84 %). Quand elle reste à l'adversaire, tu reviens peu (24 %). Les puzzles, entre 1490 et 1660, sont au-dessus du blitz : le calcul est là, il ne passe pas dans la partie.

Le système blanc `1.d4`, fou f4, cavalier f3 est à garder. Le point d'ouverture est noir, contre `1.e4`, en particulier l'écossaise.

## Périmètre et méthode

| | |
| --- | --- |
| Corpus | 806 parties, dont 805 classées. 805 blitz `180+2`, une partie de 30 minutes |
| Moteur | 100 de ces parties de blitz, au moins 8 coups, 49 défaites, 48 victoires, 3 nulles. Stockfish 16, profondeur 12. 3 322 coups de Zoliandru |
| Répartition de l'échantillon | Août 39, septembre 31, octobre 25, novembre 5. Blancs 56, Noirs 44 |
| Chiffres bruts | `analyses/2026-11-19-stats.json` |

Une **perte nette** est une capture adverse, après ta meilleure reprise, qui laisse moins de matériel qu'avant ton coup. 2 points : un cavalier ou un fou contre un pion. 3 points : une pièce entière. 5 : une tour. 9 : une dame. Un échange repris tout de suite compte pour zéro. L'avantage « confirmé » est celui qui existe encore après la réponse adverse.

Gaffe moteur : au moins 300 centipions. L'ACPL plafonne chaque coup à 15 points, pour qu'un mat ne fausse pas la moyenne. À profondeur 12, un écart de 30 centipions ne veut rien dire. On s'appuie sur les gros écarts et sur les effectifs.

Notation des coups : celle des PGN (N cavalier, B fou, R tour, Q dame, K roi).

## Résultats

389 victoires, 390 défaites, 27 nulles. Score 49,9 %, attendu 50,0 %. Adversaires au même classement (1018 de moyenne des deux côtés).

| Couleur | Parties | Score |
| --- | ---: | ---: |
| Blancs | 403 | 52 % |
| Noirs | 403 | 48 % |

Longueur médiane : 63 demi-coups, pareille en victoire et en défaite. 13 parties font moins de 8 coups, dont 3 défaites. Les parties ne se perdent pas au quatrième coup en masse. Elles se perdent ensuite.

Façon de finir :

| | Gain | Perte |
| --- | ---: | ---: |
| Abandon de l'adversaire / le tien | 178 | 309 |
| Mat | 103 | 73 |
| Temps | 81 | 8 |
| Déconnexion adverse | 27 | — |

Tu fais mat, et tu gagnes souvent au drapeau. Tu perds en abandonnant, après que la position a tourné. Huit pertes au temps, et aucune avec encore 3 points de matériel à la fin.

## Classement sur la période

Début de fenêtre : 1039. Fin : 1034. Maximum touché : 1150. Minimum : 883. Record personnel de blitz, plus ancien : 1167 le 8 août 2025.

Août finit à 1134 (316 parties, 52 %). Septembre finit à 980 (251 parties, 46 %). Octobre finit à 943. Du 9 au 15 novembre, 21 parties marquent 76 % et le classement finit à 1051. Du 16 au 18 novembre, 12 parties marquent 42 % et le classement finit à 1034. Le rebond est réel et encore court.

Rythme : environ sept parties par jour sur 109 jours. La baisse de septembre n'est pas un mois sans jouer. La semaine du 31 août compte 102 parties et finit à 992.

## Ouvertures

### Blancs

`1.d4` dans 402 parties sur 403. Score 52 %. Le coup suivant habituel est `Bf4` ou `Nf3`, puis l'autre. C'est ta London, que Chess.com découpe en « Queen's Pawn » et « London System ».

Lignes d'au moins 12 parties, score :

| Ligne | Parties | Score |
| --- | ---: | ---: |
| `1.d4 d5 2.Bf4 Bf5 3.Nf3 e6` | 13 | 73 % |
| `1.d4 c6 2.Bf4 d5 3.Nf3 Bf5` | 12 | 75 % |
| `1.d4 d5 2.Bf4 Nf6 3.Nf3 e6` | 13 | 69 % |
| `1.d4 d5 2.Bf4 Nc6 3.Nf3 Nf6` | 19 | 61 % |
| `1.d4 e5 2.dxe5 Nc6 3.Nf3 Qe7` | 22 | 57 % |
| `1.d4 d5 2.Bf4 Nf6 3.Nf3 Nc6` | 19 | 34 % |

Tu prends le gambit Englund (`1...e5`) et tu t'en sors. La seule ligne blanche courante nettement en dessous est `...Nc6` après `Nf6`. Dix-neuf parties : assez pour la surveiller, pas assez pour changer de système. Les pertes de matériel dans les dix premiers coups y sont rares (moins de 0,10 par partie sur presque toutes ces lignes).

### Noirs

| Réponse | Parties | Score |
| --- | ---: | ---: |
| Contre `1.e4` : `1...e5` | 246 | 46 % |
| Contre `1.d4` : `1...Nf6` | 110 | 53 % |

`1...e5` est presque ta seule réponse à `1.e4`. `1...Nf6`, souvent suivi de `...g6`, est ta réponse à `1.d4`, et elle marque.

| Ligne | Parties | Score | Pertes nettes ≥ 2 dans les 10 premiers coups, par partie |
| --- | ---: | ---: | ---: |
| `1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6` | 87 | 46 % | 0,21 |
| `1.e4 e5 2.Nf3 Nc6 3.d4 exd4` | 37 | 34 % | 0,16 |
| `1.e4 e5 2.Nf3 Nc6 3.Bb5 Nf6` | 26 | 46 % | 0,08 |
| `1.d4 Nf6 2.c4 g6 3.Nc3 Bg7` | 23 | 39 % | 0,00 |
| `1.d4 Nf6 2.Bf4 g6 3.e3 Bg7` | 18 | 50 % | 0,00 |

L'italienne est la ligne la plus jouée, un peu en dessous de ton score noir, et c'est là que les pièces tombent le plus tôt. L'écossaise est le vrai trou de résultat : une partie sur trois. Le fianchetto contre `1.d4` se tient, sauf la petite série `2.c4` (23 parties, 39 %), sans perte de matériel précoce : ce n'est pas le même problème.

## La pièce

Sur les 806 parties, coups qui **créent** une perte nette :

| Perte | Coups |
| --- | ---: |
| 2 points (pièce contre pion, ou équivalent) | 172 |
| 3 ou 4 | 179 |
| 5 à 8 | 96 |
| 9 ou plus | 29 |

0,59 perte ≥ 2 par partie. 0,38 perte ≥ 3 par partie. Au moins une perte ≥ 2 dans 340 parties (42 %).

| | Par partie, perte ≥ 2 | Par partie, perte ≥ 3 | Parties avec au moins une perte ≥ 2 |
| --- | ---: | ---: | ---: |
| Victoires | 0,40 | 0,22 | 30 % |
| Défaites | 0,78 | 0,53 | 54 % |

Où, et avec combien de temps :

| | Coups | Part |
| --- | ---: | ---: |
| Milieu de jeu | 364 | 76 % |
| Ouverture (jusqu'au coup 12) | 85 | 18 % |
| Finale | 27 | 6 % |
| Encore 20 secondes ou plus | 463 | 97 % |
| Moins de 20 secondes | 13 | 3 % |

Médiane du premier de ces coups : le coup 21.

Le moteur confirme le détecteur. Sur l'échantillon, 64 coups sont des pertes nettes ≥ 2. Leur coût moyen plafonné est de **293 centipions**, contre **78** sur les autres coups.

Qui garde la pièce après la réponse adverse :

| Premier à garder ≥ 3 points | Parties | Ton score ensuite | Coup médian |
| --- | ---: | ---: | ---: |
| Toi | 262 | 84 % | 20 |
| L'adversaire | 397 | 24 % | 20 |
| Personne | 147 | 60 % | — |

Pour un avantage d'au moins 5 points : toi 205 parties et 91 % ; l'adversaire 267 parties et tu marques 12 %.

Lecture : tu sais finir quand la pièce est à toi. Tu la donnes plus souvent que tu ne la prends, autour du coup 20, et la partie ne revient presque pas. Trente-neuf défaites existent malgré tout après que tu as eu la pièce le premier : ce n'est pas zéro, ce n'est pas le gros du trou.

## Ce que voit le moteur

ACPL plafonné : moyenne 78, médiane 71. Gaffes (≥ 300 cp) : 1,78 par partie. Erreurs (≥ 150 cp) : 3,97 par partie.

| Résultat | Parties | ACPL | Gaffes par partie | Coup médian de la première gaffe (position pas déjà perdue) |
| --- | ---: | ---: | ---: | ---: |
| Victoire | 48 | 64 | 1,19 | 19 |
| Défaite | 49 | 94 | 2,31 | 13 |
| Nulle | 3 | 57 | 2,67 | 26 |

Part des coups qui sont des gaffes :

| Phase | Coups | Gaffes | Taux |
| --- | ---: | ---: | ---: |
| Ouverture | 1 188 | 26 | 2,2 % |
| Milieu | 1 822 | 123 | 6,8 % |
| Finale | 275 | 29 | 10,5 % |

La finale a le taux le plus haut et le plus petit effectif. Le milieu fournit les gaffes. En position égale (évaluation entre -1,5 et +1,5) : 62 gaffes sur 1 597 coups, soit 3,9 %. En position déjà gagnante au moteur (≥ +4) : 46 gaffes sur 504 coups, soit 9,1 %. Tu lâches aussi des coups quand tu es mieux. Comme le score à 84 % une fois la pièce confirmée le montre, ces coups ne suffisent en général pas à rendre la pièce.

Temps dans l'échantillon : 25 coups commencent avec moins de 20 secondes, dont 6 gaffes. Les 3 260 autres coups contiennent 172 gaffes. Le taux en zeitnot est plus haut, le volume est minuscule.

Coups d'ouverture 1 à 8 joués en moins de 2 secondes : 593, dont **une** gaffe. Les autres coups d'ouverture : 207, dont 7 gaffes. Jouer vite un coup déjà connu ne casse pas la partie. Le coup lent de quelques secondes, qui sort du schéma, casse davantage — et il reste presque tout le temps au pendule (médiane de 1,1 seconde sur les coups 1 à 8 de tout le corpus, 4,9 secondes sur les coups 15 à 30).

Les erreurs d'au moins 150 centipions de l'échantillon se répartissent ainsi. Le mot « positionnel » ici veut dire : le moteur perd au moins 1,5 point et le détecteur de capture en un coup n'a rien vu. Une partie de ces coups sont des tactiques en deux ou trois coups.

| Motif | Erreurs ≥ 150 cp |
| --- | ---: |
| Résidu « positionnel » | 151 |
| Tactique (le meilleur coup prend ou donne échec) | 87 |
| Ouverture | 69 |
| Mat autorisé | 31 |
| Finale | 27 |
| Perte nette d'une pièce (3-4) | 11 |
| Perte nette de 2 | 11 |
| Mat manqué | 3 |
| Perte d'une tour ou plus, vue par le détecteur | 3 |
| Perte de la dame, vue par le détecteur | 1 |
| Zeitnot | 3 |

Le détecteur de matériel et le moteur ne comptent pas la même chose : beaucoup de pièces perdues en deux coups sont dans « tactique », « ouverture » ou « mat », pas dans la ligne « perte nette ».

Roque : 87 % des parties d'au moins 30 demi-coups, vers le coup 10. Au coup 15, le roi est encore au centre sans avoir roqué dans 189 parties sur 738 (26 %). C'est à surveiller, ce n'est pas l'effectif principal. La dame sort avant le coup 8 dans 20 % des parties seulement.

## Quatre parties

Les évaluations ci-dessous ont été recalculées à profondeur 12 sur la position du coup.

### Le cavalier reste en prise — 2 octobre 2026

[Partie](https://www.chess.com/game/live/184708241836), Noirs, défaite, classements 972 contre 993. Écossaise : `1.e4 e5 2.Nf3 Nc6 3.d4 Nf6 4.dxe5`.

Le pion blanc est en e5, ton cavalier est en f6. Tu joues `4...Ne7` (le cavalier de c6). Il reste **185 secondes** après le coup. Stockfish joue `4...Ng4`, qui sort le cavalier de la prise. Le coup joué passe d'une évaluation de -1,1 à -6,4, soit **524 centipions**. Suit `5.exf6`, et après `5...gxf6` il manque toujours une pièce. C'est le modèle de l'écossaise à 34 % sur 37 parties : pas une théorie longue, un cavalier laissé devant un pion.

### La dame reste devant le cavalier — 17 novembre 2026

[Partie](https://www.chess.com/game/live/187435360110), Noirs, défaite, 1060 contre 1062. `1.d3 e5 2.e4 Nc6 3.f4 Nf6`.

Au coup 10, le cavalier blanc est en d5, ta dame en e7. Tu joues `10...O-O-O`. Il reste **173 secondes**. Stockfish joue `10...Nxd5`. Le coup joué passe de +1,1 à -7,0, soit **802 centipions** : `Nxe7+` prend la dame. Le roque ne répond pas au dernier coup adverse.

### Le roi entre dans le mat — 15 septembre 2026

[Partie](https://www.chess.com/game/live/174516654780), Noirs, mat, 981 contre 975. `1.e4 e5 2.Nc3 Nc6 3.Nf3 Nf6`, puis le fou vient en f7 et le roi sort.

Au coup 15 le roi est en g7, la dame blanche en f6, des cavaliers en d5 et g5. Tu joues `15...Kh6`. Il reste **138 secondes** (2 min 18 s). Stockfish joue `15...Kg8` et annonce un **mat en 3**. L'évaluation avant le coup est encore légèrement positive (+0,8). Plus tôt dans la partie, `10...Nxa1` avait pris une tour : le matériel ne protège pas un roi qui avance.

### Le même pas de roi, avec les Blancs — 9 novembre 2026

[Partie](https://www.chess.com/game/live/186851980944), Blancs, défaite, 958 contre 954. Ta structure : `1.d4 d5 2.Bf4 Nc6 3.Nf3 Bg4`.

Au coup 27 le roi est en d2, la dame noire en h6, des tours sur la colonne d et e. Tu joues `27.Kd3`, en **3,5 secondes**, avec encore **1 min 34 s** après le coup. Stockfish joue `27.Ke2`. Évaluation de 0 à -12,7, soit **1274 centipions**. Position égale, système habituel, le roi fait un pas de trop.

### À l'envers, pour voir ce que tu sais déjà faire

[Partie](https://www.chess.com/game/live/186911974868), 10 novembre 2026, Blancs, victoire. `1.d4 d5 2.Bf4 Nf6 3.Nf3 e6`. Dans l'échantillon : aucune gaffe ≥ 3 points, ACPL plafonné 21, 43 demi-coups. La structure blanche peut se jouer proprement. Le travail n'est pas de la remplacer.

## Cinq axes, dans l'ordre

1. **Avant chaque coup qui n'est pas une reprise forcée, nommer la pièce.** Deux questions : le dernier coup adverse attaque quoi ; mon coup laisse-t-il une pièce en prise. C'est 97 % des pertes nettes, avec du temps, autour du coup 20. Les puzzles entre 1500 et 1650 disent que tu vois ces coups quand l'écran ne montre qu'eux.
2. **Garder le blitz 3+2, et en jouer moins d'affilée.** Sept parties par jour ont accompagné la baisse de septembre. Quatre parties, puis le coup où la pièce est tombée. Pas de bullet dans ces deux semaines.
3. **Noir contre `1.e4` : une règle, pas un nouveau répertoire.** Tu gardes `1...e5` et `2...Nc6`. Contre `3.d4`, si ton cavalier peut être pris par le pion qui vient d'arriver, tu joues ce cavalier (`Ng4` dans la partie du 2 octobre), tu ne joues pas l'autre. Contre `3.Bc4`, avant de prendre en e4, tu regardes f7. Contre `1.d4`, tu gardes `Nf6` et `...g6`.
4. **Le roi ne va pas chercher le mat.** Quand le roi bouge, ou qu'une dame est à côté : le prochain coup est-il échec, et mat. Les parties du 15 septembre et du 9 novembre sont le modèle. Ce n'est pas un cours de finales.
5. **Blancs : ne rien ajouter.** `1.d4`, `Bf4`, `Nf3`, `e3`, `c3`, fou en d3, petit roque. Tu prends `1...e5`. Tu regardes seulement, sans changer de système, les parties où le cavalier noir vient en c6 derrière `...Nf6` (19 parties, 34 %).

## Limites

- La perte nette ne voit qu'une capture et une reprise. Les fourchettes en deux coups sont dans les gaffes du moteur, pas toutes dans le compteur de matériel.
- Profondeur 12 : assez pour une pièce en prise ou un mat court, pas pour une finale subtile de 30 centipions.
- L'échantillon de novembre est de 5 parties au moteur et de 43 au corpus. Le score de 63 % en novembre ne se lit pas comme un nouveau niveau.
- Les deux camps donnent des pièces à ce classement. Ton score global de 50 % le dit. L'écart mesuré est ailleurs : tu es plus souvent le premier à la donner pour de bon.
- Le classement de puzzles et le classement de blitz ne sont pas la même échelle. L'écart sert de signal, pas de promesse de 1600 en parties.

Le plan qui suit ces axes est [ici](../plans/2026-11-19-plan-2-semaines.md).
