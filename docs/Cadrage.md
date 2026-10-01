# Note de cadrage — Catalogue Goodreads

**Projet :** étude de cas personnelle, entreprise fictive « Lire & Choisir ».

**Date :** 01/10/2026.

**Sujet :** [subject.txt](../subject.txt).

## 1. Problème et décision

La responsable catalogue d'une librairie en ligne souhaite préparer une page de découverte de livres en français. Je dois d'abord vérifier ce que l'extraction Goodreads permet réellement d'analyser, puis proposer **20 fiches à examiner** avant un test.

Le résultat attendu est une liste de travail argumentée. Il ne s'agit pas de prédire des ventes, de fixer un stock ou d'affirmer que ces livres plaisent à tous les clients.

## 2. Acteurs

- Responsable catalogue : valide les critères et les livres proposés.
- Équipe chargée des données catalogue : vérifie les métadonnées et les éditions.
- Responsable commercial : décide d'un éventuel test après contrôle du stock, du prix et des droits.

Ces rôles décrivent la mise en situation. Aucune mission pour une librairie réelle n'est revendiquée.

## 3. Questions

1. Quel est le poids des langues absentes et des autres défauts dans le catalogue ?
2. Comment se répartissent les fiches selon la langue, le nombre de notes et la pagination ?
3. Parmi les fiches en français, lesquelles combinent une bonne note, un volume de notations suffisant et des métadonnées utilisables ?
4. La liste change-t-elle lorsque l'on modifie les seuils ou que l'on évite les répétitions de titre et auteur ?

## 4. Périmètre et grain

J'utilise les **23 fichiers de livres** du dataset Kaggle choisi, **version 18**, mis à jour le **3 décembre 2020**. Les fichiers de notes individuelles restent hors périmètre. Le volume réellement lu est de **1 850 310 lignes**, avant contrôles.

Le grain cible est **une fiche Goodreads identifiée par `Id`**. Plusieurs éditions d'une même œuvre peuvent être présentes. Il n'y a pas d'identifiant d'œuvre utilisé dans ce périmètre : je ne peux pas garantir un nombre de livres distincts au sens éditorial.

La langue et la publication concernent la fiche. Une langue n'identifie pas un pays. Les compteurs de notes peuvent se retrouver sur plusieurs éditions : je ne les additionne pas pour annoncer des lecteurs uniques.

## 5. Indicateurs et critères

KPI principaux : nombre de fiches, part avec une note exploitable, moyenne et médiane des notes par fiche, médiane du volume de notes, part avec au moins 100 notes, couverture de la langue et nombre de fiches en français.

Critères initiaux de candidature : français renseigné, note exploitable ≥ 4/5, au moins 100 notations, auteur et éditeur renseignés, pagination positive ne dépassant pas le seuil d'alerte de 5 000 pages. Les fiches au-delà restent dans le catalogue et demandent une vérification préalable.

Ces seuils sont des hypothèses de travail. La [définition exacte des KPI](Dictionnaire.md) précise les dénominateurs et les bornes.

## 6. Qualité et limites

Les contrôles couvrent les clés, les répétitions, les versions contradictoires, les manquants, les bornes et la concordance des distributions de notes. Les sources restent intactes et les exclusions sont tracées.

Le jeu est ancien et non représentatif du marché actuel. Il ne contient ni ventes, ni prix, ni stock, ni dates individuelles de notation dans les fichiers étudiés. Aucun genre n'est inventé. Les écarts observés sont descriptifs ; aucun effet causal n'est établi.

## 7. Livrables

- [Dictionnaire](Dictionnaire.md), [rapport qualité](Qualité.md) et [synthèse des analyses](Analyse.md).
- [Audit](../notebooks/01_data_quality.ipynb), [analyse globale](../notebooks/02_analyse_globale.ipynb) et [approfondissement](../notebooks/03_analyse_approfondie.ipynb).
- CSV régénérables dans `data/processed`, dont la liste proposée.
- Projet [Power BI](../powerbi/Goodreads.pbip) : catalogue, sélection en français, qualité.
- [README](../README.md) et manifeste des [sources](../data/sources.json).

## 8. Vérification et prochaine décision

Le bilan des lignes doit retrouver le brut. La table principale doit avoir une clé unique et ne pas contenir d'identifiant mis en quarantaine. Les KPI des exports doivent retrouver ceux des notebooks. La liste doit respecter ses critères et éviter les répétitions textuelles de titre et auteur.

Les trois tables ont été actualisées dans le moteur de Power BI Desktop et les résultats DAX rapprochés des exports, y compris sous filtres. La lecture visuelle des pages reste à effectuer, le pilotage Windows étant indisponible. Avant un test commercial, il faudra vérifier les fiches proposées dans le catalogue réel de la librairie et actualiser les signaux Goodreads.
