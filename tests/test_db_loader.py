# -*- coding: utf-8 -*-

"""
Tests unitaires pour le module DatabaseLoader avec config.yaml réel.

Author: Jules Courné
Date: 2025-12-31
"""

import pytest
import pandas as pd
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import yaml

# Ajouter le chemin parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.db_loader import DatabaseLoader
from src.load.database_connection import DatabaseConnection
from src.utils.config_loader import ConfigLoader


class TestDatabaseLoader:
    """Tests pour la classe DatabaseLoader avec config.yaml."""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset le singleton DatabaseConnection avant chaque test."""
        DatabaseConnection._instance = None
        DatabaseConnection._connection = None
        yield
        if DatabaseConnection._connection:
            try:
                DatabaseConnection._connection.close()
            except:
                pass
        DatabaseConnection._instance = None
        DatabaseConnection._connection = None
    
    @pytest.fixture
    def config_with_temp_db(self, tmp_path):
        """Charge la vraie config mais avec une BDD temporaire."""
        # Charger le vrai config.yaml
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            pytest.skip(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Remplacer le chemin de la BDD par un temporaire
        temp_db_path = tmp_path / "test_books.db"
        
        # Créer une instance de ConfigLoader
        config = ConfigLoader(str(config_path))
        
        # Override du chemin de la BDD
        original_get_db_path = config.get_db_path
        config.get_db_path = lambda: str(temp_db_path)
        
        return config
    
    @pytest.fixture
    def loader(self, config_with_temp_db):
        """Fixture pour créer une instance de DatabaseLoader."""
        return DatabaseLoader(config_with_temp_db)
    
    @pytest.fixture
    def sample_dim_books(self):
        """Fixture pour créer un DataFrame DimBooks."""
        return pd.DataFrame({
            'bookID': [1, 2, 3],
            'isbn13': ['1234567890123', '2345678901234', '3456789012345'],
            'title': ['Book 1', 'Book 2', 'Book 3']
        })
    
    @pytest.fixture
    def sample_dim_authors(self):
        """Fixture pour créer un DataFrame DimAuthors."""
        return pd.DataFrame({
            'authorID': [1, 2, 3],
            'author_name': ['Author A', 'Author B', 'Author C']
        })
    
    @pytest.fixture
    def sample_dim_publishers(self):
        """Fixture pour créer un DataFrame DimPublishers."""
        return pd.DataFrame({
            'publisherID': [1, 2],
            'publisher_name': ['Publisher X', 'Publisher Y']
        })
    
    @pytest.fixture
    def sample_dim_languages(self):
        """Fixture pour créer un DataFrame DimLanguages."""
        return pd.DataFrame({
            'languageID': [1, 2, 3],
            'language_code': ['eng', 'fra', 'spa'],
            'language_name': ['English', 'French', 'Spanish'],
            'country': ['USA', 'France', 'Spain']
        })
    
    @pytest.fixture
    def sample_dim_dates(self):
        """Fixture pour créer un DataFrame DimDates."""
        return pd.DataFrame({
            'dateID': [1, 2, 3],
            'publication_date': ['2020-01-01', '2020-06-15', '2021-03-20'],
            'year': [2020, 2020, 2021],
            'month': [1, 6, 3],
            'day': [1, 15, 20],
            'month_name': ['January', 'June', 'March'],
            'day_name': ['Wednesday', 'Monday', 'Saturday'],
            'quarter': [1, 2, 1]
        })
    
    @pytest.fixture
    def sample_dim_genres(self):
        """Fixture pour créer un DataFrame DimGenres."""
        return pd.DataFrame({
            'genreID': [1, 2, 3],
            'genre_name': ['Fiction', 'Science Fiction', 'Fantasy']
        })
    
    @pytest.fixture
    def sample_fact_books(self):
        """Fixture pour créer un DataFrame FactBooks."""
        return pd.DataFrame({
            'bookID': [1, 2, 3],
            'publisherID': [1, 2, 1],
            'languageID': [1, 2, 1],
            'dateID': [1, 2, 3],
            'genreID': [1, 2, 3],
            'average_rating': [4.5, 3.8, 4.2],
            'ratings_count': [1000, 500, 750],
            'text_reviews_count': [50, 25, 40],
            'num_pages': [300, 250, 400],
            'engagement': [0.05, 0.05, 0.053]
        })
    
    @pytest.fixture
    def sample_source_df(self):
        """Fixture pour créer un DataFrame source."""
        return pd.DataFrame({
            'bookID': [1, 2, 3],
            'authors': ['Author A', 'Author B / Author C', 'Author A']
        })
    
    def test_init(self, config_with_temp_db):
        """Test l'initialisation du DatabaseLoader."""
        loader = DatabaseLoader(config_with_temp_db)
        
        assert loader.config == config_with_temp_db
        assert loader.logger is not None
        assert loader.batch_size >= 100  # Valeur du config
        assert loader.changes_detected is False
        assert isinstance(loader.auto_id_columns, dict)
    
    def test_auto_id_columns_mapping(self, loader):
        """Test le mapping des colonnes auto-incrémentées."""
        assert loader.auto_id_columns['DimBooks'] is None
        assert loader.auto_id_columns['DimAuthors'] == 'authorID'
        assert loader.auto_id_columns['DimPublishers'] == 'publisherID'
        assert loader.auto_id_columns['DimLanguages'] == 'languageID'
        assert loader.auto_id_columns['DimDates'] == 'dateID'
        assert loader.auto_id_columns['DimGenres'] == 'genreID'
        assert loader.auto_id_columns['FactBooks'] is None
    
    def test_database_schema_from_config(self, loader):
        """Test que les tables sont créées selon config.yaml."""
        loader.db_conn.create_database()
        
        # Vérifier que toutes les tables existent
        expected_tables = [
            'DimBooks', 'DimAuthors', 'DimPublishers', 'DimGenres',
            'DimLanguages', 'DimDates', 'FactBooks', 'BridgeAuthorBook',
            'BookPCA', 'AuthorPCA', 'PublisherPCA'
        ]
        
        for table in expected_tables:
            assert loader.db_conn.table_exists(table), f"Table {table} should exist"
    
    def test_prepare_data_with_datetime(self, loader):
        """Test la préparation de données avec datetime."""
        df = pd.DataFrame({
            'id': [1, 2],
            'date': pd.to_datetime(['2020-01-01', '2020-06-15']),
            'value': [10, 20]
        })
        
        data = loader._prepare_data(df)
        
        assert len(data) == 2
        assert data[0][1] == '2020-01-01 00:00:00'
        assert data[1][1] == '2020-06-15 00:00:00'
    
    def test_prepare_data_with_nan(self, loader):
        """Test la préparation de données avec NaN."""
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Test', None],
            'value': [10, pd.NA]
        })
        
        data = loader._prepare_data(df)
        
        assert data[0] == (1, 'Test', 10)
        assert data[1][1] is None
        assert data[1][2] is None
    
    def test_upsert_dim_books_insert_new(self, loader, sample_dim_books):
        """Test l'insertion de nouveaux livres."""
        loader.db_conn.create_database()
        
        changed = loader._upsert_dim_books(sample_dim_books)
        
        assert changed is True
        
        # Vérifier l'insertion
        count = loader.db_conn.get_table_count('DimBooks')
        assert count == 3
        
        # Vérifier les colonnes créées (created_at)
        cursor = loader.db_conn._connection.cursor()
        cursor.execute("SELECT title, created_at FROM DimBooks WHERE bookID = 1")
        row = cursor.fetchone()
        assert row[0] == 'Book 1'
        assert row[1] is not None  # created_at doit être défini
    
    def test_upsert_dim_books_no_changes(self, loader, sample_dim_books):
        """Test avec des livres déjà existants et inchangés."""
        loader.db_conn.create_database()
        loader._upsert_dim_books(sample_dim_books)
        
        changed = loader._upsert_dim_books(sample_dim_books)
        
        assert changed is False
        assert loader.db_conn.get_table_count('DimBooks') == 3
    
    def test_upsert_dim_books_update_existing(self, loader, sample_dim_books):
        """Test la mise à jour de livres existants."""
        loader.db_conn.create_database()
        loader._upsert_dim_books(sample_dim_books)
        
        # Modifier un titre
        modified_books = sample_dim_books.copy()
        modified_books.loc[0, 'title'] = 'Book 1 - Updated'
        
        changed = loader._upsert_dim_books(modified_books)
        
        assert changed is True
        
        # Vérifier la mise à jour
        cursor = loader.db_conn._connection.cursor()
        cursor.execute("SELECT title FROM DimBooks WHERE isbn13 = ?", ('1234567890123',))
        title = cursor.fetchone()[0]
        
        assert title == 'Book 1 - Updated'
    
    def test_insert_new_records_authors(self, loader, sample_dim_authors):
        """Test l'insertion de nouveaux auteurs."""
        loader.db_conn.create_database()
        
        changed = loader._insert_new_records('DimAuthors', sample_dim_authors)
        
        assert changed is True
        
        # Vérifier l'insertion (authorID est auto-incrémenté)
        cursor = loader.db_conn._connection.cursor()
        cursor.execute("SELECT author_name FROM DimAuthors ORDER BY author_name")
        authors = [row[0] for row in cursor.fetchall()]
        
        assert len(authors) == 3
        assert 'Author A' in authors
    
    def test_insert_new_records_auto_id_excluded(self, loader):
        """Test que la colonne auto-incrémentée est exclue."""
        loader.db_conn.create_database()
        
        # DataFrame avec authorID explicite (devrait être ignoré)
        df_with_id = pd.DataFrame({
            'authorID': [100, 200],
            'author_name': ['Author X', 'Author Y']
        })
        
        loader._insert_new_records('DimAuthors', df_with_id)
        
        # Vérifier que les IDs auto-générés sont utilisés
        cursor = loader.db_conn._connection.cursor()
        cursor.execute("SELECT authorID FROM DimAuthors ORDER BY authorID")
        ids = [row[0] for row in cursor.fetchall()]
        
        # SQLite auto-increment commence à 1
        assert ids == [1, 2]
    
    def test_insert_all_dimensions(self, loader, sample_dim_authors, sample_dim_publishers,
                                   sample_dim_languages, sample_dim_dates, sample_dim_genres):
        """Test l'insertion de toutes les dimensions."""
        loader.db_conn.create_database()
        
        # Insérer toutes les dimensions
        loader._insert_new_records('DimAuthors', sample_dim_authors)
        loader._insert_new_records('DimPublishers', sample_dim_publishers)
        loader._insert_new_records('DimLanguages', sample_dim_languages)
        loader._insert_new_records('DimDates', sample_dim_dates)
        loader._insert_new_records('DimGenres', sample_dim_genres)
        
        # Vérifier les counts
        assert loader.db_conn.get_table_count('DimAuthors') == 3
        assert loader.db_conn.get_table_count('DimPublishers') == 2
        assert loader.db_conn.get_table_count('DimLanguages') == 3
        assert loader.db_conn.get_table_count('DimDates') == 3
        assert loader.db_conn.get_table_count('DimGenres') == 3
    
    def test_upsert_bridge_from_source_new_relations(self, loader, sample_dim_books,
                                                     sample_dim_authors, sample_source_df):
        """Test la création de nouvelles relations livre-auteur."""
        loader.db_conn.create_database()
        
        # Insérer les livres et auteurs
        loader._upsert_dim_books(sample_dim_books)
        loader._insert_new_records('DimAuthors', sample_dim_authors)
        
        # Créer les relations
        changed = loader._upsert_bridge_from_source(sample_source_df)
        
        assert changed is True
        
        # Vérifier les relations
        cursor = loader.db_conn._connection.cursor()
        cursor.execute("SELECT bookID, authorID FROM BridgeAuthorBook ORDER BY bookID, authorID")
        relations = cursor.fetchall()
        
        # Book 1 -> Author A (ID=1)
        # Book 2 -> Author B (ID=2), Author C (ID=3)
        # Book 3 -> Author A (ID=1)
        assert len(relations) == 4
    
    def test_upsert_bridge_multiple_authors(self, loader):
        """Test avec plusieurs auteurs séparés par '/'."""
        loader.db_conn.create_database()
        
        books = pd.DataFrame({
            'bookID': [1],
            'isbn13': ['123'],
            'title': ['Book 1']
        })
        authors = pd.DataFrame({
            'authorID': [1, 2, 3],
            'author_name': ['Author A', 'Author B', 'Author C']
        })
        source = pd.DataFrame({
            'bookID': [1],
            'authors': ['Author A / Author B / Author C']
        })
        
        loader._upsert_dim_books(books)
        loader._insert_new_records('DimAuthors', authors)
        loader._upsert_bridge_from_source(source)
        
        # Vérifier qu'il y a 3 relations
        count = loader.db_conn.get_table_count('BridgeAuthorBook')
        assert count == 3
    
    def test_foreign_key_constraints(self, loader, sample_dim_books, sample_fact_books):
        """Test que les contraintes FK sont respectées."""
        loader.db_conn.create_database()
        
        # Insérer les livres et dimensions nécessaires
        loader._upsert_dim_books(sample_dim_books)
        loader._insert_new_records('DimPublishers', pd.DataFrame({
            'publisherID': [1, 2],
            'publisher_name': ['Pub A', 'Pub B']
        }))
        loader._insert_new_records('DimLanguages', pd.DataFrame({
            'languageID': [1, 2],
            'language_code': ['eng', 'fra'],
            'language_name': ['English', 'French'],
            'country': ['USA', 'France']
        }))
        loader._insert_new_records('DimDates', pd.DataFrame({
            'dateID': [1, 2, 3],
            'publication_date': ['2020-01-01', '2020-06-15', '2021-03-20'],
            'year': [2020, 2020, 2021],
            'month': [1, 6, 3],
            'day': [1, 15, 20],
            'month_name': ['January', 'June', 'March'],
            'day_name': ['Wed', 'Mon', 'Sat'],
            'quarter': [1, 2, 1]
        }))
        loader._insert_new_records('DimGenres', pd.DataFrame({
            'genreID': [1, 2, 3],
            'genre_name': ['Fiction', 'Sci-Fi', 'Fantasy']
        }))
        
        # Insérer les faits
        loader._insert_new_records('FactBooks', sample_fact_books)
        
        # Vérifier l'insertion
        assert loader.db_conn.get_table_count('FactBooks') == 3
    
    @patch('src.load.db_loader.PCACalculator')
    def test_load_all_tables_success(self, mock_pca, loader, sample_dim_books, sample_dim_authors,
                                     sample_dim_publishers, sample_dim_languages, sample_dim_dates,
                                     sample_dim_genres, sample_fact_books, sample_source_df):
        """Test le chargement complet de toutes les tables."""
        # Mock PCA
        mock_pca_instance = Mock()
        mock_pca_instance.calculate_and_load_all.return_value = True
        mock_pca.return_value = mock_pca_instance
        
        tables = {
            'dim_books': sample_dim_books,
            'dim_authors': sample_dim_authors,
            'dim_publishers': sample_dim_publishers,
            'dim_languages': sample_dim_languages,
            'dim_dates': sample_dim_dates,
            'dim_genres': sample_dim_genres,
            'fact_books': sample_fact_books
        }
        
        success = loader.load_all_tables(tables, sample_source_df)
        
        assert success is True
        assert loader.changes_detected is True
        
        # Vérifier que PCA a été appelée
        mock_pca_instance.calculate_and_load_all.assert_called_once()
        
        # Vérifier les counts
        assert loader.db_conn.get_table_count('DimBooks') == 3
        assert loader.db_conn.get_table_count('DimAuthors') == 3
        assert loader.db_conn.get_table_count('BridgeAuthorBook') == 4
        assert loader.db_conn.get_table_count('FactBooks') == 3
    
    def test_check_data_integrity(self, loader, sample_dim_books, sample_fact_books,
                                  sample_dim_publishers, sample_dim_languages,
                                  sample_dim_dates, sample_dim_genres):
        """Test la vérification d'intégrité des données."""
        loader.db_conn.create_database()
        
        # Insérer des données valides
        loader._upsert_dim_books(sample_dim_books)
        loader._insert_new_records('DimPublishers', sample_dim_publishers)
        loader._insert_new_records('DimLanguages', sample_dim_languages)
        loader._insert_new_records('DimDates', sample_dim_dates)
        loader._insert_new_records('DimGenres', sample_dim_genres)
        loader._insert_new_records('FactBooks', sample_fact_books)
        
        # Ne devrait pas lever d'exception
        loader._check_data_integrity()
    
    def test_created_at_timestamp(self, loader, sample_dim_books):
        """Test que les timestamps created_at sont créés automatiquement."""
        loader.db_conn.create_database()
        loader._upsert_dim_books(sample_dim_books)
        
        cursor = loader.db_conn._connection.cursor()
        cursor.execute("SELECT created_at FROM DimBooks WHERE bookID = 1")
        created_at = cursor.fetchone()[0]
        
        assert created_at is not None
        # Vérifier le format (YYYY-MM-DD HH:MM:SS)
        assert len(created_at) >= 19


class TestDatabaseLoaderIntegration:
    """Tests d'intégration pour DatabaseLoader avec config.yaml."""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset le singleton avant chaque test."""
        DatabaseConnection._instance = None
        DatabaseConnection._connection = None
        yield
        if DatabaseConnection._connection:
            try:
                DatabaseConnection._connection.close()
            except:
                pass
        DatabaseConnection._instance = None
        DatabaseConnection._connection = None
    
    @pytest.fixture
    def config_with_temp_db(self, tmp_path):
        """Charge la vraie config avec BDD temporaire."""
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            pytest.skip(f"Config file not found: {config_path}")
        
        config = ConfigLoader(str(config_path))
        temp_db_path = tmp_path / "integration_test.db"
        config.get_db_path = lambda: str(temp_db_path)
        
        return config
    
    @patch('src.load.db_loader.PCACalculator')
    def test_complete_workflow(self, mock_pca, config_with_temp_db):
        """Test le workflow complet avec le vrai schéma."""
        mock_pca_instance = Mock()
        mock_pca_instance.calculate_and_load_all.return_value = True
        mock_pca.return_value = mock_pca_instance
        
        loader = DatabaseLoader(config_with_temp_db)
        
        # Préparer des données réalistes
        tables = {
            'dim_books': pd.DataFrame({
                'bookID': [1, 2, 3],
                'isbn13': ['1111111111111', '2222222222222', '3333333333333'],
                'title': ['The Great Book', 'Another Story', 'Epic Tale']
            }),
            'dim_authors': pd.DataFrame({
                'authorID': [1, 2, 3],
                'author_name': ['J.K. Rowling', 'George R.R. Martin', 'J.R.R. Tolkien']
            }),
            'dim_publishers': pd.DataFrame({
                'publisherID': [1, 2],
                'publisher_name': ['Penguin Books', 'HarperCollins']
            }),
            'dim_languages': pd.DataFrame({
                'languageID': [1, 2],
                'language_code': ['eng', 'fra'],
                'language_name': ['English', 'French'],
                'country': ['USA', 'France']
            }),
            'dim_dates': pd.DataFrame({
                'dateID': [1, 2, 3],
                'publication_date': ['2020-01-15', '2019-06-20', '2021-09-10'],
                'year': [2020, 2019, 2021],
                'month': [1, 6, 9],
                'day': [15, 20, 10],
                'month_name': ['January', 'June', 'September'],
                'day_name': ['Wednesday', 'Thursday', 'Friday'],
                'quarter': [1, 2, 3]
            }),
            'dim_genres': pd.DataFrame({
                'genreID': [1, 2, 3],
                'genre_name': ['Fantasy', 'Science Fiction', 'Mystery']
            }),
            'fact_books': pd.DataFrame({
                'bookID': [1, 2, 3],
                'publisherID': [1, 2, 1],
                'languageID': [1, 1, 2],
                'dateID': [1, 2, 3],
                'genreID': [1, 2, 3],
                'average_rating': [4.7, 4.3, 4.5],
                'ratings_count': [50000, 30000, 45000],
                'text_reviews_count': [2500, 1500, 2000],
                'num_pages': [450, 600, 380],
                'engagement': [0.05, 0.05, 0.053]
            })
        }
        
        source_df = pd.DataFrame({
            'bookID': [1, 2, 3],
            'authors': ['J.K. Rowling', 'George R.R. Martin', 'J.R.R. Tolkien / J.K. Rowling']
        })
        
        # Exécuter le chargement
        success = loader.load_all_tables(tables, source_df)
        
        assert success is True
        
        # Vérifications détaillées
        conn = loader.db_conn.get_connection()
        cursor = conn.cursor()
        
        # Vérifier les tables principales
        cursor.execute("SELECT COUNT(*) FROM DimBooks")
        assert cursor.fetchone()[0] == 3
        
        cursor.execute("SELECT COUNT(*) FROM DimAuthors")
        assert cursor.fetchone()[0] == 3
        
        cursor.execute("SELECT COUNT(*) FROM FactBooks")
        assert cursor.fetchone()[0] == 3
        
        # Vérifier les relations
        cursor.execute("SELECT COUNT(*) FROM BridgeAuthorBook")
        assert cursor.fetchone()[0] == 4  # 1→1, 2→2, 3→3, 3→1
        
        # Vérifier une jointure
        cursor.execute("""
            SELECT b.title, a.author_name 
            FROM DimBooks b
            JOIN BridgeAuthorBook ba ON b.bookID = ba.bookID
            JOIN DimAuthors a ON ba.authorID = a.authorID
            WHERE b.bookID = 3
            ORDER BY a.author_name
        """)
        book3_authors = cursor.fetchall()
        assert len(book3_authors) == 2
        
        # Vérifier que PCA a été appelée
        mock_pca_instance.calculate_and_load_all.assert_called_once()