# Qualité des données — Goodreads

Contrôles réalisés dans [01_data_quality.ipynb](../notebooks/01_data_quality.ipynb), puis vérifiés dans les exports. Source : les 23 fichiers de livres Kaggle, version 18. Aucun fichier brut n'est modifié.

## 1. Ce que j'ai contrôlé

| Contrôle | Ce que j'ai fait |
|---|---|
| Provenance | Vérification des 23 fichiers avec leur empreinte SHA-256, puis suivi du nombre de lignes par fichier |
| Structure | Harmonisation de `PagesNumber` et `pagesNumber` ; chargement des 18 champs communs utiles |
| Unicité | Recherche des répétitions sur les champs chargés, puis des identifiants encore répétés |
| Complétude | Comptage des langues, éditeurs et paginations manquants ou inutilisables |
| Validité | Identifiant entier positif, titre présent, bornes des notes, pagination et année |
| Cohérence | Somme des cinq effectifs de notes comparée au total ; moyenne recalculée comparée à la note annoncée |
| Traçabilité | Conservation du fichier et de la position de l'enregistrement source |

## 2. Bilan des lignes

| Étape | Lignes |
|---|---:|
| Fichiers bruts réunis | 1 850 310 |
| Répétitions retirées | 112 |
| Versions contradictoires mises en quarantaine | 166 |
| Fiches conservées | **1 850 032** |

**1 850 310 = 112 + 166 + 1 850 032.** La table finale a un `IdLivre` unique. Aucun identifiant mis en quarantaine ne se retrouve dans cette table.

Les 112 répétitions sont identiques sur les **champs chargés et normalisés**, pas nécessairement sur tous les champs des CSV, puisque les descriptions ne sont pas étudiées.

Après leur retrait, **83 identifiants** possèdent encore deux versions différentes. Sans date fiable pour choisir la bonne, je mets leurs **166 lignes** dans `quarantaine.csv`. Je ne garde pas arbitrairement la première version. Aucun autre rejet pour identifiant invalide ou titre absent n'est nécessaire sur cette extraction.

## 3. Problèmes conservés et traitement

Les effectifs ci-dessous concernent les 1 850 032 fiches conservées. Les catégories peuvent se recouper : il ne faut pas les additionner pour annoncer un total de fiches en défaut.

| Constat | Fiches | Décision |
|---|---:|---|
| Langue absente | 1 598 339, soit **86,40 %** | Catégorie « Non renseignée » ; aucune langue déduite du titre |
| Éditeur absent | 17 819 | Conserver la fiche et un indicateur d'absence ; exclure de la sélection automatique |
| Pagination non exploitable | 11 172 | Valeur numérique vide ; pas de remplacement par une moyenne |
| Année non exploitable | 72 | Valeur vide si absente, non entière ou hors de 1 à 2020 |
| Aucune notation | 451 777 | Compteur à zéro conservé, mais note analytique vide |
| Distribution de notes incohérente | 1 | Compteur invalide et note analytique vides ; fiche conservée avec une alerte |
| Pagination supérieure à 5 000 | 328 | Alerte, sans suppression du catalogue ; vérification avant sélection |
| Titre et auteur répétés après normalisation | 349 270 | Marqueur de rapprochement ; pas de suppression automatique des éditions |

La normalisation des langues réunit notamment les variantes anglaises et françaises. Le code source reste disponible dans la table de nettoyage. Les autres langues peu présentes sont regroupées pour la lecture du rapport.

### Le cas du compteur négatif

La fiche **3485352**, dans `book3000k-4000k.csv`, à la position **171210**, contient `RatingDist5 = 5:-2` et `RatingDistTotal = total:-2`, avec une note annoncée de 5. Un nombre négatif de notations n'est pas utilisable. Le parseur le laisse vide et `DistributionValide` vaut faux. Cette fiche n'est donc ni une fiche à zéro note, ni une candidate à la sélection.

### Les notes exploitables

Une note est utilisable si les cinq effectifs sont présents et non négatifs, leur somme retrouve le compteur total, le compteur est positif, et la note annoncée entre 1 et 5 diffère de la moyenne recalculée d'au plus **0,01**.

Cela donne **1 398 254 fiches avec une note exploitable**, soit **75,58 %** du catalogue. Aucun autre écart de note n'est détecté parmi les compteurs positifs. Les **451 777 zéros** et la **fiche au compteur négatif** expliquent les notes laissées vides.

### Les répétitions de titre et auteur

Je normalise la casse, les espaces et la ponctuation du titre, puis je rapproche le titre et le champ auteur. Cela évite, par exemple, deux propositions de Harry Potter 7 séparées seulement par une virgule. Ce rapprochement peut encore manquer des éditions ou réunir des titres proches : ce n'est pas un identifiant d'œuvre.

## 4. Limites qui restent

- L'extraction date de **décembre 2020** : elle ne décrit pas la demande actuelle.
- Un identifiant désigne une fiche Goodreads ; plusieurs éditions peuvent partager des informations. Les compteurs ne sont pas additionnés pour calculer des lecteurs uniques.
- La langue manque trop souvent pour déduire la part réelle de livres français dans l'ensemble du catalogue.
- Jour et mois présentent des valeurs ambiguës ; je ne construis pas de date complète. L'année seule reste un attribut de publication.
- Les ISBN restent du texte. Leur clé de contrôle, la bonne édition et la disponibilité commerciale ne sont pas validées ici.
- Les auteurs/contributeurs restent dans un champ texte. Le dataset ne fournit pas de genre exploité dans cette étude.

## 5. Décision pour l'analyse

Le catalogue contrôlé convient à une **analyse descriptive avec ses limites visibles**. Pour la mission francophone, je retiens uniquement les fiches explicitement renseignées en français. Je demande un volume de notes et des métadonnées utilisables avant de proposer une fiche, puis je prévois une validation manuelle avant tout test commercial.

Les exports de contrôle sont `audit_sources.csv`, `controle_qualite.csv` et `quarantaine.csv`. Les règles exactes sont dans le [dictionnaire](Dictionnaire.md).

## 6. Vérification dans Power BI

Les trois tables ont été actualisées sans erreur dans le moteur local de Power BI Desktop. Les **33 mesures** retrouvent les calculs Pandas dans **six contextes** : catalogue, français, anglais, zéro notation, compteur absent et périmètre vide. Les 20 identifiants proposés, leur rang, leur titre, leur note et leur compteur concordent également.

Le contrôle du zéro a notamment permis d'utiliser `== 0` en DAX, afin de ne pas inclure le compteur manquant dans les fiches sans notation. Le bilan d'import reste fixe sous filtres et les ratios sans dénominateur restent vides. Les [résultats de contrôle](../powerbi/controle_resultats.json) sont conservés. Le rendu visuel des pages reste à vérifier dans Desktop.
