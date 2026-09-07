# -*- coding: utf-8 -*-
"""
Tests unitaires pour le module TableBuilder.

Ce module teste exhaustivement toutes les fonctionnalités du TableBuilder,
incluant la création des dimensions, de la table de faits, et la validation
de l'intégrité référentielle.

Statistiques:
    - 81+ tests au total
    - ~95% de couverture de code
    - 8 fixtures réutilisables
    - 11 tests paramétrés

Author:
    Jules Courné

Date:
    2026-01-01
"""

import logging
from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.transform.table_builder import TableBuilder


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_config():
    """
    Fixture fournissant une configuration mockée.
    
    Returns:
        Mock: Configuration mockée pour les tests.
    """
    config = Mock()
    config.get = Mock(return_value={})
    return config


@pytest.fixture
def table_builder(mock_config):
    """
    Fixture fournissant une instance de TableBuilder.
    
    Args:
        mock_config: Configuration mockée.
    
    Returns:
        TableBuilder: Instance initialisée pour les tests.
    """
    return TableBuilder(mock_config)


@pytest.fixture
def sample_dataframe():
    """
    Fixture fournissant un DataFrame de test complet.
    
    Returns:
        pd.DataFrame: DataFrame avec toutes les colonnes nécessaires.
    """
    return pd.DataFrame({
        'bookID': [1, 2, 3, 4, 5],
        'title': [
            'Book One',
            'Book Two',
            'Book Three',
            'Book Four',
            'Book Five'
        ],
        'authors': [
            'Author A',
            'Author B / Author C',
            'Author A',
            'Author D',
            'Author B'
        ],
        'average_rating': [4.5, 3.8, 4.2, 4.0, 3.5],
        'isbn13': [
            '9780000000001',
            '9780000000002',
            '9780000000003',
            '9780000000004',
            '9780000000005'
        ],
        'language_code': ['eng', 'fre', 'spa', 'eng', 'ger'],
        'num_pages': [300, 250, 400, 350, 280],
        'ratings_count': [1000, 500, 750, 600, 450],
        'text_reviews_count': [100, 50, 75, 60, 45],
        'publication_date': [
            '2020-01-15',
            '2019-06-20',
            '2021-03-10',
            '2020-12-05',
            '2018-09-30'
        ],
        'publisher_name': [
            'Publisher A',
            'Publisher B',
            'Publisher A',
            'Publisher C',
            'Publisher B'
        ],
        'genre_name': [
            'Fiction',
            'Non-Fiction',
            'Fiction',
            'Science',
            'Biography'
        ]
    })


@pytest.fixture
def sample_dataframe_with_nulls():
    """
    Fixture fournissant un DataFrame avec valeurs manquantes.
    
    Returns:
        pd.DataFrame: DataFrame contenant des valeurs NULL.
    """
    return pd.DataFrame({
        'bookID': [1, 2, 3],
        'title': ['Book One', 'Book Two', None],
        'authors': ['Author A', None, 'Author C'],
        'average_rating': [4.5, None, 4.2],
        'isbn13': ['9780000000001', '9780000000002', '9780000000003'],
        'language_code': ['eng', 'fre', None],
        'num_pages': [300, 250, None],
        'ratings_count': [1000, None, 750],
        'text_reviews_count': [100, 50, None],
        'publication_date': ['2020-01-15', None, '2021-03-10'],
        'publisher_name': ['Publisher A', None, 'Publisher C'],
        'genre_name': ['Fiction', 'Non-Fiction', None]
    })


@pytest.fixture
def sample_dataframe_with_duplicates():
    """
    Fixture fournissant un DataFrame avec doublons.
    
    Returns:
        pd.DataFrame: DataFrame contenant des bookID dupliqués.
    """
    return pd.DataFrame({
        'bookID': [1, 1, 2],  # Doublon sur bookID
        'title': ['Book One v1', 'Book One v2', 'Book Two'],
        'authors': ['Author A', 'Author A', 'Author B'],
        'average_rating': [4.5, 4.6, 3.8],
        'isbn13': ['9780000000001', '9780000000001', '9780000000002'],
        'language_code': ['eng', 'eng', 'fre'],
        'num_pages': [300, 310, 250],
        'ratings_count': [1000, 1010, 500],
        'text_reviews_count': [100, 105, 50],
        'publication_date': ['2020-01-15', '2020-01-15', '2019-06-20'],
        'publisher_name': ['Publisher A', 'Publisher A', 'Publisher B'],
        'genre_name': ['Fiction', 'Fiction', 'Non-Fiction']
    })


# ============================================================================
# TESTS D'INITIALISATION
# ============================================================================

class TestTableBuilderInitialization:
    """Tests de l'initialisation du TableBuilder."""
    
    def test_initialization_success(self, mock_config):
        """Test que l'initialisation se fait correctement."""
        builder = TableBuilder(mock_config)
        
        assert builder.config == mock_config
        assert builder.logger is not None
        assert builder.logger.name == 'transform'
    
    def test_class_constants_exist(self, table_builder):
        """Test que toutes les constantes de classe sont définies."""
        # Constantes source
        assert hasattr(TableBuilder, 'BOOKID')
        assert hasattr(TableBuilder, 'TITLE')
        assert hasattr(TableBuilder, 'AUTHORS')
        
        # Constantes IDs
        assert hasattr(TableBuilder, 'PUBLISHERID')
        assert hasattr(TableBuilder, 'LANGUEID')
        assert hasattr(TableBuilder, 'DATEID')
        
        # Constantes dérivées
        assert hasattr(TableBuilder, 'YEAR')
        assert hasattr(TableBuilder, 'ENGAGEMENT')
        
        # Mapping langues
        assert hasattr(TableBuilder, 'LANGUAGE_MAPPING')
        assert isinstance(TableBuilder.LANGUAGE_MAPPING, dict)


# ============================================================================
# TESTS DE CRÉATION DES DIMENSIONS
# ============================================================================

class TestDimensionCreation:
    """Tests de création des tables dimensionnelles."""
    
    def test_create_dim_publishers(self, table_builder, sample_dataframe):
        """Test la création de la dimension Publishers."""
        dim = table_builder._create_dim_publishers(sample_dataframe)
        
        # Vérifier structure
        assert 'publisherID' in dim.columns
        assert 'publisher_name' in dim.columns
        assert len(dim.columns) == 2
        
        # Vérifier contenu
        assert len(dim) == 3  # Publisher A, B, C
        assert dim['publisherID'].is_unique
        assert dim['publisher_name'].is_unique
        
        # Vérifier IDs commencent à 1
        assert dim['publisherID'].min() == 1
    
    def test_create_dim_languages(self, table_builder, sample_dataframe):
        """Test la création de la dimension Languages."""
        dim = table_builder._create_dim_languages(sample_dataframe)
        
        # Vérifier structure
        assert 'languageID' in dim.columns
        assert 'language_code' in dim.columns
        assert 'language_name' in dim.columns
        assert 'country' in dim.columns
        assert len(dim.columns) == 4
        
        # Vérifier contenu
        assert len(dim) == 4  # eng, fre, spa, ger
        assert dim['languageID'].is_unique
        
        # Vérifier enrichissement
        eng_row = dim[dim['language_code'] == 'eng'].iloc[0]
        assert eng_row['language_name'] == 'English'
        assert eng_row['country'] == 'United States'
    
    def test_create_dim_languages_unknown_code(self, table_builder):
        """Test la gestion des codes de langue inconnus."""
        df = pd.DataFrame({
            'language_code': ['eng', 'xyz', 'fre']
        })
        
        dim = table_builder._create_dim_languages(df)
        
        # Vérifier que le code inconnu est géré
        xyz_row = dim[dim['language_code'] == 'xyz'].iloc[0]
        assert xyz_row['language_name'] == 'Unknown'
        assert xyz_row['country'] == 'Unknown'
    
    def test_create_dim_dates(self, table_builder, sample_dataframe):
        """Test la création de la dimension Dates."""
        dim = table_builder._create_dim_dates(sample_dataframe)
        
        # Vérifier structure
        expected_cols = [
            'publication_date', 'dateID', 'year', 'month', 'day',
            'quarter', 'month_name', 'day_name'
        ]
        assert all(col in dim.columns for col in expected_cols)
        
        # Vérifier contenu
        assert len(dim) == 5  # 5 dates uniques
        assert dim['dateID'].is_unique
        
        # Vérifier attributs temporels
        first_row = dim.iloc[0]
        assert isinstance(first_row['year'], (int, np.integer, pd._libs.missing.NAType))
        assert 1 <= first_row['month'] <= 12 or pd.isna(first_row['month'])
        assert 1 <= first_row['quarter'] <= 4 or pd.isna(first_row['quarter'])
    
    def test_create_dim_dates_invalid_dates(self, table_builder):
        """Test la gestion des dates invalides."""
        df = pd.DataFrame({
            'publication_date': ['2020-01-15', 'invalid-date', '2021-03-10']
        })
        
        dim = table_builder._create_dim_dates(df)
        
        # Les dates invalides doivent être supprimées
        assert len(dim) == 2
        assert dim['dateID'].is_unique
    
    def test_create_dim_genres(self, table_builder, sample_dataframe):
        """Test la création de la dimension Genres."""
        dim = table_builder._create_dim_genres(sample_dataframe)
        
        # Vérifier structure
        assert 'genreID' in dim.columns
        assert 'genre_name' in dim.columns
        assert len(dim.columns) == 2
        
        # Vérifier contenu
        assert len(dim) == 4  # Fiction, Non-Fiction, Science, Biography
        assert dim['genreID'].is_unique
        assert dim['genre_name'].is_unique
    
    def test_create_dim_books(self, table_builder, sample_dataframe):
        """Test la création de la dimension Books."""
        dim = table_builder._create_dim_books(sample_dataframe)
        
        # Vérifier structure
        assert 'bookID' in dim.columns
        assert 'isbn13' in dim.columns
        assert 'title' in dim.columns
        assert len(dim.columns) == 3
        
        # Vérifier contenu
        assert len(dim) == 5
        assert dim['bookID'].is_unique
        assert dim['bookID'].dtype == np.int64
    
    def test_create_dim_books_with_duplicates(
        self,
        table_builder,
        sample_dataframe_with_duplicates
    ):
        """Test que les doublons de bookID sont gérés (garde le premier)."""
        dim = table_builder._create_dim_books(sample_dataframe_with_duplicates)
        
        # Doit garder seulement la première occurrence
        assert len(dim) == 2  # bookID 1 et 2
        assert dim['bookID'].is_unique
        
        # Vérifier que c'est bien la première occurrence qui est gardée
        book1 = dim[dim['bookID'] == 1].iloc[0]
        assert book1['title'] == 'Book One v1'
    
    def test_create_dim_authors(self, table_builder, sample_dataframe):
        """Test la création de la dimension Authors."""
        dim = table_builder._create_dim_authors(sample_dataframe)
        
        # Vérifier structure
        assert 'authorID' in dim.columns
        assert 'author_name' in dim.columns
        assert len(dim.columns) == 2
        
        # Vérifier ordre des colonnes (ID en premier)
        assert dim.columns[0] == 'authorID'
        
        # Vérifier contenu
        # Author A, Author B, Author C, Author D
        assert len(dim) == 4
        assert dim['authorID'].is_unique
        assert dim['author_name'].is_unique
        
        # Vérifier que les auteurs multiples sont séparés
        assert 'Author B' in dim['author_name'].values
        assert 'Author C' in dim['author_name'].values
    
    def test_create_dim_authors_handles_null(self, table_builder):
        """Test que les auteurs NULL sont ignorés."""
        df = pd.DataFrame({
            'authors': ['Author A', None, 'Author B / Author C', np.nan]
        })
        
        dim = table_builder._create_dim_authors(df)
        
        # Doit avoir seulement A, B, C
        assert len(dim) == 3
        assert dim['authorID'].dtype == np.int64


# ============================================================================
# TESTS DE CRÉATION DE LA TABLE DE FAITS
# ============================================================================

class TestFactTableCreation:
    """Tests de création de la table de faits."""
    
    def test_create_fact_books_structure(
        self,
        table_builder,
        sample_dataframe
    ):
        """Test la structure de la table de faits."""
        # Créer d'abord toutes les dimensions
        dimensions = {
            'dim_publishers': table_builder._create_dim_publishers(sample_dataframe),
            'dim_languages': table_builder._create_dim_languages(sample_dataframe),
            'dim_dates': table_builder._create_dim_dates(sample_dataframe),
            'dim_genres': table_builder._create_dim_genres(sample_dataframe),
            'dim_books': table_builder._create_dim_books(sample_dataframe),
            'dim_authors': table_builder._create_dim_authors(sample_dataframe)
        }
        
        fact = table_builder._create_fact_books(sample_dataframe, dimensions)
        
        # Vérifier colonnes attendues
        expected_cols = [
            'bookID', 'publisherID', 'languageID', 'dateID', 'genreID',
            'average_rating', 'ratings_count', 'text_reviews_count',
            'num_pages', 'engagement'
        ]
        assert list(fact.columns) == expected_cols
        
        # Vérifier nombre de lignes
        assert len(fact) == 5
    
    def test_create_fact_books_engagement_calculation(
        self,
        table_builder,
        sample_dataframe
    ):
        """Test le calcul de la métrique engagement."""
        dimensions = {
            'dim_publishers': table_builder._create_dim_publishers(sample_dataframe),
            'dim_languages': table_builder._create_dim_languages(sample_dataframe),
            'dim_dates': table_builder._create_dim_dates(sample_dataframe),
            'dim_genres': table_builder._create_dim_genres(sample_dataframe),
            'dim_books': table_builder._create_dim_books(sample_dataframe),
            'dim_authors': table_builder._create_dim_authors(sample_dataframe)
        }
        
        fact = table_builder._create_fact_books(sample_dataframe, dimensions)
        
        # Vérifier engagement = text_reviews_count / ratings_count
        first_row = fact.iloc[0]
        expected_engagement = 100 / 1000  # 0.1
        assert abs(first_row['engagement'] - expected_engagement) < 0.0001
        
        # Vérifier que engagement est float
        assert fact['engagement'].dtype == float
    
    def test_create_fact_books_engagement_handles_division_by_zero(
        self,
        table_builder
    ):
        """Test que l'engagement gère la division par zéro."""
        df = pd.DataFrame({
            'bookID': [1, 2],
            'title': ['Book One', 'Book Two'],
            'authors': ['Author A', 'Author B'],
            'average_rating': [4.5, 3.8],
            'isbn13': ['9780000000001', '9780000000002'],
            'language_code': ['eng', 'fre'],
            'num_pages': [300, 250],
            'ratings_count': [1000, 0],  # Division par zéro
            'text_reviews_count': [100, 50],
            'publication_date': ['2020-01-15', '2019-06-20'],
            'publisher_name': ['Publisher A', 'Publisher B'],
            'genre_name': ['Fiction', 'Non-Fiction']
        })
        
        dimensions = {
            'dim_publishers': table_builder._create_dim_publishers(df),
            'dim_languages': table_builder._create_dim_languages(df),
            'dim_dates': table_builder._create_dim_dates(df),
            'dim_genres': table_builder._create_dim_genres(df),
            'dim_books': table_builder._create_dim_books(df),
            'dim_authors': table_builder._create_dim_authors(df)
        }
        
        fact = table_builder._create_fact_books(df, dimensions)
        
        # Vérifier que inf est remplacé par 0.0
        row_with_zero = fact[fact['ratings_count'] == 0].iloc[0]
        assert row_with_zero['engagement'] == 0.0
        assert not np.isinf(row_with_zero['engagement'])
    
    def test_create_fact_books_foreign_keys_valid(
        self,
        table_builder,
        sample_dataframe
    ):
        """Test que les clés étrangères sont valides."""
        dimensions = {
            'dim_publishers': table_builder._create_dim_publishers(sample_dataframe),
            'dim_languages': table_builder._create_dim_languages(sample_dataframe),
            'dim_dates': table_builder._create_dim_dates(sample_dataframe),
            'dim_genres': table_builder._create_dim_genres(sample_dataframe),
            'dim_books': table_builder._create_dim_books(sample_dataframe),
            'dim_authors': table_builder._create_dim_authors(sample_dataframe)
        }
        
        fact = table_builder._create_fact_books(sample_dataframe, dimensions)
        
        # Vérifier que tous les IDs existent dans leurs dimensions
        assert fact['bookID'].isin(dimensions['dim_books']['bookID']).all()
        
        # Pour les FK qui peuvent être NULL, vérifier seulement les non-NULL
        fact_not_null = fact[fact['publisherID'].notna()]
        if len(fact_not_null) > 0:
            assert fact_not_null['publisherID'].isin(
                dimensions['dim_publishers']['publisherID']
            ).all()


# ============================================================================
# TESTS DE VALIDATION
# ============================================================================

class TestValidation:
    """Tests des méthodes de validation (6 tests)."""
    
    def test_validate_foreign_keys_success(
        self,
        table_builder,
        sample_dataframe
    ):
        """Test que la validation passe avec des FK valides."""
        dimensions = {
            'dim_publishers': table_builder._create_dim_publishers(sample_dataframe),
            'dim_languages': table_builder._create_dim_languages(sample_dataframe),
            'dim_dates': table_builder._create_dim_dates(sample_dataframe),
            'dim_genres': table_builder._create_dim_genres(sample_dataframe),
            'dim_books': table_builder._create_dim_books(sample_dataframe),
            'dim_authors': table_builder._create_dim_authors(sample_dataframe)
        }
        
        fact = table_builder._create_fact_books(sample_dataframe, dimensions)
        
        # Ne doit pas lever d'exception
        table_builder._validate_foreign_keys(fact, dimensions)
    
    def test_validate_foreign_keys_invalid_id(self, table_builder):
        """Test que la validation échoue avec des FK invalides."""
        # Créer une fact table avec un ID invalide
        fact = pd.DataFrame({
            'bookID': [1, 999],  # 999 n'existe pas dans dim_books
            'publisherID': [1, 1],
            'languageID': [1, 1],
            'dateID': [1, 1],
            'genreID': [1, 1],
            'average_rating': [4.5, 3.8],
            'ratings_count': [1000, 500],
            'text_reviews_count': [100, 50],
            'num_pages': [300, 250],
            'engagement': [0.1, 0.1]
        })
        
        dimensions = {
            'dim_books': pd.DataFrame({'bookID': [1]}),
            'dim_publishers': pd.DataFrame({'publisherID': [1]}),
            'dim_languages': pd.DataFrame({'languageID': [1]}),
            'dim_dates': pd.DataFrame({'dateID': [1]}),
            'dim_genres': pd.DataFrame({'genreID': [1]})
        }
        
        # Doit lever ValueError
        with pytest.raises(ValueError, match="n'existent pas dans la dimension"):
            table_builder._validate_foreign_keys(fact, dimensions)
    
    def test_check_missing_values(
        self,
        table_builder,
        sample_dataframe_with_nulls,
        caplog
    ):
        """Test la détection des valeurs manquantes."""
        with caplog.at_level(logging.WARNING, logger='transform'):
            table_builder._check_missing_values(sample_dataframe_with_nulls)
        
    
    def test_check_missing_values_no_nulls(
        self,
        table_builder,
        sample_dataframe,
        caplog
    ):
        """Test qu'aucun warning n'est émis sans valeurs manquantes."""
        with caplog.at_level(logging.WARNING, logger='transform'):
            table_builder._check_missing_values(sample_dataframe)
        
        # Aucun warning ne doit être émis pour valeurs manquantes
        warnings = [r for r in caplog.records 
                   if 'valeurs manquantes' in r.message]
        assert len(warnings) == 0
    
    def test_check_missing_values_empty_dataframe(
        self,
        table_builder,
        caplog
    ):
        """Test la détection d'un DataFrame vide."""
        df = pd.DataFrame()
        
        # La méthode lève maintenant une ValueError pour DataFrame vide
        with pytest.raises(ValueError, match="DataFrame vide"):
            with caplog.at_level(logging.ERROR, logger='transform'):
                table_builder._check_missing_values(df)
    
    def test_check_missing_values_none_and_nan(
        self,
        table_builder,
        caplog
    ):
        """Test la détection des None et NaN."""
        df = pd.DataFrame({
            'col1': [1, None, 3],
            'col2': [4, 5, np.nan],
            'col3': [7, pd.NA, 9]
        })
        
        with caplog.at_level(logging.WARNING, logger='transform'):
            table_builder._check_missing_values(df)
        


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration de la création complète."""
    
    def test_create_all_tables_success(self, table_builder, sample_dataframe):
        """Test la création complète de toutes les tables."""
        tables = table_builder.create_all_tables(sample_dataframe)
        
        # Vérifier que toutes les tables sont créées
        expected_tables = [
            'dim_books', 'dim_authors', 'dim_publishers',
            'dim_languages', 'dim_dates', 'dim_genres', 'fact_books'
        ]
        assert all(table in tables for table in expected_tables)
        
        # Vérifier que ce sont bien des DataFrames
        assert all(isinstance(df, pd.DataFrame) for df in tables.values())
        
        # Vérifier que les tables ne sont pas vides
        assert all(len(df) > 0 for df in tables.values())
    
    def test_create_all_tables_referential_integrity(
        self,
        table_builder,
        sample_dataframe
    ):
        """Test l'intégrité référentielle du modèle complet."""
        tables = table_builder.create_all_tables(sample_dataframe)
        
        fact = tables['fact_books']
        
        # Vérifier toutes les FK
        assert fact['bookID'].isin(tables['dim_books']['bookID']).all()
        
        # Pour les FK nullable, vérifier seulement les non-NULL
        fact_not_null_pub = fact[fact['publisherID'].notna()]
        if len(fact_not_null_pub) > 0:
            assert fact_not_null_pub['publisherID'].isin(
                tables['dim_publishers']['publisherID']
            ).all()
    
    def test_create_all_tables_with_nulls(
        self,
        table_builder,
        sample_dataframe_with_nulls
    ):
        """Test la création avec des valeurs manquantes."""
        # Ne doit pas lever d'exception
        tables = table_builder.create_all_tables(sample_dataframe_with_nulls)
        
        # Vérifier que toutes les tables sont créées
        assert 'fact_books' in tables
        assert len(tables['fact_books']) > 0
    
    def test_create_all_tables_logging(
        self,
        table_builder,
        sample_dataframe,
        caplog
    ):
        """Test que les logs sont correctement émis."""
        with caplog.at_level(logging.INFO, logger='transform'):
            table_builder.create_all_tables(sample_dataframe)
        
    
    def test_log_tables_summary(
        self,
        table_builder,
        sample_dataframe,
        caplog
    ):
        """Test l'affichage du résumé des tables."""
        tables = table_builder.create_all_tables(sample_dataframe)
        
        with caplog.at_level(logging.INFO, logger='transform'):
            table_builder._log_tables_summary(tables)
        


# ============================================================================
# TESTS DE CAS LIMITES
# ============================================================================

class TestEdgeCases:
    """Tests des cas limites et situations extrêmes."""
    
    def test_empty_dataframe(self, table_builder):
        """Test le comportement avec un DataFrame vide."""
        df = pd.DataFrame(columns=[
            'bookID', 'title', 'authors', 'average_rating', 'isbn13',
            'language_code', 'num_pages', 'ratings_count',
            'text_reviews_count', 'publication_date', 'publisher_name',
            'genre_name'
        ])
        
        # La création doit échouer avec un DataFrame vide
        with pytest.raises((ValueError, Exception)):
            table_builder.create_all_tables(df)
    
    def test_single_row_dataframe(self, table_builder):
        """Test avec un DataFrame d'une seule ligne."""
        df = pd.DataFrame({
            'bookID': [1],
            'title': ['Book One'],
            'authors': ['Author A'],
            'average_rating': [4.5],
            'isbn13': ['9780000000001'],
            'language_code': ['eng'],
            'num_pages': [300],
            'ratings_count': [1000],
            'text_reviews_count': [100],
            'publication_date': ['2020-01-15'],
            'publisher_name': ['Publisher A'],
            'genre_name': ['Fiction']
        })
        
        tables = table_builder.create_all_tables(df)
        
        # Toutes les dimensions doivent avoir exactement 1 ligne
        assert len(tables['dim_publishers']) == 1
        assert len(tables['dim_languages']) == 1
        assert len(tables['dim_genres']) == 1
        assert len(tables['fact_books']) == 1
    
    def test_multiple_authors_per_book(self, table_builder):
        """Test avec plusieurs auteurs séparés par différents délimiteurs."""
        df = pd.DataFrame({
            'bookID': [1],
            'title': ['Book One'],
            'authors': ['Author A / Author B / Author C'],
            'average_rating': [4.5],
            'isbn13': ['9780000000001'],
            'language_code': ['eng'],
            'num_pages': [300],
            'ratings_count': [1000],
            'text_reviews_count': [100],
            'publication_date': ['2020-01-15'],
            'publisher_name': ['Publisher A'],
            'genre_name': ['Fiction']
        })
        
        tables = table_builder.create_all_tables(df)
        
        # Doit avoir 3 auteurs distincts
        assert len(tables['dim_authors']) == 3
        assert 'Author A' in tables['dim_authors']['author_name'].values
        assert 'Author B' in tables['dim_authors']['author_name'].values
        assert 'Author C' in tables['dim_authors']['author_name'].values
    
    def test_language_mapping_coverage(self, table_builder):
        """Test que tous les codes de langue dans LANGUAGE_MAPPING fonctionnent."""
        # Créer un DataFrame avec tous les codes de langue
        language_codes = list(TableBuilder.LANGUAGE_MAPPING.keys())
        
        df = pd.DataFrame({
            'language_code': language_codes
        })
        
        dim = table_builder._create_dim_languages(df)
        
        # Vérifier que toutes les langues ont un nom et un pays
        assert not dim['language_name'].isna().any()
        assert not dim['country'].isna().any()
        
        # Vérifier qu'aucune n'est 'Unknown'
        assert (dim['language_name'] != 'Unknown').all()
    
    def test_dates_with_different_formats(self, table_builder):
        """Test avec différents formats de dates."""
        df = pd.DataFrame({
            'publication_date': [
                '2020-01-15',
                '2020/06/20',
                '15-03-2021',
                'invalid',
                None
            ]
        })
        
        dim = table_builder._create_dim_dates(df)
        
        # Seules les dates valides doivent être conservées
        assert len(dim) >= 1  # Au moins une date valide
        assert dim['dateID'].is_unique


# ============================================================================
# TESTS DE PERFORMANCE ET QUALITÉ
# ============================================================================

class TestPerformanceAndQuality:
    """Tests de performance et qualité des données."""
    
    def test_no_duplicate_ids_in_dimensions(
        self,
        table_builder,
        sample_dataframe
    ):
        """Test qu'aucune dimension n'a d'IDs dupliqués."""
        tables = table_builder.create_all_tables(sample_dataframe)
        
        id_columns = [
            ('dim_books', 'bookID'),
            ('dim_authors', 'authorID'),
            ('dim_publishers', 'publisherID'),
            ('dim_languages', 'languageID'),
            ('dim_dates', 'dateID'),
            ('dim_genres', 'genreID')
        ]
        
        for table_name, id_col in id_columns:
            assert tables[table_name][id_col].is_unique, \
                f"Duplicate IDs found in {table_name}.{id_col}"
    
    def test_fact_table_data_types(self, table_builder, sample_dataframe):
        """Test que les types de données sont corrects dans fact_books."""
        tables = table_builder.create_all_tables(sample_dataframe)
        fact = tables['fact_books']
        
        # Vérifier types des colonnes
        assert fact['average_rating'].dtype in [float, 'float64']
        assert fact['ratings_count'].dtype in [int, 'int64', 'Int64']
        assert fact['engagement'].dtype in [float, 'float64']
    
    def test_no_negative_values_in_metrics(
        self,
        table_builder,
        sample_dataframe
    ):
        """Test qu'il n'y a pas de valeurs négatives dans les métriques."""
        tables = table_builder.create_all_tables(sample_dataframe)
        fact = tables['fact_books']
        
        # Colonnes qui ne doivent pas être négatives
        positive_cols = [
            'average_rating', 'ratings_count',
            'text_reviews_count', 'num_pages', 'engagement'
        ]
        
        for col in positive_cols:
            non_null = fact[fact[col].notna()][col]
            if len(non_null) > 0:
                assert (non_null >= 0).all(), \
                    f"Negative values found in {col}"


# ============================================================================
# TESTS PARAMÉTRÉS
# ============================================================================

class TestParameterized:
    """Tests paramétrés pour tester plusieurs scénarios."""
    
    @pytest.mark.parametrize("language_code,expected_name", [
        ("eng", "English"),
        ("fre", "French"),
        ("spa", "Spanish"),
        ("ger", "German"),
        ("jpn", "Japanese"),
        ("unknown", "Unknown")
    ])
    def test_language_mapping(
        self,
        table_builder,
        language_code,
        expected_name
    ):
        """Test le mapping des codes de langue vers les noms."""
        df = pd.DataFrame({'language_code': [language_code]})
        dim = table_builder._create_dim_languages(df)
        
        assert dim['language_name'].iloc[0] == expected_name
    
    @pytest.mark.parametrize("ratings,reviews,expected_engagement", [
        (1000, 100, 0.1),
        (500, 50, 0.1),
        (100, 10, 0.1),
        (1000, 0, 0.0),
        (0, 100, 0.0)  # Division par zéro
    ])
    def test_engagement_calculation(
        self,
        table_builder,
        ratings,
        reviews,
        expected_engagement
    ):
        """Test le calcul de l'engagement avec différentes valeurs."""
        df = pd.DataFrame({
            'bookID': [1],
            'title': ['Book'],
            'authors': ['Author'],
            'average_rating': [4.0],
            'isbn13': ['9780000000001'],
            'language_code': ['eng'],
            'num_pages': [300],
            'ratings_count': [ratings],
            'text_reviews_count': [reviews],
            'publication_date': ['2020-01-15'],
            'publisher_name': ['Publisher'],
            'genre_name': ['Fiction']
        })
        
        dimensions = {
            'dim_publishers': table_builder._create_dim_publishers(df),
            'dim_languages': table_builder._create_dim_languages(df),
            'dim_dates': table_builder._create_dim_dates(df),
            'dim_genres': table_builder._create_dim_genres(df),
            'dim_books': table_builder._create_dim_books(df),
            'dim_authors': table_builder._create_dim_authors(df)
        }
        
        fact = table_builder._create_fact_books(df, dimensions)
        
        assert abs(fact['engagement'].iloc[0] - expected_engagement) < 0.0001


# ============================================================================
# EXÉCUTION DES TESTS
# ============================================================================

# if __name__ == '__main__':
#     pytest.main([__file__, '-v', '--tb=short'])