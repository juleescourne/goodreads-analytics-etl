"""Real CSV -> transform -> dimensions -> SQLite -> PCA, plus recovery."""
import sqlite3
from pathlib import Path
import pandas as pd
import pytest
import yaml
from main import ETLPipeline
from scripts.generate_sample_data import build_rows
from src.load.database_connection import DatabaseConnection
from src.utils.pca_calculator import PCACalculator

@pytest.fixture
def pipeline(tmp_path):
    DatabaseConnection._instance = None
    DatabaseConnection._connection = None
    config = yaml.safe_load(Path('config/config.yaml').read_text())
    for key in ['raw_data', 'processed_data', 'archive', 'logs']:
        config['paths'][key] = str(tmp_path / key)
        (tmp_path / key).mkdir()
    config['paths']['database'] = str(tmp_path / 'books.db')
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(yaml.safe_dump(config))
    runner = ETLPipeline(str(config_path))
    csv_path = tmp_path / 'raw_data/books.csv'
    pd.DataFrame(build_rows(60, 42)).to_csv(csv_path, index=False)
    yield runner, csv_path, tmp_path / 'books.db'
    if DatabaseConnection._instance:
        DatabaseConnection._instance.close()
    DatabaseConnection._instance = None

def snapshot(path):
    with sqlite3.connect(path) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return {t: conn.execute(f'SELECT * FROM {t} ORDER BY 1').fetchall() for t in tables}

def test_end_to_end_repeat_update_and_dimension_remap(pipeline):
    runner, source, db = pipeline
    assert runner.run() == 0
    first = snapshot(db)
    assert len(first['FactBooks']) == 60 and len(first['BookPCA']) > 0
    assert runner.run() == 0
    assert snapshot(db) == first
    frame = pd.read_csv(source).iloc[::-1].copy()
    frame.loc[frame.bookID == 2, 'average_rating'] = 4.75
    frame.loc[frame.bookID == 2, 'ratings_count'] = 98765
    frame.loc[frame.bookID == 2, 'publisher_name'] = 'New publisher'
    frame.loc[frame.bookID == 2, 'authors'] = 'New Author'
    frame.to_csv(source, index=False)
    assert runner.run() == 0
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT average_rating, ratings_count FROM FactBooks WHERE bookID=2').fetchone() == (4.75, 98765)
        assert conn.execute('SELECT publisher_name FROM FactBooks JOIN DimPublishers USING(publisherID) WHERE bookID=2').fetchone() == ('New publisher',)
        assert conn.execute('SELECT author_name FROM BridgeAuthorBook JOIN DimAuthors USING(authorID) WHERE bookID=2').fetchall() == [('New Author',)]
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    updated = snapshot(db)
    assert runner.run() == 0
    assert snapshot(db) == updated

def test_pca_failure_rolls_back_facts_and_partial_pca(pipeline, monkeypatch):
    runner, source, db = pipeline
    assert runner.run() == 0
    before = snapshot(db)
    frame = pd.read_csv(source)
    frame.loc[frame.bookID == 2, 'ratings_count'] = 98765
    frame.to_csv(source, index=False)
    with monkeypatch.context() as patch:
        patch.setattr(PCACalculator, '_load_author_pca', lambda *args: False)
        assert runner.run() == 1
    assert snapshot(db) == before
    assert runner.run() == 0
    assert snapshot(db) != before
