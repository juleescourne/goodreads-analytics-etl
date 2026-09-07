# -*- coding: utf-8 -*-
"""
Created on Wed Dec 31 23:54:05 2025

@author: Jules Courné
"""

"""
Tests unitaires pour le module BooksTransformer.

Author: Jules Courné
Date: 2025-12-31
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Ajouter le chemin parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transform.book_transformer import BooksTransformer
from src.utils.config_loader import ConfigLoader


class TestBooksTransformer:
    """Tests pour la classe BooksTransformer."""
    
    @pytest.fixture
    def config_loader(self):
        """Charge la vraie configuration."""
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            pytest.skip(f"Config file not found: {config_path}")
        
        return ConfigLoader(str(config_path))
    
    @pytest.fixture
    def transformer(self, config_loader):
        """Fixture pour créer une instance de BooksTransformer."""
        return BooksTransformer(config_loader)
    
    @pytest.fixture
    def sample_valid_df(self):
        """DataFrame valide pour les tests."""
        return pd.DataFrame({
            'bookID': [1, 2, 3, 4, 5],
            'title': ['Book 1', 'Book 2', 'Book 3', 'Book 4', 'Book 5'],
            'authors': ['Author A', 'Author B', 'Author C', 'Author D', 'Author E'],
            'average_rating': [4.5, 3.8, 4.2, 4.0, 3.5],
            'isbn13': ['1234567890123', '2345678901234', '3456789012345', '4567890123456', '5678901234567'],
            'language_code': ['eng', 'fra', 'eng', 'spa', 'eng'],
            'num_pages': [300, 250, 400, 350, 200],
            'ratings_count': [1000, 500, 750, 600, 300],
            'text_reviews_count': [50, 25, 40, 30, 15],
            'publication_date': ['2020-01-01', '2019-06-15', '2021-03-20', '2018-12-10', '2022-07-04'],
            'publisher_name': ['Publisher A', 'Publisher B', 'Publisher A', 'Publisher C', 'Publisher B'],
            'genre_name': ['Fiction', 'Science Fiction', 'Fiction', 'Mystery', 'Fantasy']
        })
    
    @pytest.fixture
    def sample_corrupted_df(self):
        """DataFrame avec données corrompues."""
        return pd.DataFrame({
            'bookID': ['1', 'abc', '3', 'def', '5'],  # Certains non numériques
            'title': ['Book 1', 'Book 2', 'Book 3', 'Book 4', 'Book 5'],
            'authors': ['Author A', 'Author B', 'Author C', 'Author D', 'Author E'],
            'average_rating': [4.5, 3.8, 4.2, 4.0, 3.5],
            'isbn13': ['1234567890123', 'not_isbn', '3456789012345', 'bad', '5678901234567'],
            'language_code': ['eng', 'fra', 'eng', 'spa', 'eng'],
            'num_pages': [300, 250, 400, 350, 200],
            'ratings_count': [1000, 500, 750, 600, 300],
            'text_reviews_count': [50, 25, 40, 30, 15],
            'publication_date': ['2020-01-01', '2019-06-15', '2021-03-20', '2018-12-10', '2022-07-04'],
            'publisher_name': ['Publisher A', 'Publisher B', 'Publisher A', 'Publisher C', 'Publisher B'],
            'genre_name': ['Fiction', 'Science Fiction', 'Fiction', 'Mystery', 'Fantasy']
        })
    
    def test_init(self, config_loader):
        """Test l'initialisation du BooksTransformer."""
        transformer = BooksTransformer(config_loader)
        
        assert transformer.config == config_loader
        assert transformer.logger is not None
        assert isinstance(transformer.genres, list)
        assert isinstance(transformer.default_values, dict)
        
        # Vérifier les noms de colonnes
        assert transformer.BOOKID == 'bookID'
        assert transformer.TITLE == 'title'
        assert transformer.AUTHORS == 'authors'
        assert transformer.AVG_RATING == 'average_rating'
        assert transformer.ISBN == 'isbn13'
    
    def test_validate_columns_success(self, transformer, sample_valid_df):
        """Test la validation avec toutes les colonnes présentes."""
        result = transformer._validate_columns(sample_valid_df)
        
        assert result is True
    
    def test_validate_columns_missing(self, transformer):
        """Test la validation avec colonnes manquantes."""
        df = pd.DataFrame({
            'bookID': [1, 2],
            'title': ['Book 1', 'Book 2']
            # Colonnes manquantes
        })
        
        result = transformer._validate_columns(df)
        
        assert result is False
    
    def test_validate_columns_cleanup(self, transformer, sample_valid_df):
        """Test le nettoyage des noms de colonnes."""
        # Ajouter des espaces et caractères spéciaux
        df = sample_valid_df.copy()
        df.columns = [f' {col}; ' for col in df.columns]
        
        result = transformer._validate_columns(df)
        
        assert result is True
        # Vérifier que les colonnes sont nettoyées
        assert all(col.strip() == col for col in df.columns)
        assert all(';' not in col for col in df.columns)
    
    def test_remove_corrupted_rows(self, transformer, sample_corrupted_df):
        """Test la suppression des lignes corrompues."""
        initial_count = len(sample_corrupted_df)
        
        result = transformer._remove_corrupted_rows(sample_corrupted_df)
        
        # Devrait avoir supprimé les lignes avec bookID ou ISBN non numériques
        assert len(result) < initial_count
        
        # Vérifier que toutes les valeurs restantes sont numériques
        assert result['bookID'].astype(str).str.isnumeric().all()
        assert result['isbn13'].astype(str).str.isnumeric().all()
    
    def test_remove_corrupted_rows_clean_data(self, transformer, sample_valid_df):
        """Test avec données déjà propres."""
        initial_count = len(sample_valid_df)
        
        result = transformer._remove_corrupted_rows(sample_valid_df)
        
        # Ne devrait rien supprimer
        assert len(result) == initial_count
    
    def test_remove_corrupted_rows_genre_semicolon(self, transformer):
        """Test la suppression des points-virgules dans les genres."""
        df = pd.DataFrame({
            'bookID': ['1', '2'],
            'isbn13': ['123', '456'],
            'genre_name': ['Fiction;Drama', 'Mystery']
        })
        
        result = transformer._remove_corrupted_rows(df)
        
        assert ';' not in result['genre_name'].iloc[0]
    
    def test_convert_types(self, transformer, sample_valid_df):
        """Test la conversion des types."""
        result = transformer._convert_types(sample_valid_df)
        
        # Vérifier les types numériques
        assert result['bookID'].dtype == 'Int64'
        assert result['average_rating'].dtype == 'Float64'
        assert result['ratings_count'].dtype == 'Int64'
        assert result['text_reviews_count'].dtype == 'Int64'
        assert result['num_pages'].dtype == 'Int64'
        
        # Vérifier le type datetime
        assert pd.api.types.is_datetime64_any_dtype(result['publication_date'])
    
    def test_convert_types_with_invalid_values(self, transformer):
        """Test la conversion avec valeurs invalides."""
        df = pd.DataFrame({
            'bookID': ['1', 'invalid', '3'],
            'average_rating': ['4.5', 'not_a_number', '3.8'],
            'ratings_count': ['100', 'abc', '200'],
            'text_reviews_count': ['10', '20', 'xyz'],
            'num_pages': ['300', '250', 'bad'],
            'publication_date': ['2020-01-01', 'invalid_date', '2021-03-20']
        })
        
        result = transformer._convert_types(df)
        
        # Les valeurs invalides devraient être NaN
        assert pd.isna(result['bookID'].iloc[1])
        assert pd.isna(result['average_rating'].iloc[1])
        assert pd.isna(result['publication_date'].iloc[1])
    
    def test_handle_missing_values_drop_critical(self, transformer):
        """Test la suppression des lignes avec bookID/ISBN manquant."""
        df = pd.DataFrame({
            'bookID': [1, None, 3],
            'isbn13': ['123', '456', None],
            'title': ['Book 1', 'Book 2', 'Book 3'],
            'average_rating': [4.5, 3.8, 4.2]
        })
        
        result = transformer._handle_missing_values(df)
        
        # Devrait supprimer les lignes avec bookID ou ISBN manquant
        assert len(result) == 1  # Seule la première ligne est complète
    
    def test_handle_missing_values_fill_numeric(self, transformer, sample_valid_df):
        """Test le remplissage des valeurs numériques manquantes."""
        df = sample_valid_df.copy()
        df.loc[0, 'average_rating'] = None
        df.loc[1, 'ratings_count'] = None
        df.loc[2, 'num_pages'] = None
        
        result = transformer._handle_missing_values(df)
        
        # Vérifier que les valeurs ont été remplies
        assert not pd.isna(result['average_rating'].iloc[0])
        assert not pd.isna(result['ratings_count'].iloc[1])
        assert not pd.isna(result['num_pages'].iloc[2])
    
    def test_handle_missing_values_default_values(self, transformer):
        """Test le remplissage avec valeurs par défaut."""
        df = pd.DataFrame({
            'bookID': [1, 2],
            'isbn13': ['123', '456'],
            'publication_date': [None, '2020-01-01'],
            'language_code': ['eng', None],
            'publisher_name': ['Pub A', None],
            'authors': [None, 'Author B']
        })
        
        result = transformer._handle_missing_values(df)
        
        # Vérifier les valeurs par défaut
        assert result['publication_date'].iloc[0] is not None
        assert result['language_code'].iloc[1] is not None
        assert result['publisher_name'].iloc[1] is not None
        assert result['authors'].iloc[0] is not None
    
    def test_handle_missing_values_genre_validation(self, transformer):
        """Test la validation et remplissage des genres."""
        df = pd.DataFrame({
            'bookID': [1, 2, 3],
            'isbn13': ['123', '456', '789'],
            'genre_name': ['Fiction', 'InvalidGenre', None]
        })
        
        result = transformer._handle_missing_values(df)
        
        # Les genres invalides ou None devraient être 'Other'
        assert result['genre_name'].iloc[1] == 'Other'
        assert result['genre_name'].iloc[2] == 'Other'
    
    def test_clean_strings(self, transformer, sample_valid_df):
        """Test le nettoyage des chaînes."""
        df = sample_valid_df.copy()
        # Ajouter des espaces
        df['title'] = '  ' + df['title'] + '  '
        df['authors'] = '  ' + df['authors'] + '  '
        
        result = transformer._clean_strings(df)
        
        # Vérifier que les espaces sont supprimés
        assert not result['title'].str.startswith(' ').any()
        assert not result['title'].str.endswith(' ').any()
        assert not result['authors'].str.startswith(' ').any()
    
    def test_clean_strings_column_selection(self, transformer, sample_valid_df):
        """Test la sélection des colonnes utiles."""
        df = sample_valid_df.copy()
        df['extra_column'] = 'should_be_removed'
        
        result = transformer._clean_strings(df)
        
        # La colonne extra ne devrait pas être présente
        assert 'extra_column' not in result.columns
        
        # Toutes les colonnes requises devraient être présentes
        required = ['bookID', 'title', 'authors', 'average_rating', 'isbn13',
                   'language_code', 'num_pages', 'ratings_count', 
                   'text_reviews_count', 'publication_date', 
                   'publisher_name', 'genre_name']
        for col in required:
            assert col in result.columns
    
    def test_handle_outliers_rating_clip(self, transformer):
        """Test le clipping des notes."""
        df = pd.DataFrame({
            'average_rating': [-1.0, 3.5, 6.0, 4.2, 10.0],
            'ratings_count': [100, 200, 300, 400, 500],
            'text_reviews_count': [10, 20, 30, 40, 50],
            'num_pages': [300, 250, 400, 350, 200],
            'publication_date': pd.to_datetime(['2020-01-01'] * 5)
        })
        
        result = transformer._handle_outliers(df)
        
        # Les notes doivent être entre 0 et 5
        assert result['average_rating'].min() >= 0
        assert result['average_rating'].max() <= 5
    
    def test_handle_outliers_negative_counts(self, transformer):
        """Test le clipping des compteurs négatifs."""
        df = pd.DataFrame({
            'average_rating': [4.5, 3.8, 4.2],
            'ratings_count': [-100, 200, 300],
            'text_reviews_count': [10, -20, 30],
            'num_pages': [300, 250, 400],
            'publication_date': pd.to_datetime(['2020-01-01'] * 3)
        })
        
        result = transformer._handle_outliers(df)
        
        # Les compteurs doivent être >= 0
        assert result['ratings_count'].min() >= 0
        assert result['text_reviews_count'].min() >= 0
    
    def test_handle_outliers_pages_zero(self, transformer):
        """Test le remplacement des pages <= 0."""
        df = pd.DataFrame({
            'average_rating': [4.5, 3.8, 4.2, 4.0],
            'ratings_count': [100, 200, 300, 400],
            'text_reviews_count': [10, 20, 30, 40],
            'num_pages': [0, -50, 300, 400],
            'publication_date': pd.to_datetime(['2020-01-01'] * 4)
        })
        
        result = transformer._handle_outliers(df)
        
        # Les pages <= 0 doivent être remplacées par la médiane
        assert result['num_pages'].min() > 0
    
    def test_handle_outliers_future_dates(self, transformer):
        """Test la suppression des dates futures."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        df = pd.DataFrame({
            'bookID': [1, 2, 3],
            'average_rating': [4.5, 3.8, 4.2],
            'ratings_count': [100, 200, 300],
            'text_reviews_count': [10, 20, 30],
            'num_pages': [300, 250, 400],
            'publication_date': pd.to_datetime(['2020-01-01', future_date, '2021-03-20'])
        })
        
        initial_count = len(df)
        result = transformer._handle_outliers(df)
        
        # La ligne avec date future devrait être supprimée
        assert len(result) < initial_count
        assert all(result['publication_date'] <= pd.Timestamp.now())
    
    def test_remove_duplicates(self, transformer):
        """Test la suppression des doublons."""
        df = pd.DataFrame({
            'bookID': [1, 2, 1, 3],  # bookID 1 en doublon
            'isbn13': ['123', '456', '123', '789'],
            'title': ['Book 1', 'Book 2', 'Book 1 Duplicate', 'Book 3'],
            'average_rating': [4.5, 3.8, 4.5, 4.2]
        })
        
        result = transformer._remove_duplicates(df)
        
        # Devrait garder 3 lignes (une des deux lignes avec bookID=1 supprimée)
        assert len(result) == 3
        
        # Vérifier qu'il n'y a plus de doublons
        assert not result.duplicated(subset=['bookID', 'isbn13']).any()
    
    def test_remove_duplicates_keep_first(self, transformer):
        """Test que la première occurrence est gardée."""
        df = pd.DataFrame({
            'bookID': [1, 1],
            'isbn13': ['123', '123'],
            'title': ['Original', 'Duplicate']
        })
        
        result = transformer._remove_duplicates(df)
        
        assert len(result) == 1
        assert result['title'].iloc[0] == 'Original'
    
    def test_transform_books_complete_pipeline(self, transformer, sample_valid_df):
        """Test le pipeline complet de transformation."""
        result = transformer.transform_books(sample_valid_df)
        
        assert result is not None
        assert len(result) > 0
        
        # Vérifier les types
        assert result['bookID'].dtype == 'Int64'
        assert result['average_rating'].dtype == 'Float64'
        assert pd.api.types.is_datetime64_any_dtype(result['publication_date'])
        
        # Vérifier qu'il n'y a pas de doublons
        assert not result.duplicated(subset=['bookID', 'isbn13']).any()
        
        # Vérifier les contraintes
        assert result['average_rating'].between(0, 5).all()
        assert (result['ratings_count'] >= 0).all()
        assert (result['num_pages'] > 0).all()
    
    def test_transform_books_with_corrupted_data(self, transformer, sample_corrupted_df):
        """Test le pipeline avec données corrompues."""
        result = transformer.transform_books(sample_corrupted_df)
        
        assert result is not None
        # Certaines lignes devraient être supprimées
        assert len(result) < len(sample_corrupted_df)
    
    def test_transform_books_invalid_columns(self, transformer):
        """Test avec colonnes manquantes."""
        df = pd.DataFrame({
            'bookID': [1, 2],
            'title': ['Book 1', 'Book 2']
        })
        
        result = transformer.transform_books(df)
        
        # Devrait retourner None car colonnes manquantes
        assert result is None
    
    def test_transform_books_empty_result(self, transformer):
        """Test avec données qui résultent en DataFrame vide."""
        # Toutes les lignes ont des bookID invalides
        df = pd.DataFrame({
            'bookID': ['invalid', 'bad', 'wrong'],
            'isbn13': ['abc', 'def', 'ghi'],
            'title': ['Book 1', 'Book 2', 'Book 3'],
            'authors': ['A', 'B', 'C'],
            'average_rating': [4.5, 3.8, 4.2],
            'language_code': ['eng', 'fra', 'spa'],
            'num_pages': [300, 250, 400],
            'ratings_count': [100, 200, 300],
            'text_reviews_count': [10, 20, 30],
            'publication_date': ['2020-01-01', '2019-06-15', '2021-03-20'],
            'publisher_name': ['Pub A', 'Pub B', 'Pub C'],
            'genre_name': ['Fiction', 'Mystery', 'Fantasy']
        })
        
        result = transformer.transform_books(df)
        
        # Devrait retourner None car toutes les lignes sont supprimées
        assert result is None


class TestBooksTransformerIntegration:
    """Tests d'intégration pour BooksTransformer."""
    
    @pytest.fixture
    def config_loader(self):
        """Charge la vraie configuration."""
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            pytest.skip(f"Config file not found: {config_path}")
        
        return ConfigLoader(str(config_path))
    
    def test_realistic_data_transformation(self, config_loader):
        """Test avec des données réalistes."""
        transformer = BooksTransformer(config_loader)
        
        # Données réalistes avec divers problèmes
        df = pd.DataFrame({
            'bookID': ['1', '2', 'invalid', '4', '5', '1'],  # Doublon et invalide
            'title': ['  The Great Book  ', 'Another Story', 'Book 3', 'Epic Tale', 'Mystery Novel', 'The Great Book'],
            'authors': ['J.K. Rowling', 'George R.R. Martin', 'Unknown', None, 'Agatha Christie', 'J.K. Rowling'],
            'average_rating': [4.7, 8.5, 4.3, -1.0, 4.5, 4.7],  # Outliers
            'isbn13': ['1111111111111', '2222222222222', 'bad_isbn', '4444444444444', '5555555555555', '1111111111111'],
            'language_code': ['eng', 'fra', 'eng', None, 'spa', 'eng'],
            'num_pages': [450, 600, 0, 380, -50, 450],  # Valeurs <= 0
            'ratings_count': [50000, 30000, -100, 45000, 20000, 50000],  # Négatif
            'text_reviews_count': [2500, 1500, 2000, None, 1000, 2500],
            'publication_date': ['2020-01-15', (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'), '2021-09-10', '2019-03-20', 'invalid', '2020-01-15'],
            'publisher_name': ['Penguin Books', 'HarperCollins', None, 'Random House', 'Mystery Press', 'Penguin Books'],
            'genre_name': ['Fantasy', 'InvalidGenre', 'Science Fiction;Drama', 'Mystery', None, 'Fantasy']
        })
        
        result = transformer.transform_books(df)
        
        assert result is not None
        
        # Vérifications
        assert len(result) < len(df)  # Certaines lignes supprimées
        
        # Pas de doublons
        assert not result.duplicated(subset=['bookID', 'isbn13']).any()
        
        # Contraintes respectées
        assert result['average_rating'].between(0, 5).all()
        assert (result['ratings_count'] >= 0).all()
        assert (result['num_pages'] > 0).all()
        assert all(result['publication_date'] <= pd.Timestamp.now())
        
        # Pas de valeurs manquantes critiques
        assert not result['bookID'].isna().any()
        assert not result['isbn13'].isna().any()
        
        # Strings nettoyés
        assert not result['title'].str.startswith(' ').any()
        assert not result['title'].str.endswith(' ').any()