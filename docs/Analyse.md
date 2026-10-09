# Analyse — Préparer une sélection de livres en français

**Décision à préparer :** proposer 20 fiches à examiner pour une page de découverte de la librairie fictive « Lire & Choisir ».

Cette synthèse reprend [l'analyse globale](../notebooks/02_analyse_globale.ipynb) et [l'analyse approfondie](../notebooks/03_analyse_approfondie.ipynb). Tous les résultats portent sur la version 18 du dataset Kaggle, datant de décembre 2020.

## 1. Le catalogue de départ

| Indicateur | Résultat | Lecture |
|---|---:|---|
| Fiches conservées | **1 850 032** | Une ligne par identifiant Goodreads, pas une œuvre unique |
| Fiches avec note exploitable | 1 398 254 (**75,58 %**) | Les zéros et la distribution invalide sont exclus des moyennes de notes |
| Note moyenne des fiches | **3,83 / 5** | Moyenne non pondérée : chaque fiche notée a le même poids |
| Note médiane | **3,89 / 5** | Sur les notes exploitables |
| Nombre médian de notes | **5** | Les compteurs à zéro sont inclus ; le compteur invalide est exclu |
| Fiches avec au moins 100 notes | 342 289 (**18,50 %**) | Part calculée sur toutes les fiches conservées |
| Langue absente | **86,40 %** | Limite majeure pour une sélection par langue |
| Fiches explicitement en français | **16 327** | Périmètre de la mission |

Le catalogue est volumineux, mais le volume de notations est souvent faible. La majorité des langues ne sont pas renseignées : les 16 327 fiches françaises ne représentent pas toutes les fiches qui pourraient être en français.

## 2. Ce que montre l'analyse globale

### Lire la note avec le volume

| Nombre de notes associé à la fiche | Fiches |
|---|---:|
| 0 | 451 777 |
| 1 à 99 | 1 055 965 |
| 100 à 999 | 197 794 |
| 1 000 à 9 999 | 95 952 |
| 10 000 et plus | 48 543 |
| Compteur non exploitable | 1 |

**79 824 fiches affichent une note exploitable de 5/5 avec moins de 100 notations. Aucune n'a 5/5 avec au moins 100 notations.** Trier uniquement sur la note ferait donc remonter beaucoup de fiches peu évaluées. Cela ne prouve pas qu'elles sont mauvaises : le recul disponible est simplement limité.

Parmi les fiches notées, la part à au moins 4/5 est de **45,32 %** pour 1 à 99 notations, **34,83 %** pour 100 à 999, **41,20 %** pour 1 000 à 9 999 et **49,52 %** au-delà. Il n'y a pas de relation simple et régulière entre volume et bonne note.

### Langues, formats et années

Les fiches en français ont une note médiane de **3,87**, avec un nombre médian de **100 notations**. Elles sont assez nombreuses pour un approfondissement descriptif, mais restent un sous-ensemble sélectionné par la disponibilité de la langue.

Les notes médianes par pagination restent proches à l'échelle globale : de **3,86 à 4,00** dans les groupes de pagination renseignée. Je ne conclus pas qu'un livre plus long est mieux apprécié. Les auteurs, les types de livres et les publics peuvent différer.

Les périodes **1980-1999** et **2000-2009** concentrent beaucoup de fiches. L'année décrit une publication renseignée, pas une date de vente ou d'évaluation. Ce graphique ne mesure donc pas une tendance du marché.

## 3. Approfondissement du périmètre français

### Passer du catalogue à une liste exploitable

| Étape cumulative | Fiches |
|---|---:|
| Français renseigné | 16 327 |
| Avec une note exploitable | 15 317 |
| Note d'au moins 4/5 | 5 668 |
| Et au moins 100 notations | 3 104 |
| Et auteur, éditeur, pagination positive ≤ 5 000 présents | **3 002** |
| Une fiche représentante par titre/auteur normalisé | **2 716** |
| Première liste à vérifier | **20** |

Les seuils sont lisibles et discutables avec la responsable catalogue. Ils ne garantissent ni une représentativité statistique, ni de futures ventes. Parmi les éditions candidates rapprochées, je retiens celle au plus grand compteur de notes, puis au plus petit identifiant en cas d'égalité. Je ne fusionne pas les compteurs.

### Comparer des groupes proches

En français, pour les fiches avec **1 à 99 notations**, la médiane est de **3,69** pour 151 à 300 pages (2 394 fiches), contre **4,12** pour plus de 600 pages (537 fiches).

Avec **10 000 notations ou plus**, les médianes sont de **3,98** pour 151 à 300 pages (781 fiches), contre **4,03** pour plus de 600 pages (294 fiches). L'écart descriptif est donc beaucoup plus réduit dans cette tranche de volume.

Cette comparaison aide à éviter une conclusion trop rapide sur la longueur des livres. Elle ne contrôle pas le genre ni les auteurs, et ne démontre aucun effet causal. Les groupes de moins de 30 fiches notées ne sont pas commentés ; ce seuil est une règle de lecture.

### Vérifier la sensibilité des critères

Effectifs candidats avant rapprochement titre/auteur, avec les mêmes critères de métadonnées :

| Note minimum | Au moins 100 notes | Au moins 500 | Au moins 1 000 |
|---|---:|---:|---:|
| 3,8 | 5 341 | 4 220 | 3 705 |
| **4,0** | **3 002** | **2 409** | **2 123** |
| 4,2 | 1 212 | 988 | 865 |

Le passage de 100 à 500 notations à note ≥ 4 réduit le nombre de candidats de **593**, soit **19,75 %**. Dans la liste initiale de 20, **5 fiches** ont moins de 500 notations. Le choix du seuil a donc un effet concret. Je garde 100 comme base de travail et présente cette limite au décideur ; ce n'est pas un seuil « optimal » démontré.

## 4. Comparer la liste initiale et la proposition diversifiée

La liste initiale contient 20 fiches et 12 libellés auteur. Six fiches concernent Hiromu Arakawa. Pour une page de découverte, je compare un plafond de **deux fiches par libellé auteur normalisé**. Les fiches au-delà du plafond laissent place aux suivantes dans le même classement.

| Indicateur au seuil 100 | Liste initiale | Proposition plafonnée |
|---|---:|---:|
| Fiches | 20 | 20 |
| Libellés auteur distincts | 12 | 16 |
| Maximum de fiches par auteur | 6 | 2 |
| Note moyenne | 4,646 | 4,642 |
| Note minimale | 4,59 | 4,57 |

Les moyennes sont arrondies à trois décimales. **16 fiches restent communes** ; les quatre remplaçantes sont attribuées à Hayao Miyazaki, Pierre Clostermann, Stephen King et Natsuki Takaya. Les listes sont publiées dans [les petits exports](livrables/listes_scenarios.csv).

Les nouveaux titres comprennent encore des tomes ou épisodes avancés. Le plafond ne suffit pas à construire une page de découverte définitive. Une [relecture des titres](Relecture_selection.md) précise les points à vérifier sans inventer de disponibilité ni de catégorie commerciale.

## 5. Recalculer les listes et mesurer leur stabilité

Les comparaisons portent sur les identifiants de fiche, avec comme référence **la liste à 100 notations de la même règle**. Un changement d’édition représentante compte comme un changement de fiche.

| Règle | Minimum de notations | Fiches communes / 20 | Entrées / sorties | Libellés auteur | Maximum / auteur |
|---|---:|---:|---:|---:|---:|
| Initiale | 100 | 20 | 0 / 0 | 12 | 6 |
| Initiale | 500 | 15 | 5 / 5 | 10 | 9 |
| Initiale | 1 000 | 15 | 5 / 5 | 10 | 9 |
| Deux par auteur | 100 | 20 | 0 / 0 | 16 | 2 |
| Deux par auteur | 500 | 15 | 5 / 5 | 16 | 2 |
| Deux par auteur | 1 000 | 15 | 5 / 5 | 16 | 2 |

Les deux seuils supérieurs donnent les mêmes listes dans cette extraction. Au seuil 500, la liste initiale se concentre davantage sur un auteur. Un minimum de notations plus élevé ne garantit donc pas une diversité accrue. Les [titres entrants et sortants](livrables/mouvements_selections.csv) permettent de comprendre concrètement les changements.

## 6. Recommandation

Je propose **le seuil de 100 notations et le plafond de deux fiches par libellé auteur** comme point de départ. Cette règle conserve une liste de 20, augmente la diversité des auteurs et modifie peu sa note moyenne. Elle reste un choix éditorial, pas un optimum statistique. La stabilité de 15 fiches sur 20 aux seuils supérieurs donne un repère descriptif ; elle ne mesure pas une performance commerciale.

Avant publication, vérifier les titres, éditions, ISBN et séries, puis la disponibilité, le stock, le prix et les droits dans le catalogue réel. Les genres et les publics doivent être validés par l’équipe catalogue. Les notes doivent être actualisées : cette étude utilise une photographie de 2020.

Un test de mise en avant pourrait ensuite suivre le taux de clic (clics sur les livres / impressions des livres) et le taux d’ajout (sessions avec ajout / sessions ayant consulté la page), avec des règles de comptage stables. Aucun gain financier ni causalité n’est établi par les données Goodreads.

## 7. Restitution et contrôles

La [synthèse PDF](livrables/Goodreads_synthese.pdf), les figures et les listes sont générées depuis les résultats Python. Le [portfolio](https://juleescourne.github.io/portfolio-data-analyst/#/goodreads) permet de comparer les six scénarios réels, leurs titres et leurs mouvements.

La page de sélection Power BI présente une table de stabilité indépendante des filtres, la répartition des auteurs et les 20 propositions plafonnées à deux par auteur. Les menus réduisent l’affichage de cette proposition sans recalculer le classement. Les cinq tables sont décrites dans le [guide](../powerbi/LISEZ_MOI.txt).

Les notebooks ont été réexécutés le 9 octobre 2026 ; dix tests ciblés portent sur les règles de nettoyage et de sélection. Les vérifications historiques du moteur DAX ne sont pas présentées comme une validation de la nouvelle version. L’actualisation et le rendu dans Desktop restent à contrôler après ouverture.
