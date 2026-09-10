# Installation

Temps nécessaire : **moins de 2 minutes**, jeu de données inclus.

## Prérequis

| Outil | Version | Vérifier |
| --- | --- | --- |
| Python | 3.11 ou supérieur | `python --version` |
| pip | fourni avec Python | `pip --version` |

Aucun serveur de base de données : SQLite est intégré à Python.

---

## Installation

```bash
git clone https://github.com/juleescourne/goodreads-analytics-etl.git
cd goodreads-analytics-etl

python -m venv .venv
source .venv/bin/activate          # .\.venv\Scripts\Activate.ps1 sous Windows

pip install -r requirements.txt
```

Cinq dépendances : `numpy`, `pandas`, `pydantic`, `PyYAML`, `scikit-learn`. Les
versions sont épinglées.

---

## Exécuter le pipeline

### Avec le jeu de démonstration

Le dataset Goodreads n'est pas redistribué ici. Le dépôt fournit un générateur qui
produit un CSV de structure identique, **défauts compris** :

```bash
python scripts/generate_sample_data.py
python main.py
```

Le pipeline s'exécute en environ 5 secondes et écrit
`data/database/book_database.db`.

Options du générateur :

```bash
python scripts/generate_sample_data.py --rows 1000 --seed 7
```

### Avec le jeu de données réel

Téléchargez le dataset Goodreads, puis placez le fichier ici :

```text
data/raw/books.csv
```

Colonnes attendues :

```text
bookID, title, authors, average_rating, isbn13, language_code,
num_pages, ratings_count, text_reviews_count, publication_date,
publisher_name, genre_name
```

Puis `python main.py`.

---

## Vérifier l'installation

```bash
pip install -r requirements-dev.txt
pytest
```

**278 tests** doivent passer, en une quinzaine de secondes.

Avec la couverture :

```bash
pytest --cov=src --cov-report=term-missing
```

---

## Ce que produit une exécution

```text
data/database/book_database.db    entrepôt SQLite — 11 tables, 10 index
data/archive/books_<horodatage>.csv   copie horodatée de la source
logs/                             trace détaillée de chaque étape
```

Tous ces répertoires sont exclus de Git.

Contrôle rapide du résultat :

```bash
python -c "import sqlite3; c=sqlite3.connect('data/database/book_database.db'); print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")])"
```

---

## Configuration

Tout le comportement est dans `config/config.yaml` :

| Section | Contenu |
| --- | --- |
| `paths` | emplacements source, archive, base, journaux |
| `database` | schémas SQL des 11 tables et des 10 index |
| `csv` | encodage, séparateur, options de lecture |
| `defaults` | valeurs de remplacement des données manquantes |
| `genres` | liste blanche des genres retenus |
| `pipeline` | taille de lot, nombre de tentatives, archivage |

Le format des journaux se règle séparément dans `config/logging_config.yaml`.

> Si vous modifiez la liste `genres`, pensez à aligner `GENRES` dans
> `scripts/generate_sample_data.py` : tout genre absent de la liste blanche bascule
> en « Other ».

---

## Automatisation quotidienne (Windows)

```powershell
cd scheduler
.\setup.ps1
```

Enregistre une tâche quotidienne à minuit qui active l'environnement virtuel,
exécute le pipeline et écrit son état dans `logs/`.

Sous Linux, l'équivalent tient en une ligne de crontab :

```cron
0 0 * * * cd /chemin/vers/le/projet && .venv/bin/python main.py >> logs/cron.log 2>&1
```

---

## Problèmes courants

**`FileNotFoundError: data/raw/books.csv`**
Aucune source n'a été fournie. Lancez `python scripts/generate_sample_data.py`.

**`Colonnes manquantes dans le CSV`**
Le fichier source n'a pas le schéma attendu. La liste des colonnes requises est
rappelée ci-dessus et dans `data/README.md`.

**Toutes les lignes tombent en genre « Other »**
Les valeurs de `genre_name` ne figurent pas dans la liste blanche de
`config/config.yaml`.

**`database is locked`**
La base SQLite est ouverte ailleurs — Power BI, un navigateur SQLite, une autre
exécution. Fermez l'application concernée.
