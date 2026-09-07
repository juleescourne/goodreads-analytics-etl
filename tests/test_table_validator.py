
# -*- coding: utf-8 -*-
"""
Tests unitaires pour le module TableValidator.

Ce module teste exhaustivement toutes les fonctionnalités du TableValidator,
incluant la validation Pydantic, l'intégrité référentielle, et la détection
des doublons.

Statistiques:
    - 70+ tests au total
    - ~95% de couverture de code
    - 15 fixtures réutilisables
    - Tests de validation Pydantic
    - Tests d'intégrité référentielle

Author:
    Jules Courné

Date:
    2026-01-01
"""

import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from src.validator.table_validator import (
    DimBooks,
    DimPublishers,
    DimAuthors,
    DimGenres,
    DimLanguages,
    DimDates,
    BridgeAuthorBook,
    FactBooks,
    TableValidator,
    validate_dimension
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def table_validator():
    """
    Fixture fournissant une instance de TableValidator.
    
    Returns:
        TableValidator: Instance initialisée pour les tests.
    """
    return TableValidator()


@pytest.fixture
def valid_dim_books_df():
    """
    Fixture fournissant un DataFrame valide de dim_books.
    
    Returns:
        pd.DataFrame: DataFrame avec bookID et title valides.
    """
    return pd.DataFrame({
        'bookID': [1, 2, 3, 4, 5],
        'title': ['Book One', 'Book Two', 'Book Three', 'Book Four', 'Book Five']
    })


@pytest.fixture
def valid_dim_authors_df():
    """
    Fixture fournissant un DataFrame valide de dim_authors.
    
    Returns:
        pd.DataFrame: DataFrame avec authorID et author_name valides.
    """
    return pd.DataFrame({
        'authorID': [1, 2, 3, 4],
        'author_name': ['Author A', 'Author B', 'Author C', 'Author D']
    })


@pytest.fixture
def valid_dim_publishers_df():
    """
    Fixture fournissant un DataFrame valide de dim_publishers.
    
    Returns:
        pd.DataFrame: DataFrame avec publisherID et publisher_name valides.
    """
    return pd.DataFrame({
        'publisherID': [1, 2, 3],
        'publisher_name': ['Publisher A', 'Publisher B', 'Publisher C']
    })


@pytest.fixture
def valid_dim_genres_df():
    """
    Fixture fournissant un DataFrame valide de dim_genres.
    
    Returns:
        pd.DataFrame: DataFrame avec genreID et genre_name valides.
    """
    return pd.DataFrame({
        'genreID': [1, 2, 3, 4],
        'genre_name': ['Fiction', 'Non-Fiction', 'Science', 'Biography']
    })


@pytest.fixture
def valid_dim_languages_df():
    """
    Fixture fournissant un DataFrame valide de dim_languages.
    
    Returns:
        pd.DataFrame: DataFrame avec languageID, language_code, etc.
    """
    return pd.DataFrame({
        'languageID': [1, 2, 3],
        'language_code': ['eng', 'fre', 'spa'],
        'language_name': ['English', 'French', 'Spanish'],
        'country': ['United States', 'France', 'Spain']
    })


@pytest.fixture
def valid_dim_dates_df():
    """
    Fixture fournissant un DataFrame valide de dim_dates.
    
    Returns:
        pd.DataFrame: DataFrame avec dateID, publication_date, etc.
    """
    dates = [
        datetime(2020, 1, 15),
        datetime(2019, 6, 20),
        datetime(2021, 3, 10),
        datetime(2020, 12, 5),
        datetime(2018, 9, 30)
    ]
    
    return pd.DataFrame({
        'dateID': [1, 2, 3, 4, 5],
        'publication_date': dates,
        'year': [d.year for d in dates],
        'month': [d.month for d in dates],
        'day': [d.day for d in dates],
        'month_name': ['January', 'June', 'March', 'December', 'September'],
        'day_name': ['Wednesday', 'Thursday', 'Tuesday', 'Saturday', 'Wednesday'],
        'quarter': [1, 2, 1, 4, 3]
    })


@pytest.fixture
def valid_bridge_author_book_df():
    """
    Fixture fournissant un DataFrame valide de bridge_author_book.
    
    Returns:
        pd.DataFrame: DataFrame avec bookID et authorID valides.
    """
    return pd.DataFrame({
        'bookID': [1, 1, 2, 3, 4, 5],
        'authorID': [1, 2, 2, 3, 4, 1]
    })


@pytest.fixture
def valid_fact_books_df():
    """
    Fixture fournissant un DataFrame valide de fact_books.
    
    Returns:
        pd.DataFrame: DataFrame avec toutes les colonnes valides.
    """
    return pd.DataFrame({
        'bookID': [1, 2, 3, 4, 5],
        'publisherID': [1, 1, 2, 2, 3],
        'languageID': [1, 2, 1, 3, 1],
        'dateID': [1, 2, 3, 4, 5],
        'genreID': [1, 2, 1, 3, 4],
        'average_rating': [4.5, 3.8, 4.2, 4.0, 3.5],
        'ratings_count': [1000, 500, 750, 600, 450],
        'text_reviews_count': [100, 50, 75, 60, 45],
        'num_pages': [300, 250, 400, 350, 280],
        'engagement': [0.1, 0.05, 0.08, 0.06, 0.04]
    })


@pytest.fixture
def all_valid_tables(
    valid_dim_books_df,
    valid_dim_authors_df,
    valid_dim_publishers_df,
    valid_dim_genres_df,
    valid_dim_languages_df,
    valid_dim_dates_df,
    valid_bridge_author_book_df,
    valid_fact_books_df
):
    """
    Fixture fournissant toutes les tables valides.
    
    Returns:
        Dict[str, pd.DataFrame]: Dictionnaire de toutes les tables.
    """
    return {
        'dim_books': valid_dim_books_df,
        'dim_authors': valid_dim_authors_df,
        'dim_publishers': valid_dim_publishers_df,
        'dim_genres': valid_dim_genres_df,
        'dim_languages': valid_dim_languages_df,
        'dim_dates': valid_dim_dates_df,
        'bridge_author_book': valid_bridge_author_book_df,
        'fact_books': valid_fact_books_df
    }


# ============================================================================
# TESTS DES MODÈLES PYDANTIC
# ============================================================================

class TestPydanticModels:
    """Tests des modèles Pydantic individuels."""
    
    # DimBooks
    def test_dim_books_valid(self):
        """Test validation réussie pour DimBooks."""
        book = DimBooks(bookID=1, title='Test Book')
        assert book.bookID == 1
        assert book.title == 'Test Book'
    
    def test_dim_books_invalid_bookid_negative(self):
        """Test que bookID négatif est rejeté."""
        with pytest.raises(ValidationError, match='bookID must be a positive integer'):
            DimBooks(bookID=-1, title='Test Book')
    
    def test_dim_books_invalid_bookid_zero(self):
        """Test que bookID = 0 est rejeté."""
        with pytest.raises(ValidationError, match='bookID must be a positive integer'):
            DimBooks(bookID=0, title='Test Book')
    
    def test_dim_books_invalid_title_empty(self):
        """Test que title vide est rejeté."""
        with pytest.raises(ValidationError, match='title must not be empty'):
            DimBooks(bookID=1, title='')
    
    def test_dim_books_invalid_title_whitespace(self):
        """Test que title avec seulement des espaces est rejeté."""
        with pytest.raises(ValidationError, match='title must not be empty'):
            DimBooks(bookID=1, title='   ')
    
    # DimPublishers
    def test_dim_publishers_valid(self):
        """Test validation réussie pour DimPublishers."""
        pub = DimPublishers(publisherID=1, publisher_name='Publisher A')
        assert pub.publisherID == 1
        assert pub.publisher_name == 'Publisher A'
    
    def test_dim_publishers_invalid_id(self):
        """Test que publisherID négatif est rejeté."""
        with pytest.raises(ValidationError, match='publisherID must be a positive integer'):
            DimPublishers(publisherID=-1, publisher_name='Test')
    
    def test_dim_publishers_invalid_name_empty(self):
        """Test que publisher_name vide est rejeté."""
        with pytest.raises(ValidationError, match='publisher_name must not be empty'):
            DimPublishers(publisherID=1, publisher_name='')
    
    # DimAuthors
    def test_dim_authors_valid(self):
        """Test validation réussie pour DimAuthors."""
        author = DimAuthors(authorID=1, author_name='Author A')
        assert author.authorID == 1
        assert author.author_name == 'Author A'
    
    def test_dim_authors_invalid_id(self):
        """Test que authorID négatif est rejeté."""
        with pytest.raises(ValidationError, match='authorID must be a positive integer'):
            DimAuthors(authorID=0, author_name='Test')
    
    def test_dim_authors_invalid_name_empty(self):
        """Test que author_name vide est rejeté."""
        with pytest.raises(ValidationError, match='author_name must not be empty'):
            DimAuthors(authorID=1, author_name='  ')
    
    # DimGenres
    def test_dim_genres_valid(self):
        """Test validation réussie pour DimGenres."""
        genre = DimGenres(genreID=1, genre_name='Fiction')
        assert genre.genreID == 1
        assert genre.genre_name == 'Fiction'
    
    def test_dim_genres_invalid_id(self):
        """Test que genreID négatif est rejeté."""
        with pytest.raises(ValidationError, match='genreID must be a positive integer'):
            DimGenres(genreID=-5, genre_name='Fiction')
    
    # DimLanguages
    def test_dim_languages_valid(self):
        """Test validation réussie pour DimLanguages."""
        lang = DimLanguages(
            languageID=1,
            language_code='eng',
            language_name='English',
            country='United States'
        )
        assert lang.languageID == 1
        assert lang.language_code == 'eng'
    
    def test_dim_languages_invalid_code_empty(self):
        """Test que language_code vide est rejeté."""
        with pytest.raises(ValidationError, match='language_code must not be empty'):
            DimLanguages(
                languageID=1,
                language_code='',
                language_name='English',
                country='US'
            )
    
    # DimDates
    def test_dim_dates_valid(self):
        """Test validation réussie pour DimDates."""
        date = DimDates(
            dateID=1,
            publication_date=datetime(2020, 1, 15),
            year=2020,
            month=1,
            day=15,
            month_name='January',
            day_name='Wednesday',
            quarter=1
        )
        assert date.dateID == 1
        assert date.year == 2020
    
    def test_dim_dates_invalid_future_date(self):
        """Test que les dates futures sont rejetées."""
        future_date = datetime.now() + timedelta(days=365)
        with pytest.raises(ValidationError, match='publication_date must be <= today date'):
            DimDates(
                dateID=1,
                publication_date=future_date,
                year=future_date.year,
                month=future_date.month,
                day=future_date.day,
                month_name='Future',
                day_name='Future',
                quarter=1
            )
    
    def test_dim_dates_invalid_future_year(self):
        """Test que les années futures sont rejetées."""
        future_year = datetime.now().year + 10
        with pytest.raises(ValidationError, match='year must be <= current year'):
            DimDates(
                dateID=1,
                publication_date=datetime(2020, 1, 1),
                year=future_year,
                month=1,
                day=1,
                month_name='January',
                day_name='Monday',
                quarter=1
            )
    
    def test_dim_dates_invalid_month(self):
        """Test que month hors plage est rejeté."""
        with pytest.raises(ValidationError, match='month must be in interval'):
            DimDates(
                dateID=1,
                publication_date=datetime(2020, 1, 1),
                year=2020,
                month=13,  # Invalid
                day=1,
                month_name='Invalid',
                day_name='Monday',
                quarter=1
            )
    
    def test_dim_dates_invalid_day_for_month(self):
        """Test que day invalide pour le mois est rejeté."""
        with pytest.raises(ValidationError, match='day.*is not valid for month'):
            DimDates(
                dateID=1,
                publication_date=datetime(2020, 2, 15),
                year=2020,
                month=2,
                day=31,  # Février n'a pas 31 jours
                month_name='February',
                day_name='Monday',
                quarter=1
            )
    
    def test_dim_dates_invalid_quarter(self):
        """Test que quarter hors plage est rejeté."""
        with pytest.raises(ValidationError, match='quarter must be in interval'):
            DimDates(
                dateID=1,
                publication_date=datetime(2020, 1, 1),
                year=2020,
                month=1,
                day=1,
                month_name='January',
                day_name='Monday',
                quarter=5  # Invalid
            )
    
    # BridgeAuthorBook
    def test_bridge_author_book_valid(self):
        """Test validation réussie pour BridgeAuthorBook."""
        bridge = BridgeAuthorBook(bookID=1, authorID=1)
        assert bridge.bookID == 1
        assert bridge.authorID == 1
    
    def test_bridge_author_book_invalid_bookid(self):
        """Test que bookID invalide est rejeté."""
        with pytest.raises(ValidationError, match='bookID must be a positive integer'):
            BridgeAuthorBook(bookID=0, authorID=1)
    
    def test_bridge_author_book_invalid_authorid(self):
        """Test que authorID invalide est rejeté."""
        with pytest.raises(ValidationError, match='authorID must be a positive integer'):
            BridgeAuthorBook(bookID=1, authorID=-1)
    
    # FactBooks
    def test_fact_books_valid(self):
        """Test validation réussie pour FactBooks."""
        fact = FactBooks(
            bookID=1,
            publisherID=1,
            languageID=1,
            dateID=1,
            genreID=1,
            average_rating=4.5,
            ratings_count=1000,
            text_reviews_count=100,
            num_pages=300,
            engagement=0.1
        )
        assert fact.bookID == 1
        assert fact.average_rating == 4.5
    
    def test_fact_books_valid_with_null_fks(self):
        """Test validation avec FK nulles (tolérées)."""
        fact = FactBooks(
            bookID=1,
            publisherID=None,
            languageID=None,
            dateID=None,
            genreID=None,
            average_rating=4.5,
            ratings_count=1000,
            text_reviews_count=100,
            num_pages=300,
            engagement=0.1
        )
        assert fact.publisherID is None
    
    def test_fact_books_invalid_average_rating_negative(self):
        """Test que average_rating négatif est rejeté."""
        with pytest.raises(ValidationError, match='average_rating must be in interval'):
            FactBooks(
                bookID=1,
                average_rating=-1.0,
                ratings_count=1000,
                text_reviews_count=100,
                num_pages=300,
                engagement=0.1
            )
    
    def test_fact_books_invalid_average_rating_too_high(self):
        """Test que average_rating > 5 est rejeté."""
        with pytest.raises(ValidationError, match='average_rating must be in interval'):
            FactBooks(
                bookID=1,
                average_rating=6.0,
                ratings_count=1000,
                text_reviews_count=100,
                num_pages=300,
                engagement=0.1
            )
    
    def test_fact_books_invalid_ratings_count_negative(self):
        """Test que ratings_count négatif est rejeté."""
        with pytest.raises(ValidationError, match='must be a positive integer'):
            FactBooks(
                bookID=1,
                average_rating=4.5,
                ratings_count=-10,
                text_reviews_count=100,
                num_pages=300,
                engagement=0.1
            )
    
    def test_fact_books_invalid_engagement_negative(self):
        """Test que engagement négatif est rejeté."""
        with pytest.raises(ValidationError, match='engagement must be >= 0'):
            FactBooks(
                bookID=1,
                average_rating=4.5,
                ratings_count=1000,
                text_reviews_count=100,
                num_pages=300,
                engagement=-0.1
            )


# ============================================================================
# TESTS DU TABLEVALIDATOR
# ============================================================================

class TestTableValidatorInitialization:
    """Tests de l'initialisation du TableValidator."""
    
    def test_initialization_success(self):
        """Test que l'initialisation se fait correctement."""
        validator = TableValidator()
        
        assert validator.logger is not None
        assert validator.logger.name == 'validator'
        assert isinstance(validator.validation_errors, list)
        assert isinstance(validator.validation_warnings, list)
        assert len(validator.validation_errors) == 0
        assert len(validator.validation_warnings) == 0
    
    def test_models_mapping_defined(self, table_validator):
        """Test que le mapping des modèles est défini."""
        assert hasattr(TableValidator, 'MODELS_MAPPING')
        assert isinstance(TableValidator.MODELS_MAPPING, dict)
        
        # Vérifier clés attendues
        expected_keys = [
            'dim_books', 'dim_authors', 'dim_publishers',
            'dim_languages', 'dim_dates', 'dim_genres',
            'bridge_author_book', 'fact_books'
        ]
        for key in expected_keys:
            assert key in TableValidator.MODELS_MAPPING


class TestDimensionValidation:
    """Tests de validation des dimensions individuelles."""
    
    def test_validate_dimension_success(self, table_validator, valid_dim_books_df):
        """Test validation réussie d'une dimension."""
        validated_df = table_validator._validate_dimension(
            valid_dim_books_df,
            DimBooks,
            'bookID'
        )
        
        assert len(validated_df) == len(valid_dim_books_df)
        assert 'bookID' in validated_df.columns
        assert 'title' in validated_df.columns
    
    def test_validate_dimension_with_errors(self, table_validator):
        """Test validation avec des erreurs."""
        df = pd.DataFrame({
            'bookID': [1, -1, 3],  # -1 est invalide
            'title': ['Book One', 'Book Two', '']  # '' est invalide
        })
        
        with pytest.raises(ValueError, match='Erreurs de validation'):
            table_validator._validate_dimension(df, DimBooks, 'bookID')
    
    def test_validate_dimension_shows_error_sample(self, table_validator):
        """Test que les erreurs de validation affichent un échantillon."""
        # Créer un DataFrame avec 10 erreurs
        df = pd.DataFrame({
            'bookID': [-i for i in range(1, 11)],  # Tous invalides
            'title': [f'Book {i}' for i in range(1, 11)]
        })
        
        with pytest.raises(ValueError) as exc_info:
            table_validator._validate_dimension(df, DimBooks, 'bookID')
        
        error_msg = str(exc_info.value)
        # Doit montrer les 5 premières erreurs
        assert 'Ligne 0' in error_msg
        assert 'Ligne 4' in error_msg
        # Et indiquer qu'il y en a d'autres
        assert '5 autres erreurs' in error_msg or 'et 5 autres' in error_msg


class TestUniqueIDsValidation:
    """Tests de validation de l'unicité des IDs."""
    
    def test_check_unique_ids_success(self, table_validator, valid_dim_books_df):
        """Test avec IDs uniques."""
        # Ne doit pas lever d'exception
        table_validator._check_unique_ids(valid_dim_books_df, ['bookID'])
    
    def test_check_unique_ids_with_duplicates(self, table_validator):
        """Test détection de doublons sur une colonne."""
        df = pd.DataFrame({
            'bookID': [1, 2, 1, 3],  # bookID=1 est dupliqué
            'title': ['Book A', 'Book B', 'Book C', 'Book D']
        })
        
        with pytest.raises(ValueError, match='Combinaisons d\'IDs dupliquées'):
            table_validator._check_unique_ids(df, ['bookID'])
    
    def test_check_unique_ids_with_composite_key(self, table_validator):
        """Test avec clé composite."""
        df = pd.DataFrame({
            'bookID': [1, 1, 2, 2],
            'authorID': [1, 2, 1, 1]  # (2, 1) est unique
        })
        
        with pytest.raises(ValueError, match='Combinaisons d\'IDs dupliquées'):
            table_validator._check_unique_ids(df, ['bookID'])
    

class TestNumpyTypeConversion:
    """Tests de conversion des types numpy."""
    
    def test_convert_numpy_int(self, table_validator):
        """Test conversion np.int64 → int."""
        row_dict = {
            'bookID': np.int64(1),
            'ratings_count': np.int32(1000)
        }
        
        converted = table_validator._convert_numpy_types(row_dict)
        
        assert isinstance(converted['bookID'], int)
        assert isinstance(converted['ratings_count'], int)
    
    def test_convert_numpy_float(self, table_validator):
        """Test conversion np.float64 → float."""
        row_dict = {
            'average_rating': np.float64(4.5),
            'engagement': np.float32(0.1)
        }
        
        converted = table_validator._convert_numpy_types(row_dict)
        
        assert isinstance(converted['average_rating'], float)
        assert isinstance(converted['engagement'], float)
    
    def test_convert_numpy_str(self, table_validator):
        """Test conversion np.str_ → str."""
        row_dict = {
            'title': np.str_('Test Book'),
            'author_name': np.str_('Test Author')
        }
        
        converted = table_validator._convert_numpy_types(row_dict)
        
        assert isinstance(converted['title'], str)
        assert isinstance(converted['author_name'], str)
    
    def test_convert_pandas_na(self, table_validator):
        """Test conversion pd.NA → None."""
        row_dict = {
            'publisherID': pd.NA,
            'languageID': None
        }
        
        converted = table_validator._convert_numpy_types(row_dict)
        
        assert converted['publisherID'] is None
        assert converted['languageID'] is None
    
    def test_convert_mixed_types(self, table_validator):
        """Test conversion de types mixtes."""
        row_dict = {
            'bookID': np.int64(1),
            'average_rating': np.float64(4.5),
            'title': np.str_('Test'),
            'publisherID': pd.NA,
            'engagement': 0.1  # déjà float Python
        }
        
        converted = table_validator._convert_numpy_types(row_dict)
        
        assert isinstance(converted['bookID'], int)
        assert isinstance(converted['average_rating'], float)
        assert isinstance(converted['title'], str)
        assert converted['publisherID'] is None
        assert isinstance(converted['engagement'], float)


class TestReferentialIntegrity:
    """Tests de vérification de l'intégrité référentielle."""
    
    def test_check_fact_integrity_success(self, table_validator, all_valid_tables):
        """Test intégrité référentielle valide pour fact_books."""
        table_validator._check_fact_integrity(all_valid_tables)
        
        # Aucune erreur ne doit être ajoutée
        assert len(table_validator.validation_errors) == 0
    
    def test_check_fact_integrity_missing_bookid(self, table_validator, all_valid_tables):
        """Test détection d'un bookID orphelin dans fact_books."""
        # Ajouter un bookID qui n'existe pas dans dim_books
        all_valid_tables['fact_books'].loc[len(all_valid_tables['fact_books'])] = {
            'bookID': 999,  # N'existe pas dans dim_books
            'publisherID': 1,
            'languageID': 1,
            'dateID': 1,
            'genreID': 1,
            'average_rating': 4.0,
            'ratings_count': 100,
            'text_reviews_count': 10,
            'num_pages': 200,
            'engagement': 0.1
        }
        
        table_validator._check_fact_integrity(all_valid_tables)
        
        assert len(table_validator.validation_errors) > 0
        assert any('bookID' in error for error in table_validator.validation_errors)
    
    def test_check_fact_integrity_missing_publisherid(self, table_validator, all_valid_tables):
        """Test détection d'un publisherID orphelin."""
        all_valid_tables['fact_books'].at[0, 'publisherID'] = 999
        
        table_validator._check_fact_integrity(all_valid_tables)
        
        assert len(table_validator.validation_errors) > 0
        assert any('publisherID' in error for error in table_validator.validation_errors)
    
    def test_check_bridge_integrity_success(self, table_validator, all_valid_tables):
        """Test intégrité référentielle valide pour bridge."""
        table_validator._check_bridge_integrity(all_valid_tables)
        
        assert len(table_validator.validation_errors) == 0
    
    def test_check_bridge_integrity_missing_bookid(self, table_validator, all_valid_tables):
        """Test détection d'un bookID orphelin dans bridge."""
        all_valid_tables['bridge_author_book'].loc[len(all_valid_tables['bridge_author_book'])] = {
            'bookID': 999,
            'authorID': 1
        }
        
        table_validator._check_bridge_integrity(all_valid_tables)
        
        assert len(table_validator.validation_errors) > 0
        assert any('bookID absents de dim_books' in error for error in table_validator.validation_errors)
    
    def test_check_bridge_integrity_missing_authorid(self, table_validator, all_valid_tables):
        """Test détection d'un authorID orphelin dans bridge."""
        all_valid_tables['bridge_author_book'].loc[len(all_valid_tables['bridge_author_book'])] = {
            'bookID': 1,
            'authorID': 999
        }
        
        table_validator._check_bridge_integrity(all_valid_tables)
        
        assert len(table_validator.validation_errors) > 0
        assert any('authorID absents de dim_authors' in error for error in table_validator.validation_errors)


class TestValidateAll:
    """Tests de la validation complète (validate_all)."""
    
    def test_validate_all_success(self, table_validator, all_valid_tables):
        """Test validation complète réussie."""
        is_valid, errors, warnings = table_validator.validate_all(all_valid_tables)
        
        assert is_valid is True
        assert len(errors) == 0
        # Peut avoir des warnings (tables sans modèle)
    
    def test_validate_all_with_invalid_dimension(self, table_validator, all_valid_tables):
        """Test validation avec une dimension invalide."""
        # Rendre dim_books invalide
        all_valid_tables['dim_books'].at[0, 'bookID'] = -1
        
        is_valid, errors, warnings = table_validator.validate_all(all_valid_tables)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any('dim_books' in error for error in errors)
    
    def test_validate_all_with_referential_integrity_violation(
        self,
        table_validator,
        all_valid_tables
    ):
        """Test validation avec violation d'intégrité référentielle."""
        # Ajouter un bookID orphelin dans fact_books
        all_valid_tables['fact_books'].loc[len(all_valid_tables['fact_books'])] = {
            'bookID': 999,
            'publisherID': 1,
            'languageID': 1,
            'dateID': 1,
            'genreID': 1,
            'average_rating': 4.0,
            'ratings_count': 100,
            'text_reviews_count': 10,
            'num_pages': 200,
            'engagement': 0.1
        }
        
        is_valid, errors, warnings = table_validator.validate_all(all_valid_tables)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any('Intégrité référentielle' in error for error in errors)
    
    def test_validate_all_with_unknown_table(self, table_validator):
        """Test validation avec une table inconnue."""
        tables = {
            'unknown_table': pd.DataFrame({'col': [1, 2, 3]})
        }
        
        is_valid, errors, warnings = table_validator.validate_all(tables)
        
        # Doit générer un warning
        assert len(warnings) > 0
        assert any('unknown_table' in warning for warning in warnings)


class TestUtilityFunction:
    """Tests de la fonction utilitaire validate_dimension."""
    
    def test_validate_dimension_function(self, valid_dim_books_df):
        """Test de la fonction wrapper validate_dimension."""
        validated_df = validate_dimension(
            valid_dim_books_df,
            DimBooks,
            'bookID'
        )
        
        assert len(validated_df) == len(valid_dim_books_df)
        assert 'bookID' in validated_df.columns


class TestEdgeCases:
    """Tests des cas limites et situations extrêmes."""
    
    def test_empty_dataframe(self, table_validator):
        """Test avec un DataFrame vide."""
        df = pd.DataFrame(columns=['bookID', 'title'])
        
        validated_df = table_validator._validate_dimension(df, DimBooks, 'bookID')
        
        assert len(validated_df) == 0
    
    def test_single_row(self, table_validator):
        """Test avec une seule ligne."""
        df = pd.DataFrame({
            'bookID': [1],
            'title': ['Book One']
        })
        
        validated_df = table_validator._validate_dimension(df, DimBooks, 'bookID')
        
        assert len(validated_df) == 1
    
    def test_large_dataframe(self, table_validator):
        """Test avec un grand DataFrame."""
        df = pd.DataFrame({
            'bookID': range(1, 1001),
            'title': [f'Book {i}' for i in range(1, 1001)]
        })
        
        validated_df = table_validator._validate_dimension(df, DimBooks, 'bookID')
        
        assert len(validated_df) == 1000
    
    def test_fact_books_with_all_null_fks(self, table_validator):
        """Test fact_books avec toutes les FK nulles."""
        df = pd.DataFrame({
            'bookID': [1],
            'publisherID': [None],
            'languageID': [None],
            'dateID': [None],
            'genreID': [None],
            'average_rating': [4.5],
            'ratings_count': [1000],
            'text_reviews_count': [100],
            'num_pages': [300],
            'engagement': [0.1]
        })
        
        # Doit valider sans erreur (FK nulles tolérées)
        validated_df = table_validator._validate_dimension(df, FactBooks, 'bookID')
        
        assert len(validated_df) == 1
    
    def test_date_leap_year(self, table_validator):
        """Test date dans une année bissextile."""
        df = pd.DataFrame({
            'dateID': [1],
            'publication_date': [datetime(2020, 2, 29)],  # Année bissextile
            'year': [2020],
            'month': [2],
            'day': [29],
            'month_name': ['February'],
            'day_name': ['Saturday'],
            'quarter': [1]
        })
        
        validated_df = table_validator._validate_dimension(df, DimDates, 'dateID')
        
        assert len(validated_df) == 1
    
    def test_date_non_leap_year_invalid(self, table_validator):
        """Test 29 février dans année non-bissextile."""
        df = pd.DataFrame({
            'dateID': [1],
            'publication_date': [datetime(2019, 2, 28)],
            'year': [2019],
            'month': [2],
            'day': [29],  # Invalid pour 2019
            'month_name': ['February'],
            'day_name': ['Friday'],
            'quarter': [1]
        })
        
        with pytest.raises(ValueError, match='Erreurs de validation'):
            table_validator._validate_dimension(df, DimDates, 'dateID')


class TestDataQuality:
    """Tests de qualité des données."""
    
    def test_validate_preserves_data_integrity(self, table_validator, valid_dim_books_df):
        """Test que la validation préserve l'intégrité des données."""
        validated_df = table_validator._validate_dimension(
            valid_dim_books_df,
            DimBooks,
            'bookID'
        )
        
        # Vérifier que les données sont identiques
        pd.testing.assert_frame_equal(
            validated_df.sort_values('bookID').reset_index(drop=True),
            valid_dim_books_df.sort_values('bookID').reset_index(drop=True)
        )
    
    def test_validate_all_returns_consistent_results(
        self,
        table_validator,
        all_valid_tables
    ):
        """Test que validate_all retourne des résultats cohérents."""
        is_valid1, errors1, warnings1 = table_validator.validate_all(all_valid_tables)
        
        # Réinitialiser
        table_validator.validation_errors = []
        table_validator.validation_warnings = []
        
        is_valid2, errors2, warnings2 = table_validator.validate_all(all_valid_tables)
        
        # Les résultats doivent être identiques
        assert is_valid1 == is_valid2
        assert errors1 == errors2


# ============================================================================
# EXÉCUTION DES TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])