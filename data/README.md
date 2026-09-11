# Répertoire `data/`

Le jeu de données source n'est **volontairement pas versionné** dans ce dépôt.

Placez le fichier d'entrée ici :

```text
data/raw/books.csv
```

L'ETL attend les colonnes suivantes (les noms sont ceux du fichier source, en anglais) :

```text
bookID
title
authors
average_rating
isbn13
language_code
num_pages
ratings_count
text_reviews_count
publication_date
publisher_name
genre_name
```

Pas de fichier source sous la main ? Un jeu de substitution est généré par :

```bash
python scripts/generate_sample_data.py
```

Il contient six défauts volontaires (doublons, dates invalides, valeurs manquantes,
notes hors bornes) afin que les règles de validation soient réellement exercées.

Pendant son exécution, le pipeline peut créer :

- `data/archive/` — copies horodatées des fichiers sources traités ;
- `data/processed/` — réservé aux artefacts intermédiaires ;
- `data/database/book_database.db` — la base analytique SQLite.

Ces fichiers générés sont ignorés par Git.
