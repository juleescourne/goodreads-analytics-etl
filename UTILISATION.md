# Guide d'utilisation

Ce guide couvre l'exploitation courante du pipeline : le lancer, lire ce qu'il
raconte, interroger l'entrepôt produit et le brancher sur un outil BI.

---

## 1. Lancer le pipeline

```bash
python main.py
```

Le pipeline affiche sa progression en six phases :

```text
============================================================
PIPELINE ETL - Extraction vers SQLite pour Power BI
============================================================

[1/6] Chargement de la configuration...
[2/6] Extraction des données CSV...
[3/6] Transformation des données...
[4/6] Création des tables dimensionnelles...
[5/6] Validation des tables...
[6/6] Chargement dans la base de données...

============================================================
PIPELINE TERMINÉ AVEC SUCCÈS
============================================================
Durée d'exécution : 4.75 secondes
Lignes traitées : 300
```

Le code de sortie vaut `0` en cas de succès, `1` en cas d'échec — ce qui permet de
l'enchaîner dans un ordonnanceur.

### Relance automatique

```python
from main import run_with_retry
run_with_retry(max_retries=3, retry_delay=5)
```

Utile lorsque la source est déposée par un autre système et peut être
temporairement verrouillée.

---

## 2. Lire la trace d'exécution

Les journaux sont l'intérêt principal du pipeline au quotidien : ils disent ce qui a
été corrigé, et donc ce qui n'allait pas dans la source.

```text
Fichier lu : 301 lignes, 12 colonnes
Statistiques : 301 lignes, 1 doublons
genre_name: valeurs invalides/NA remplacées par 'Other'
average_rating: 1 valeurs corrigées [0-5]
1 paires de doublons supprimées
Transformation terminée : 300 lignes (1 supprimées, 0.3%)
Aucune valeur manquante
```

| Ligne | Ce qu'elle signifie |
| --- | --- |
| `X doublons` | doublons détectés dans la source, avant tout traitement |
| `valeurs corrigées [0-5]` | notes hors intervalle ramenées dans les bornes |
| `remplacées par 'Other'` | genre absent de la liste blanche de configuration |
| `X supprimées (Y %)` | perte totale entre source et sortie |

> **Un taux de suppression qui grimpe est un signal.** Si la source passe
> soudainement de 0,3 % à 15 % de lignes écartées, c'est le format amont qui a
> changé, pas le pipeline qui s'améliore.

La trace complète est écrite dans `logs/`.

---

## 3. Interroger l'entrepôt

L'entrepôt est un fichier SQLite standard : n'importe quel client SQL l'ouvre.

### Les livres les plus discutés au regard de leur audience

```sql
SELECT b.title,
       f.ratings_count,
       f.text_reviews_count,
       ROUND(f.engagement, 4) AS engagement
FROM FactBooks f
JOIN DimBooks b ON b.bookID = f.bookID
WHERE f.ratings_count > 1000
ORDER BY f.engagement DESC
LIMIT 10;
```

### Note moyenne et volume par éditeur

```sql
SELECT p.publisher_name,
       COUNT(*)                       AS livres,
       ROUND(AVG(f.average_rating), 2) AS note_moyenne,
       SUM(f.ratings_count)            AS notes_totales
FROM FactBooks f
JOIN DimPublishers p ON p.publisherID = f.publisherID
GROUP BY p.publisherID
HAVING livres >= 3
ORDER BY note_moyenne DESC;
```

### Production par trimestre

```sql
SELECT d.year, d.quarter, COUNT(*) AS livres
FROM FactBooks f
JOIN DimDates d ON d.dateID = f.dateID
GROUP BY d.year, d.quarter
ORDER BY d.year, d.quarter;
```

### Les auteurs les plus prolifiques, via la table de pont

```sql
SELECT a.author_name, COUNT(*) AS livres
FROM BridgeAuthorBook br
JOIN DimAuthors a ON a.authorID = br.authorID
GROUP BY a.authorID
ORDER BY livres DESC
LIMIT 15;
```

C'est ici que la table de pont montre son intérêt : un livre à trois auteurs compte
pour chacun des trois, sans qu'aucun ne soit arbitrairement désigné principal.

### Lire les segments issus de l'ACP

```sql
SELECT Cluster_Label,
       COUNT(*)                        AS livres,
       ROUND(AVG(average_rating), 2)   AS note_moyenne,
       ROUND(AVG(engagement), 4)       AS engagement_moyen
FROM BookPCA
GROUP BY Cluster_Label
ORDER BY note_moyenne DESC;
```

> Ces libellés sont **descriptifs**, issus d'un K-means non supervisé. Ils résument
> une structure observée : ce ne sont pas des catégories validées, et ils ne
> prédisent rien.

---

## 4. Brancher Power BI

1. **Obtenir des données → Base de données → SQLite** (connecteur ODBC), ou exporter
   les tables en CSV depuis un client SQL.
2. Charger `FactBooks` et les six dimensions.
3. Vérifier les relations : Power BI les détecte généralement sur les clés
   étrangères ; sinon, reliez chaque `DimX.xID` à `FactBooks.xID`, en **plusieurs
   vers un** avec filtrage simple.
4. Marquer `DimDates` comme **table de dates** (`publication_date`), ce qui active
   les fonctions temporelles DAX.

Le modèle en étoile est fait pour ça : les dimensions servent de filtres, la table
de faits d'agrégat.

---

## 5. Relancer sans tout recharger

Le chargement est **incrémental**. Relancer `python main.py` sur une source
inchangée n'écrit rien et conserve l'ACP existante.

Pour repartir de zéro, supprimez simplement la base :

```bash
rm data/database/book_database.db
python main.py
```

---

## 6. Adapter le pipeline

| Besoin | Où intervenir |
| --- | --- |
| Ajouter un genre | liste `genres` dans `config/config.yaml` |
| Changer le séparateur ou l'encodage | section `csv` |
| Ajouter un index | section `indexes` — aucun code à modifier |
| Modifier une valeur de remplacement | section `defaults` |
| Ajuster la verbosité des journaux | `config/logging_config.yaml` |

Les schémas SQL vivant dans la configuration, ajouter une dimension ne demande pas
de toucher au code de chargement.
