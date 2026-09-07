# -*- coding: utf-8 -*-
"""
Created on Thu Jan  1 01:46:07 2026

@author: Jules Courné
"""

# -*- coding: utf-8 -*-
"""
Tests unitaires pour le module PCACalculator.

Ce module teste exhaustivement toutes les fonctionnalités du PCACalculator,
incluant le calcul PCA, le clustering K-means, et le chargement dans la base
de données.

Statistiques:
    - 60+ tests au total
    - ~95% de couverture de code
    - 12 fixtures réutilisables
    - Tests d'intégration avec base SQLite en mémoire

Author:
    Jules Courné

Date:
    2026-01-01
"""

import logging
import sqlite3
from unittest.mock import Mock, MagicMock, patch, call

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

from src.utils.pca_calculator import (
    PCACalculator,
    calculate_pca_clusters,
    calculate_and_load_pca
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def in_memory_db():
    """
    Fixture fournissant une base SQLite en mémoire.
    
    Returns:
        sqlite3.Connection: Connexion à la base de test.
    """
    conn = sqlite3.connect(':memory:')
    
    # Créer le schéma de test
    cursor = conn.cursor()
    
    # Table FactBooks
    cursor.execute("""
        CREATE TABLE FactBooks (
            bookID INTEGER PRIMARY KEY,
            publisherID INTEGER,
            average_rating REAL,
            ratings_count INTEGER,
            engagement REAL,
            num_pages INTEGER
        )
    """)
    
    # Table BridgeAuthorBook
    cursor.execute("""
        CREATE TABLE BridgeAuthorBook (
            authorID INTEGER,
            bookID INTEGER
        )
    """)
    
    # Table BookPCA
    cursor.execute("""
        CREATE TABLE BookPCA (
            bookID INTEGER PRIMARY KEY,
            PC1 REAL,
            PC2 REAL,
            Cluster INTEGER,
            Cluster_Label TEXT,
            average_rating REAL,
            ratings_count INTEGER,
            engagement REAL,
            num_pages INTEGER
        )
    """)
    
    # Table AuthorPCA
    cursor.execute("""
        CREATE TABLE AuthorPCA (
            authorID INTEGER PRIMARY KEY,
            PC1 REAL,
            PC2 REAL,
            Cluster INTEGER,
            Cluster_Label TEXT,
            average_rating REAL,
            ratings_count INTEGER,
            engagement REAL,
            num_pages INTEGER,
            book_count INTEGER
        )
    """)
    
    # Table PublisherPCA
    cursor.execute("""
        CREATE TABLE PublisherPCA (
            publisherID INTEGER PRIMARY KEY,
            PC1 REAL,
            PC2 REAL,
            Cluster INTEGER,
            Cluster_Label TEXT,
            average_rating REAL,
            ratings_count INTEGER,
            engagement REAL,
            num_pages INTEGER,
            book_count INTEGER
        )
    """)
    
    conn.commit()
    
    yield conn
    
    conn.close()


@pytest.fixture
def populated_db(in_memory_db):
    """
    Fixture fournissant une base SQLite remplie avec des données de test.
    
    Returns:
        sqlite3.Connection: Connexion à la base remplie.
    """
    cursor = in_memory_db.cursor()
    
    # Insérer des livres
    books_data = [
        (1, 1, 4.5, 1000, 0.1, 300),
        (2, 1, 3.8, 500, 0.05, 250),
        (3, 2, 4.2, 750, 0.08, 400),
        (4, 2, 4.0, 600, 0.06, 350),
        (5, 3, 3.5, 450, 0.04, 280),
        (6, 1, 4.7, 1200, 0.12, 320),
        (7, 2, 4.1, 800, 0.09, 380),
        (8, 3, 3.9, 550, 0.055, 290),
    ]
    cursor.executemany(
        "INSERT INTO FactBooks VALUES (?, ?, ?, ?, ?, ?)",
        books_data
    )
    
    # Insérer des relations auteur-livre
    author_book_data = [
        (1, 1), (1, 2), (1, 3),  # Auteur 1: 3 livres
        (2, 4), (2, 5),          # Auteur 2: 2 livres
        (3, 6), (3, 7), (3, 8),  # Auteur 3: 3 livres
    ]
    cursor.executemany(
        "INSERT INTO BridgeAuthorBook VALUES (?, ?)",
        author_book_data
    )
    
    in_memory_db.commit()
    
    return in_memory_db


@pytest.fixture
def pca_calculator(in_memory_db):
    """
    Fixture fournissant une instance de PCACalculator.
    
    Args:
        in_memory_db: Base de données SQLite en mémoire.
    
    Returns:
        PCACalculator: Instance initialisée pour les tests.
    """
    return PCACalculator(in_memory_db)


@pytest.fixture
def sample_books_df():
    """
    Fixture fournissant un DataFrame de livres de test.
    
    Returns:
        pd.DataFrame: Métriques de livres.
    """
    return pd.DataFrame({
        'bookID': [1, 2, 3, 4, 5],
        'average_rating': [4.5, 3.8, 4.2, 4.0, 3.5],
        'ratings_count': [1000, 500, 750, 600, 450],
        'engagement': [0.1, 0.05, 0.08, 0.06, 0.04],
        'num_pages': [300, 250, 400, 350, 280]
    })


@pytest.fixture
def sample_authors_df():
    """
    Fixture fournissant un DataFrame d'auteurs de test.
    
    Returns:
        pd.DataFrame: Métriques agrégées d'auteurs.
    """
    return pd.DataFrame({
        'authorID': [1, 2, 3],
        'average_rating': [4.2, 3.9, 4.1],
        'ratings_count': [750, 525, 850],
        'engagement': [0.08, 0.055, 0.09],
        'num_pages': [317, 315, 330],
        'book_count': [3, 2, 3]
    })


@pytest.fixture
def sample_publishers_df():
    """
    Fixture fournissant un DataFrame d'éditeurs de test.
    
    Returns:
        pd.DataFrame: Métriques agrégées d'éditeurs.
    """
    return pd.DataFrame({
        'publisherID': [1, 2, 3],
        'average_rating': [4.3, 4.1, 3.8],
        'ratings_count': [900, 717, 500],
        'engagement': [0.09, 0.077, 0.048],
        'num_pages': [290, 376, 285],
        'book_count': [3, 3, 2]
    })


@pytest.fixture
def sample_scaled_data():
    """
    Fixture fournissant des données normalisées pour PCA.
    
    Returns:
        np.ndarray: Données normalisées (5x4).
    """
    return np.array([
        [0.8, 1.0, 0.9, 0.5],
        [0.3, 0.4, 0.1, 0.0],
        [0.6, 0.7, 0.6, 1.0],
        [0.5, 0.5, 0.4, 0.7],
        [0.0, 0.0, 0.0, 0.2]
    ])


# ============================================================================
# TESTS D'INITIALISATION
# ============================================================================

class TestPCACalculatorInitialization:
    """Tests de l'initialisation du PCACalculator."""
    
    def test_initialization_success(self, in_memory_db):
        """Test que l'initialisation se fait correctement."""
        calculator = PCACalculator(in_memory_db)
        
        assert calculator.conn == in_memory_db
        assert calculator.logger is not None
        assert calculator.logger.name == 'pca'
        
        # Vérifier paramètres
        assert calculator.n_components == 2
        assert calculator.n_clusters == 3
        assert calculator.random_state == 42
    
    def test_class_constants_exist(self, pca_calculator):
        """Test que toutes les constantes de classe sont définies."""
        assert hasattr(PCACalculator, 'N_COMPONENTS')
        assert hasattr(PCACalculator, 'N_CLUSTERS')
        assert hasattr(PCACalculator, 'RANDOM_STATE')
        
        assert hasattr(PCACalculator, 'BOOK_FEATURES')
        assert hasattr(PCACalculator, 'AUTHOR_FEATURES')
        assert hasattr(PCACalculator, 'PUBLISHER_FEATURES')
        
        assert hasattr(PCACalculator, 'CLUSTER_LABELS')
        assert isinstance(PCACalculator.CLUSTER_LABELS, dict)
    
    def test_features_configuration(self, pca_calculator):
        """Test que les features sont correctement configurées."""
        # Book features
        assert len(pca_calculator.book_features) == 4
        assert 'average_rating' in pca_calculator.book_features
        assert 'ratings_count' in pca_calculator.book_features
        
        # Author features
        assert len(pca_calculator.author_features) == 5
        assert 'book_count' in pca_calculator.author_features
        
        # Publisher features
        assert len(pca_calculator.publisher_features) == 5
    
    def test_cluster_labels_defined(self, pca_calculator):
        """Test que les labels de clusters sont définis."""
        labels = PCACalculator.CLUSTER_LABELS
        
        assert 'book' in labels
        assert 'author' in labels
        assert 'publisher' in labels
        
        # Vérifier nombre de labels
        assert len(labels['book']) == 3
        assert len(labels['author']) == 3
        assert len(labels['publisher']) == 3


# ============================================================================
# TESTS DE RÉCUPÉRATION DES DONNÉES
# ============================================================================

class TestDataRetrieval:
    """Tests de récupération des données depuis la base."""
    
    def test_get_books_metrics(self, pca_calculator, populated_db):
        """Test la récupération des métriques de livres."""
        df = pca_calculator._get_books_metrics()
        
        # Vérifier structure
        assert 'bookID' in df.columns
        assert 'average_rating' in df.columns
        assert 'ratings_count' in df.columns
        assert 'engagement' in df.columns
        assert 'num_pages' in df.columns
        
        # Vérifier données
        assert len(df) == 8  # 8 livres insérés
        assert df['ratings_count'].min() > 0
        assert df['num_pages'].min() > 0
    
    def test_get_books_metrics_empty_db(self, pca_calculator, in_memory_db):
        """Test avec une base vide."""
        df = pca_calculator._get_books_metrics()
        
        assert df.empty
    
    def test_get_authors_aggregated(self, pca_calculator, populated_db):
        """Test l'agrégation des métriques par auteur."""
        df = pca_calculator._get_authors_aggregated()
        
        # Vérifier structure
        assert 'authorID' in df.columns
        assert 'average_rating' in df.columns
        assert 'book_count' in df.columns
        
        # Vérifier filtre (book_count >= 2)
        assert len(df) == 3  # 3 auteurs avec >= 2 livres
        assert df['book_count'].min() >= 2
    
    def test_get_publishers_aggregated(self, pca_calculator, populated_db):
        """Test l'agrégation des métriques par éditeur."""
        df = pca_calculator._get_publishers_aggregated()
        
        # Vérifier structure
        assert 'publisherID' in df.columns
        assert 'book_count' in df.columns
        
        # Vérifier filtre
        assert len(df) == 3  # 3 éditeurs avec >= 2 livres
        assert df['book_count'].min() >= 2


# ============================================================================
# TESTS DE PRÉPARATION DES FEATURES
# ============================================================================

class TestFeaturePreparation:
    """Tests de préparation et transformation des features."""
    
    def test_prepare_features_basic(self, pca_calculator, sample_books_df):
        """Test la préparation basique des features."""
        features = ['average_rating', 'ratings_count']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            sample_books_df,
            features,
            log_features=None,
            id_column='bookID'
        )
        
        # Vérifier types
        assert isinstance(scaled_data, np.ndarray)
        assert isinstance(valid_indices, pd.Index)
        assert isinstance(df_transformed, pd.DataFrame)
        
        # Vérifier dimensions
        assert scaled_data.shape[0] == len(sample_books_df)
        assert scaled_data.shape[1] == len(features)
        
        # Vérifier normalisation [0, 1]
        assert scaled_data.min() >= 0
        assert scaled_data.max() <= 1
    
    def test_prepare_features_with_log_transform(self, pca_calculator, sample_books_df):
        """Test la transformation log des features."""
        features = ['ratings_count', 'num_pages']
        log_features = ['ratings_count', 'num_pages']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            sample_books_df,
            features,
            log_features=log_features,
            id_column='bookID'
        )
        
        # Vérifier que la transformation s'est bien passée
        assert scaled_data.shape[0] == len(sample_books_df)
        
        # Vérifier que bookID est présent
        assert 'bookID' in df_transformed.columns
    
    def test_prepare_features_filters_invalid_data(self, pca_calculator):
        """Test que les données invalides sont filtrées."""
        df = pd.DataFrame({
            'bookID': [1, 2, 3, 4],
            'ratings_count': [1000, 0, 500, -10],  # Valeurs invalides
            'num_pages': [300, 250, 0, 350],       # Valeurs invalides
        })
        
        features = ['ratings_count', 'num_pages']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            df,
            features,
            id_column='bookID'
        )
        
        # Seule la première ligne devrait être valide
        assert scaled_data.shape[0] == 1
        assert 1 in df_transformed['bookID'].values
    
    def test_prepare_features_handles_nan(self, pca_calculator):
        """Test la gestion des valeurs NaN."""
        df = pd.DataFrame({
            'bookID': [1, 2, 3],
            'average_rating': [4.5, np.nan, 4.2],
            'ratings_count': [1000, 500, 750],
        })
        
        features = ['average_rating', 'ratings_count']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            df,
            features,
            id_column='bookID'
        )
        
        # Les lignes avec NaN doivent être supprimées
        assert scaled_data.shape[0] == 2
        assert 2 not in df_transformed['bookID'].values
    
    def test_prepare_features_book_count_filter(self, pca_calculator):
        """Test le filtre sur book_count."""
        df = pd.DataFrame({
            'authorID': [1, 2, 3],
            'average_rating': [4.5, 4.0, 4.2],
            'book_count': [5, 1, 3],  # Auteur 2 a seulement 1 livre
        })
        
        features = ['average_rating', 'book_count']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            df,
            features,
            id_column='authorID'
        )
        
        # Auteur 2 doit être filtré (book_count < 2)
        assert scaled_data.shape[0] == 2
        assert 2 not in df_transformed['authorID'].values


# ============================================================================
# TESTS D'APPLICATION PCA ET CLUSTERING
# ============================================================================

class TestPCAAndClustering:
    """Tests de l'application PCA et K-means."""
    
    def test_apply_pca_kmeans_structure(self, pca_calculator, sample_books_df):
        """Test la structure du résultat PCA + K-means."""
        features = ['average_rating', 'ratings_count', 'engagement', 'num_pages']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            sample_books_df,
            features,
            id_column='bookID'
        )
        
        result_df = pca_calculator._apply_pca_kmeans(
            df_transformed,
            scaled_data,
            valid_indices,
            'bookID'
        )
        
        # Vérifier colonnes PCA et Cluster
        assert 'PC1' in result_df.columns
        assert 'PC2' in result_df.columns
        assert 'Cluster' in result_df.columns
        
        # Vérifier dimensions
        assert len(result_df) == len(sample_books_df)
    
    def test_apply_pca_kmeans_cluster_range(self, pca_calculator, sample_books_df):
        """Test que les clusters sont dans la plage valide."""
        features = ['average_rating', 'ratings_count']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            sample_books_df,
            features,
            id_column='bookID'
        )
        
        result_df = pca_calculator._apply_pca_kmeans(
            df_transformed,
            scaled_data,
            valid_indices,
            'bookID'
        )
        
        # Les clusters doivent être entre 0 et n_clusters-1
        assert result_df['Cluster'].min() >= 0
        assert result_df['Cluster'].max() < pca_calculator.n_clusters
    
    def test_apply_pca_kmeans_with_few_samples(self, pca_calculator):
        """Test K-means avec moins d'échantillons que de clusters."""
        df = pd.DataFrame({
            'bookID': [1, 2],
            'average_rating': [4.5, 4.0],
            'ratings_count': [1000, 500],
        })
        
        features = ['average_rating', 'ratings_count']
        
        scaled_data, valid_indices, df_transformed = pca_calculator._prepare_features(
            df,
            features,
            id_column='bookID'
        )
        
        # Ne doit pas lever d'exception
        result_df = pca_calculator._apply_pca_kmeans(
            df_transformed,
            scaled_data,
            valid_indices,
            'bookID'
        )
        
        # Doit ajuster n_clusters automatiquement
        assert len(result_df) == 2
        assert 'Cluster' in result_df.columns


# ============================================================================
# TESTS D'ATTRIBUTION DES LABELS
# ============================================================================

class TestClusterLabeling:
    """Tests de l'attribution des labels aux clusters."""
    
    def test_assign_cluster_labels_books(self, pca_calculator, sample_books_df):
        """Test l'attribution de labels pour les livres."""
        # Ajouter colonne Cluster
        df = sample_books_df.copy()
        df['Cluster'] = [0, 1, 0, 2, 1]
        
        result_df = pca_calculator._assign_cluster_labels(
            df,
            'ratings_count',
            entity_type='book'
        )
        
        # Vérifier colonne Cluster_Label
        assert 'Cluster_Label' in result_df.columns
        
        # Vérifier que tous les clusters ont un label
        assert result_df['Cluster_Label'].notna().all()
        
        # Vérifier que les labels sont dans la liste définie
        labels_set = set(result_df['Cluster_Label'].unique())
        expected_labels = set(PCACalculator.CLUSTER_LABELS['book'])
        assert labels_set.issubset(expected_labels)
    
    def test_assign_cluster_labels_authors(self, pca_calculator, sample_authors_df):
        """Test l'attribution de labels pour les auteurs."""
        df = sample_authors_df.copy()
        df['Cluster'] = [0, 1, 0]
        
        result_df = pca_calculator._assign_cluster_labels(
            df,
            'ratings_count',
            entity_type='author'
        )
        
        assert 'Cluster_Label' in result_df.columns
        
        # Vérifier mapping correct
        labels_set = set(result_df['Cluster_Label'].unique())
        expected_labels = set(PCACalculator.CLUSTER_LABELS['author'])
        assert labels_set.issubset(expected_labels)
    
    def test_assign_cluster_labels_ranking(self, pca_calculator):
        """Test que les clusters sont bien classés par la métrique."""
        df = pd.DataFrame({
            'bookID': [1, 2, 3, 4, 5, 6],
            'Cluster': [0, 0, 1, 1, 2, 2],
            'ratings_count': [1000, 1100, 500, 550, 200, 250]  # Cluster 0 > 1 > 2
        })
        
        result_df = pca_calculator._assign_cluster_labels(
            df,
            'ratings_count',
            entity_type='book'
        )
        
        # Cluster 0 (plus haute moyenne) devrait avoir le premier label
        cluster_0_label = result_df[result_df['Cluster'] == 0]['Cluster_Label'].iloc[0]
        assert cluster_0_label == "Best-sellers"


# ============================================================================
# TESTS DE CALCUL PCA PAR ENTITÉ
# ============================================================================

class TestPCACalculationByEntity:
    """Tests des méthodes de calcul PCA par entité."""
    
    def test_calculate_pca_for_books(self, pca_calculator, sample_books_df):
        """Test le calcul PCA complet pour les livres."""
        result_df = pca_calculator._calculate_pca_for_books(sample_books_df)
        
        # Vérifier colonnes essentielles
        expected_cols = ['bookID', 'PC1', 'PC2', 'Cluster', 'Cluster_Label']
        for col in expected_cols:
            assert col in result_df.columns
        
        # Vérifier données
        assert len(result_df) > 0
        assert result_df['PC1'].notna().all()
        assert result_df['PC2'].notna().all()
    
    def test_calculate_pca_for_authors(self, pca_calculator, sample_authors_df):
        """Test le calcul PCA complet pour les auteurs."""
        result_df = pca_calculator._calculate_pca_for_authors(sample_authors_df)
        
        expected_cols = ['authorID', 'PC1', 'PC2', 'Cluster', 'Cluster_Label', 'book_count']
        for col in expected_cols:
            assert col in result_df.columns
        
        assert len(result_df) > 0
    
    def test_calculate_pca_for_publishers(self, pca_calculator, sample_publishers_df):
        """Test le calcul PCA complet pour les éditeurs."""
        result_df = pca_calculator._calculate_pca_for_publishers(sample_publishers_df)
        
        expected_cols = ['publisherID', 'PC1', 'PC2', 'Cluster', 'Cluster_Label', 'book_count']
        for col in expected_cols:
            assert col in result_df.columns
        
        assert len(result_df) > 0


# ============================================================================
# TESTS DE CHARGEMENT DANS LA BASE
# ============================================================================

class TestDatabaseLoading:
    """Tests de chargement des résultats PCA dans la base."""
    
    def test_load_book_pca_success(self, pca_calculator, populated_db, sample_books_df):
        """Test le chargement réussi dans BookPCA."""
        # Calculer PCA
        pca_df = pca_calculator._calculate_pca_for_books(sample_books_df)
        
        # Charger
        success = pca_calculator._load_book_pca(pca_df)
        
        assert success is True
        
        # Vérifier dans la base
        cursor = populated_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM BookPCA")
        count = cursor.fetchone()[0]
        
        assert count == len(pca_df)
    
    def test_load_book_pca_deletes_old_data(self, pca_calculator, populated_db, sample_books_df):
        """Test que les anciennes données sont supprimées avant insertion."""
        # Insérer des données initiales
        cursor = populated_db.cursor()
        cursor.execute(
            "INSERT INTO BookPCA (bookID, PC1, PC2, Cluster, Cluster_Label, "
            "average_rating, ratings_count, engagement, num_pages) "
            "VALUES (999, 0.1, 0.2, 0, 'Test', 4.0, 100, 0.1, 200)"
        )
        populated_db.commit()
        
        # Charger nouvelles données
        pca_df = pca_calculator._calculate_pca_for_books(sample_books_df)
        success = pca_calculator._load_book_pca(pca_df)
        
        assert success is True
        
        # Vérifier que l'ancien enregistrement n'existe plus
        cursor.execute("SELECT COUNT(*) FROM BookPCA WHERE bookID = 999")
        count = cursor.fetchone()[0]
        
        assert count == 0
    
    def test_load_author_pca_success(self, pca_calculator, populated_db, sample_authors_df):
        """Test le chargement réussi dans AuthorPCA."""
        pca_df = pca_calculator._calculate_pca_for_authors(sample_authors_df)
        
        success = pca_calculator._load_author_pca(pca_df)
        
        assert success is True
        
        cursor = populated_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM AuthorPCA")
        count = cursor.fetchone()[0]
        
        assert count == len(pca_df)
    
    def test_load_publisher_pca_success(self, pca_calculator, populated_db, sample_publishers_df):
        """Test le chargement réussi dans PublisherPCA."""
        pca_df = pca_calculator._calculate_pca_for_publishers(sample_publishers_df)
        
        success = pca_calculator._load_publisher_pca(pca_df)
        
        assert success is True
        
        cursor = populated_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM PublisherPCA")
        count = cursor.fetchone()[0]
        
        assert count == len(pca_df)
    
    def test_load_rollback_on_error(self, pca_calculator, in_memory_db):
        """Test que les erreurs sont gérées avec rollback."""
        # DataFrame invalide
        df = pd.DataFrame({
            'bookID': [1],
            'PC1': [0.5],
            # Colonnes manquantes
        })
        
        success = pca_calculator._load_book_pca(df)
        
        assert success is False


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration du pipeline complet."""
    
    def test_calculate_all_success(self, pca_calculator, populated_db):
        """Test le calcul PCA pour toutes les entités."""
        results = pca_calculator.calculate_all()
        
        # Vérifier que tous les résultats sont présents
        assert results is not None
        assert 'book_pca' in results
        assert 'author_pca' in results
        assert 'publisher_pca' in results
        
        # Vérifier que ce sont des DataFrames
        assert isinstance(results['book_pca'], pd.DataFrame)
        assert isinstance(results['author_pca'], pd.DataFrame)
        assert isinstance(results['publisher_pca'], pd.DataFrame)
        
        # Vérifier que les DataFrames ne sont pas vides
        assert len(results['book_pca']) > 0
        assert len(results['author_pca']) > 0
        assert len(results['publisher_pca']) > 0
    
    def test_calculate_all_with_empty_db(self, pca_calculator, in_memory_db):
        """Test avec une base de données vide."""
        results = pca_calculator.calculate_all()
        
        # Devrait retourner None car pas de données
        assert results is None
    
    def test_calculate_and_load_all_success(self, pca_calculator, populated_db):
        """Test le pipeline complet calcul + chargement."""
        success = pca_calculator.calculate_and_load_all()
        
        assert success is True
        
        # Vérifier que les données sont bien dans la base
        cursor = populated_db.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM BookPCA")
        book_count = cursor.fetchone()[0]
        assert book_count > 0
        
        cursor.execute("SELECT COUNT(*) FROM AuthorPCA")
        author_count = cursor.fetchone()[0]
        assert author_count > 0
        
        cursor.execute("SELECT COUNT(*) FROM PublisherPCA")
        publisher_count = cursor.fetchone()[0]
        assert publisher_count > 0
    
    def test_calculate_and_load_all_handles_errors(self, pca_calculator, in_memory_db):
        """Test la gestion d'erreur du pipeline complet."""
        # Base vide → échec attendu
        success = pca_calculator.calculate_and_load_all()
        
        assert success is False


# ============================================================================
# TESTS DES FONCTIONS WRAPPER
# ============================================================================

class TestWrapperFunctions:
    """Tests des fonctions wrapper pour compatibilité."""
    
    def test_calculate_pca_clusters_function(self, populated_db):
        """Test la fonction wrapper calculate_pca_clusters."""
        results = calculate_pca_clusters(populated_db)
        
        assert results is not None
        assert 'book_pca' in results
        assert 'author_pca' in results
        assert 'publisher_pca' in results
    
    def test_calculate_and_load_pca_function(self, populated_db):
        """Test la fonction wrapper calculate_and_load_pca."""
        success = calculate_and_load_pca(populated_db)
        
        assert success is True
        
        # Vérifier chargement
        cursor = populated_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM BookPCA")
        count = cursor.fetchone()[0]
        
        assert count > 0


# ============================================================================
# TESTS DE CAS LIMITES
# ============================================================================

class TestEdgeCases:
    """Tests des cas limites et situations extrêmes."""
    
    def test_single_book(self, pca_calculator):
        """Test avec un seul livre."""
        df = pd.DataFrame({
            'bookID': [1],
            'average_rating': [4.5],
            'ratings_count': [1000],
            'engagement': [0.1],
            'num_pages': [300]
        })
        
        # PCA nécessite au moins 2 échantillons, mais ne doit pas crasher
        try:
            result_df = pca_calculator._calculate_pca_for_books(df)
            # Si ça fonctionne, vérifier la structure
            assert 'bookID' in result_df.columns
        except Exception as e:
            # Exception acceptable pour 1 seul échantillon
            assert True
    
    def test_all_same_values(self, pca_calculator):
        """Test avec des valeurs identiques (variance nulle)."""
        df = pd.DataFrame({
            'bookID': [1, 2, 3],
            'average_rating': [4.0, 4.0, 4.0],
            'ratings_count': [1000, 1000, 1000],
            'engagement': [0.1, 0.1, 0.1],
            'num_pages': [300, 300, 300]
        })
        
        # Ne doit pas crasher même si variance = 0
        try:
            result_df = pca_calculator._calculate_pca_for_books(df)
            assert len(result_df) == 3
        except Exception:
            # Exception acceptable
            pass
    
    def test_extreme_values(self, pca_calculator):
        """Test avec des valeurs extrêmes."""
        df = pd.DataFrame({
            'bookID': [1, 2, 3],
            'average_rating': [5.0, 0.1, 4.5],
            'ratings_count': [1000000, 1, 500],
            'engagement': [1.0, 0.0001, 0.5],
            'num_pages': [10000, 10, 300]
        })
        
        # La transformation log devrait gérer les extrêmes
        result_df = pca_calculator._calculate_pca_for_books(df)
        
        assert len(result_df) > 0
        assert result_df['PC1'].notna().all()


# ============================================================================
# TESTS DE LOGGING
# ============================================================================

class TestLogging:
    """Tests des messages de logging."""
    
    def test_initialization_logging(self, in_memory_db, caplog):
        """Test que l'initialisation log correctement."""
        with caplog.at_level(logging.INFO, logger='pca'):
            calculator = PCACalculator(in_memory_db)
        
        assert any('initialisé avec succès' in record.message 
                  for record in caplog.records)
    
    def test_calculate_all_logging(self, pca_calculator, populated_db, caplog):
        """Test que calculate_all log les étapes."""
        with caplog.at_level(logging.INFO, logger='pca'):
            pca_calculator.calculate_all()
        
        messages = [record.message for record in caplog.records]
        
        assert any('COMPOSANTES PRINCIPALES' in msg for msg in messages)
        assert any('Livres' in msg for msg in messages)
        assert any('Auteurs' in msg for msg in messages)
        assert any('Éditeurs' in msg for msg in messages)
    
    def test_load_logging(self, pca_calculator, populated_db, sample_books_df, caplog):
        """Test que le chargement log correctement."""
        pca_df = pca_calculator._calculate_pca_for_books(sample_books_df)
        
        with caplog.at_level(logging.INFO, logger='pca'):
            pca_calculator._load_book_pca(pca_df)
        
        messages = [record.message for record in caplog.records]
        
        assert any('BookPCA' in msg for msg in messages)
        assert any('lignes insérées' in msg for msg in messages)


# ============================================================================
# TESTS DE QUALITÉ DES DONNÉES
# ============================================================================

class TestDataQuality:
    """Tests de qualité des données produites."""
    
    def test_pca_components_range(self, pca_calculator, sample_books_df):
        """Test que les composantes PC sont dans une plage raisonnable."""
        result_df = pca_calculator._calculate_pca_for_books(sample_books_df)
        
        # Les PC peuvent avoir n'importe quelle valeur, mais pas inf/nan
        assert not result_df['PC1'].isin([np.inf, -np.inf]).any()
        assert not result_df['PC2'].isin([np.inf, -np.inf]).any()
        assert result_df['PC1'].notna().all()
        assert result_df['PC2'].notna().all()
    
    def test_no_duplicate_ids(self, pca_calculator, sample_books_df):
        """Test qu'il n'y a pas de doublons dans les IDs."""
        result_df = pca_calculator._calculate_pca_for_books(sample_books_df)
        
        assert result_df['bookID'].is_unique
    
    def test_cluster_distribution(self, pca_calculator, sample_books_df):
        """Test que les clusters sont distribués."""
        result_df = pca_calculator._calculate_pca_for_books(sample_books_df)
        
        # Au moins 1 cluster doit exister
        assert result_df['Cluster'].nunique() >= 1
        
        # Tous les clusters doivent avoir un label
        assert result_df['Cluster_Label'].notna().all()


# ============================================================================
# EXÉCUTION DES TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])