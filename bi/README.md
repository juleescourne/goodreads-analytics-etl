# Contrat BI et mesures de référence

Un fait représente l'état courant d'un livre (`FactBooks.bookID`). Les avis sont
cumulés ; ils ne mesurent ni ventes ni lecteurs uniques. La date de publication
n'est pas la date des interactions. Les données synthétiques ne décrivent pas le marché.

Importer les tables SQLite via un DSN ODBC configuré dans Power BI Desktop.
Conserver les clés entières, les notes décimales et les dates de publication.

| Relation | Cardinalité | Filtre |
| --- | --- | --- |
| DimBooks → FactBooks | 1 → 1 | livre vers fait |
| DimPublishers / DimLanguages / DimDates / DimGenres → FactBooks | 1 → plusieurs | dimension vers faits |
| DimAuthors → BridgeAuthorBook | 1 → plusieurs | auteur vers liaison |

La mesure `Ratings For Selected Authors` applique les bookID de la liaison avec
`TREATAS`. Ne pas fusionner auteurs et faits : un livre à plusieurs auteurs
multiplierait ses avis. L'attribution intégrale à chaque auteur n'est pas additive.

## Rapprocher SQL et DAX

1. Générer les données et exécuter `python main.py`.
2. Exécuter [verification.sql](verification.sql).
3. Créer individuellement les mesures de [measures.dax](measures.dax) dans Desktop.
4. Sans filtre, rapprocher nombre de livres, avis et note pondérée.
5. Filtrer le premier auteur, puis rapprocher la dernière requête SQL.

[Résultats SQL exécutés](reference-results.tsv) : comparer notamment la somme
correcte des avis avec la somme artificiellement gonflée après jointure auteur.
À filtre identique, l'écart attendu SQL/DAX est nul à l'arrondi près.

**Statut :** SQL exécuté ; DAX proposé, à valider dans Power BI Desktop. Ces
mesures ne sont pas extraites des captures historiques. **Le fichier PBIX/PBIP
original n’a pas été conservé : seules les images sont disponibles.** Le rapport
historique ne peut donc pas être audité ni reproduit à l’identique à partir du dépôt.
Ces mesures constituent une proposition de reconstruction, pas une récupération
du modèle initial.
