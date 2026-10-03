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

## 4. Lire la liste proposée

La liste contient **20 fiches et 12 libellés d'auteur distincts**. Elle comprend notamment *Mafalda, l'intégrale*, *Le Monogramme*, des albums de Calvin et Hobbes et plusieurs tomes de *Fullmetal Alchemist*. Six fiches sont attribuées à Hiromu Arakawa : un classement automatique peut concentrer les propositions sur une même série.

Il n'y a pas d'ISBN manquant dans cette liste, mais cela ne valide ni l'ISBN ni l'édition. Une des fiches appartient à un groupe titre/auteur répété dans le catalogue ; seule sa représentante entre dans la liste.

Le résultat ne doit donc pas être publié tel quel comme « les 20 meilleurs livres ». Il faut relire les titres, distinguer les coffrets, les séries et les éditions, puis vérifier l'offre réelle de la librairie. La sélection complète est exportée dans `data/processed/selection_francais.csv` et affichée dans le notebook approfondi.

## 5. Recommandation

Je recommande de **faire vérifier les 20 propositions**, puis de tester une petite page de découverte avec les titres réellement disponibles. La priorité est la qualité et la diversité de la liste avant un classement plus sophistiqué.

| Prochaine action | Données ou validation attendues |
|---|---|
| Vérifier les fiches | Bon titre, édition, ISBN, format et identifiant d'œuvre |
| Équilibrer la sélection | Éviter trop de tomes d'une même série ; catégories validées par l'équipe catalogue |
| Vérifier la faisabilité | Catalogue commercial, disponibilité, stock, prix et droits |
| Actualiser le signal | Notes récentes et date de collecte documentée |
| Tester la page | Taux de clic = clics sur les livres / impressions des livres ; taux d'ajout = sessions avec ajout / sessions ayant consulté la page, avec règles de comptage stables |

La disponibilité et la diversité sont des garde-fous. Aucun gain de clic, de panier ou de chiffre d'affaires n'est calculé : ces données ne sont pas fournies. Cette analyse est descriptive et ne justifie pas un test statistique causal sur les seules fiches Goodreads.

## 6. Traduction dans Power BI

| Page | Question traitée |
|---|---|
| Comprendre le catalogue | Quelle est la couverture des données et comment se répartissent les fiches ? |
| Sélection en français | Combien de fiches passent les critères, quel est l'effet du seuil de notations et quelle diversité présente la liste ? |
| Qualité des données | Quels défauts restent dans le périmètre filtré et combien de lignes ont été retirées à l'import ? |

Les KPI du catalogue réagissent aux filtres. Le bilan d'import reste fixe. Les critères et le classement sont calculés sur la source complète : filtrer la liste réduit l'affichage, sans fabriquer un nouveau top 20. Le [guide Power BI](../powerbi/LISEZ_MOI.txt) décrit l'ouverture et les valeurs de contrôle.

La page de sélection montre désormais deux résultats utiles à la décision : **3 002, 2 409 et 2 123 candidats** selon le minimum de notations, et la répartition de la liste par libellé d'auteur (**6 fiches sur 20 pour Hiromu Arakawa**, sans filtre). Le graphique des seuils reste sur le catalogue français complet, indépendamment des menus ; celui des auteurs suit le périmètre visible. La comparaison des notes selon la pagination reste consultable dans le notebook approfondi.

Le [script vidéo](Script_video.txt) suit le cadrage puis les trois pages : choix des indicateurs, résultats, interprétation et suites proposées. La sensibilité est une comparaison de scénarios déjà calculés, pas un outil qui recalcule une sélection de vingt fiches à chaque clic.
