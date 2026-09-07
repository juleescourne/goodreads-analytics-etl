"""
Tests unitaires pour le module CSVExtractor.

Author: Jules Courné
Date: 2025-12-31
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

import sys
from pathlib import Path

# Ajouter le chemin parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extract.csv_extractor import CSVExtractor
from src.utils.config_loader import ConfigLoader


class TestCSVExtractor:
    """Tests pour la classe CSVExtractor."""
    
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Fixture pour créer une configuration mock."""
        config = Mock(spec=ConfigLoader)
        
        # Créer les dossiers temporaires
        raw_data = tmp_path / "raw"
        processed = tmp_path / "processed"
        archive = tmp_path / "archive"
        
        raw_data.mkdir()
        processed.mkdir()
        archive.mkdir()
        
        # Configurer les retours du mock
        config.get.side_effect = lambda key, default=None: {
            'paths.raw_data': str(raw_data),
            'paths.processed_data': str(processed),
            'paths.archive': str(archive),
            'csv.encoding': 'utf-8',
            'csv.delimiter': ',',
            'csv.decimal': '.',
            'csv.skip_rows': 0,
            'pipeline.enable_archive': True,
            'pipeline.archive_format': '%Y%m%d_%H%M%S',
        }.get(key, default)
        
        return config
    
    @pytest.fixture
    def extractor(self, mock_config):
        """Fixture pour créer une instance de CSVExtractor."""
        return CSVExtractor(mock_config)
    
    @pytest.fixture
    def sample_csv(self, tmp_path, mock_config):
        """Fixture pour créer un fichier CSV de test."""
        csv_path = Path(mock_config.get('paths.raw_data')) / "test.csv"
        
        # Créer un DataFrame de test
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Book A', 'Book B', 'Book C'],
            'rating': [4.5, 3.8, 4.2]
        })
        
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def test_init_success(self, mock_config):
        """Test l'initialisation réussie de CSVExtractor."""
        extractor = CSVExtractor(mock_config)
        
        assert extractor.config == mock_config
        assert extractor.encoding == 'utf-8'
        assert extractor.delimiter == ','
        assert extractor.decimal == '.'
        assert extractor.skip_rows == 0
        assert extractor.enable_archive is True
    
    def test_init_with_custom_params(self, tmp_path):
        """Test l'initialisation avec des paramètres personnalisés."""
        config = Mock(spec=ConfigLoader)
        config.get.side_effect = lambda key, default=None: {
            'paths.raw_data': str(tmp_path / "raw"),
            'paths.processed_data': str(tmp_path / "processed"),
            'paths.archive': str(tmp_path / "archive"),
            'csv.encoding': 'latin-1',
            'csv.delimiter': ';',
            'csv.decimal': ',',
            'csv.skip_rows': 2,
            'pipeline.enable_archive': False,
            'pipeline.archive_format': '%Y-%m-%d',
        }.get(key, default)
        
        extractor = CSVExtractor(config)
        
        assert extractor.encoding == 'latin-1'
        assert extractor.delimiter == ';'
        assert extractor.decimal == ','
        assert extractor.skip_rows == 2
        assert extractor.enable_archive is False
    
    def test_extract_csv_success(self, extractor, sample_csv):
        """Test l'extraction réussie d'un fichier CSV."""
        df = extractor.extract_csv('test.csv')
        
        assert df is not None
        assert len(df) == 3
        assert list(df.columns) == ['id', 'name', 'rating']
        assert df['name'].iloc[0] == 'Book A'
    
    def test_extract_csv_file_not_found(self, extractor):
        """Test l'extraction d'un fichier inexistant."""
        df = extractor.extract_csv('nonexistent.csv')
        
        assert df is None
    
    def test_extract_csv_empty_file(self, extractor, tmp_path, mock_config):
        """Test l'extraction d'un fichier vide."""
        empty_csv = Path(mock_config.get('paths.raw_data')) / "empty.csv"
        empty_csv.touch()
        
        df = extractor.extract_csv('empty.csv')
        
        assert df is None
    
    def test_extract_csv_with_validation(self, extractor, sample_csv, mock_config):
        """Test l'extraction avec validation des colonnes."""
        mock_config.get.side_effect = lambda key, default=None: {
            'paths.raw_data': str(sample_csv.parent),
            'csv.expected_columns.books': ['id', 'name', 'rating'],
        }.get(key, default)
        
        df = extractor.extract_csv('test.csv', table_name='books')
        
        assert df is not None
        assert len(df) == 3
    
    def test_extract_csv_missing_columns(self, extractor, sample_csv, mock_config):
        """Test la validation avec des colonnes manquantes."""
        mock_config.get.side_effect = lambda key, default=None: {
            'paths.raw_data': str(sample_csv.parent),
            'csv.expected_columns.books': ['id', 'name', 'rating', 'author'],
        }.get(key, default)
        
        df = extractor.extract_csv('test.csv', table_name='books')
        
        # Le DataFrame doit être retourné malgré les colonnes manquantes
        assert df is not None
        assert 'author' not in df.columns
    
    def test_archive_file(self, extractor, sample_csv):
        """Test l'archivage d'un fichier."""
        extractor._archive_file(sample_csv)
        
        archive_path = extractor.archive_path
        archived_files = list(archive_path.glob('test_*.csv'))
        
        assert len(archived_files) == 1
        assert archived_files[0].stem.startswith('test_')
    
    def test_archive_disabled(self, extractor, sample_csv):
        """Test avec archivage désactivé."""
        extractor.enable_archive = False
        
        df = extractor.extract_csv('test.csv')
        
        archive_path = extractor.archive_path
        archived_files = list(archive_path.glob('test_*.csv'))
        
        assert df is not None
        assert len(archived_files) == 0
    
    def test_get_statistics(self, extractor):
        """Test la génération de statistiques."""
        df = pd.DataFrame({
            'A': [1, 2, 3, 1],
            'B': ['x', 'y', 'z', 'x'],
            'C': [1, 2.5, 3.5, 1],
            'D': ['x', 'y', 'z', 'x']
        })
        
        stats = extractor.get_statistics(df)

        assert stats['nb_lignes'] == 4
        assert stats['nb_colonnes'] == 4
        assert stats['colonnes'] == ['A', 'B', 'C', 'D']
        assert stats['nb_valeurs_manquantes']['B'] == 0
        assert stats['nb_doublons'] == 1
        assert 'types_donnees' in stats
    
    def test_get_statistics_empty_df(self, extractor):
        """Test les statistiques sur un DataFrame vide."""
        df = pd.DataFrame()
        
        stats = extractor.get_statistics(df)
        
        assert stats['nb_lignes'] == 0
        assert stats['nb_colonnes'] == 0
        assert stats['nb_doublons'] == 0
    
    def test_read_csv_with_custom_delimiter(self, tmp_path, mock_config):
        """Test la lecture d'un CSV avec délimiteur personnalisé."""
        mock_config.get.side_effect = lambda key, default=None: {
            'paths.raw_data': str(tmp_path),
            'paths.processed_data': str(tmp_path),
            'paths.archive': str(tmp_path),
            'csv.encoding': 'utf-8',
            'csv.delimiter': ';',
            'csv.decimal': '.',
            'csv.skip_rows': 0,
            'pipeline.enable_archive': False,
        }.get(key, default)
        
        # Créer un CSV avec délimiteur ;
        csv_path = tmp_path / "semicolon.csv"
        with open(csv_path, 'w') as f:
            f.write("id;name;value\n")
            f.write("1;Test;100\n")
        
        extractor = CSVExtractor(mock_config)
        df = extractor.extract_csv('semicolon.csv')
        
        assert df is not None
        assert len(df.columns) == 3
        assert df['name'].iloc[0] == 'Test'
    
    def test_unicode_error_handling(self, extractor, tmp_path, mock_config):
        """Test la gestion des erreurs d'encodage."""
        # Créer un fichier avec encodage différent
        bad_csv = Path(mock_config.get('paths.raw_data')) / "bad_encoding.csv"
        with open(bad_csv, 'wb') as f:
            f.write(b'\xff\xfe')  # BOM UTF-16
            f.write('test'.encode('utf-16-le'))
        
        df = extractor.extract_csv('bad_encoding.csv')
        
        # Devrait retourner None en cas d'erreur d'encodage
        assert df is None
    
    def test_validate_columns_no_expected(self, extractor):
        """Test la validation sans colonnes attendues."""
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        mock_config = extractor.config
        mock_config.get.return_value = None
        
        # Ne devrait pas lever d'exception
        extractor._validate_columns(df, 'test_table')
    
    @patch('shutil.copy2')
    def test_archive_file_failure(self, mock_copy, extractor, sample_csv):
        """Test la gestion d'erreur lors de l'archivage."""
        mock_copy.side_effect = PermissionError("Permission denied")
        
        # Ne devrait pas lever d'exception, juste un warning
        extractor._archive_file(sample_csv)
        
        mock_copy.assert_called_once()


class TestCSVExtractorIntegration:
    """Tests d'intégration pour CSVExtractor."""
    
    @pytest.fixture
    def integration_setup(self, tmp_path):
        """Setup pour les tests d'intégration."""
        # Créer la structure de dossiers
        raw = tmp_path / "data" / "raw"
        processed = tmp_path / "data" / "processed"
        archive = tmp_path / "data" / "archive"
        
        raw.mkdir(parents=True)
        processed.mkdir(parents=True)
        archive.mkdir(parents=True)
        
        # Créer un fichier CSV réaliste
        books_csv = raw / "books.csv"
        df = pd.DataFrame({
            'bookID': [1, 2, 3],
            'title': ['Book 1', 'Book 2', 'Book 3'],
            'authors': ['Author A', 'Author B', 'Author C'],
            'average_rating': [4.5, 3.8, 4.2],
            'isbn': ['123', '456', '789'],
            'language_code': ['eng', 'fra', 'eng'],
            'num_pages': [300, 250, 400],
            'ratings_count': [1000, 500, 750],
            'publication_date': ['2020-01-01', '2019-06-15', '2021-03-20']
        })
        df.to_csv(books_csv, index=False)
        
        # Créer la configuration
        config = Mock(spec=ConfigLoader)
        config.get.side_effect = lambda key, default=None: {
            'paths.raw_data': str(raw),
            'paths.processed_data': str(processed),
            'paths.archive': str(archive),
            'csv.encoding': 'utf-8',
            'csv.delimiter': ',',
            'csv.decimal': '.',
            'csv.skip_rows': 0,
            'pipeline.enable_archive': True,
            'pipeline.archive_format': '%Y%m%d_%H%M%S',
            'csv.expected_columns.books': ['bookID', 'title', 'authors', 'average_rating'],
        }.get(key, default)
        
        return {
            'config': config,
            'raw_path': raw,
            'archive_path': archive
        }
    
    def test_full_extraction_workflow(self, integration_setup):
        """Test le workflow complet d'extraction."""
        extractor = CSVExtractor(integration_setup['config'])
        
        # Extraire le fichier
        df = extractor.extract_csv('books.csv', table_name='books')
        
        # Vérifications
        assert df is not None
        assert len(df) == 3
        assert 'bookID' in df.columns
        assert 'title' in df.columns
        
        # Vérifier que le fichier a été archivé
        archive_files = list(integration_setup['archive_path'].glob('books_*.csv'))
        assert len(archive_files) == 1
        
        # Vérifier les statistiques
        stats = extractor.get_statistics(df)
        assert stats['nb_lignes'] == 3
        assert stats['nb_colonnes'] == 9
        assert stats['nb_doublons'] == 0