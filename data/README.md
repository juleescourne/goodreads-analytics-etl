# Data directory

The source dataset is intentionally **not committed** to this repository.

Place the input file at:

```text
data/raw/books.csv
```

The ETL expects the following columns:

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

During execution the pipeline can create:

- `data/archive/` — timestamped copies of processed source files;
- `data/processed/` — reserved for processed artifacts;
- `data/database/book_database.db` — the SQLite analytical database.

These generated files are ignored by Git.
