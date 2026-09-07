
# -*- coding: utf-8 -*-
"""
Tests unitaires pour le module ConfigLoader.

Ce module teste toutes les fonctionnalités de la classe ConfigLoader :
- Chargement des configurations YAML
- Initialisation du logging
- Création des répertoires
- Accès aux valeurs de configuration
- Gestion des erreurs

Author:
    Jules Courné

Date:
    2025-01-01
"""

import logging
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock

import pytest
import yaml

from src.utils.config_loader import ConfigLoader


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def sample_config():
    """Configuration de test valide."""
    return {
        'paths': {
            'raw_data': 'data/raw',
            'processed_data': 'data/processed',
            'archive': 'data/archive',
            'logs': 'logs',
            'database': 'data/db/pipeline.db'
        },
        'database': {
            'name': 'pipeline.db',
            'tables': [
                {
                    'name': 'users',
                    'schema': 'CREATE TABLE users (id INTEGER PRIMARY KEY)'
                },
                {
                    'name': 'transactions',
                    'schema': 'CREATE TABLE transactions (id INTEGER PRIMARY KEY)'
                }
            ]
        },
        'processing': {
            'batch_size': 100,
            'timeout': 30
        }
    }


@pytest.fixture
def sample_logging_config():
    """Configuration de logging de test."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        }
    }


@pytest.fixture
def temp_config_files(tmp_path, sample_config, sample_logging_config):
    """Crée des fichiers de configuration temporaires."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    config_file = config_dir / "config.yaml"
    logging_file = config_dir / "logging_config.yaml"
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_config, f)
    
    with open(logging_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_logging_config, f)
    
    return str(config_file), str(logging_file)


# ========================================
# Tests d'initialisation
# ========================================

class TestConfigLoaderInit:
    """Tests de l'initialisation de ConfigLoader."""
    
    def test_init_with_default_paths(self, sample_config, sample_logging_config):
        """Test l'initialisation avec les chemins par défaut."""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.side_effect = [sample_config, sample_logging_config]
                with patch('pathlib.Path.mkdir'):
                    loader = ConfigLoader()
                    
                    assert loader.config == sample_config
                    assert loader.config_path == Path("config/config.yaml")
                    assert loader.logging_config_path == Path("config/logging_config.yaml")
    
    def test_init_with_custom_paths(self, sample_config, sample_logging_config):
        """Test l'initialisation avec des chemins personnalisés."""
        custom_config = "custom/config.yaml"
        custom_logging = "custom/logging.yaml"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.side_effect = [sample_config, sample_logging_config]
                with patch('pathlib.Path.mkdir'):
                    loader = ConfigLoader(custom_config, custom_logging)
                    
                    assert loader.config_path == Path(custom_config)
                    assert loader.logging_config_path == Path(custom_logging)
    
    def test_init_creates_directories(self, temp_config_files, tmp_path):
        """Test que l'initialisation crée les répertoires nécessaires."""
        config_file, logging_file = temp_config_files
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            loader = ConfigLoader(config_file, logging_file)
            
            # Vérifie que mkdir a été appelé pour chaque répertoire
            assert mock_mkdir.call_count >= 5  # raw, processed, archive, logs, db parent


# ========================================
# Tests de chargement de configuration
# ========================================

class TestLoadConfig:
    """Tests du chargement de la configuration."""
    
    def test_load_config_success(self, temp_config_files):
        """Test le chargement réussi de la configuration."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.config is not None
        assert 'paths' in loader.config
        assert 'database' in loader.config
    
    def test_load_config_file_not_found(self):
        """Test l'erreur si le fichier de configuration n'existe pas."""
        with pytest.raises(FileNotFoundError) as exc_info:
            ConfigLoader("nonexistent/config.yaml", "nonexistent/logging.yaml")
        
        assert "non trouvé" in str(exc_info.value)
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test l'erreur si le YAML est invalide."""
        config_file = tmp_path / "invalid_config.yaml"
        logging_file = tmp_path / "logging.yaml"
        
        # Créer un fichier YAML invalide
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [\n")
        
        with open(logging_file, 'w') as f:
            yaml.dump({'version': 1}, f)
        
        with pytest.raises(ValueError) as exc_info:
            ConfigLoader(str(config_file), str(logging_file))
        
        assert "parsing du YAML" in str(exc_info.value)


# ========================================
# Tests de configuration du logging
# ========================================

class TestSetupLogging:
    """Tests de la configuration du logging."""
    
    def test_setup_logging_success(self, temp_config_files, caplog):
        """Test la configuration réussie du logging."""
        config_file, logging_file = temp_config_files
        
        with caplog.at_level(logging.INFO):
            loader = ConfigLoader(config_file, logging_file)
        
        # Le logging devrait être configuré sans erreur
        assert loader.config is not None
    
    def test_setup_logging_file_not_found(self, temp_config_files, caplog):
        """Test le fallback si le fichier de logging n'existe pas."""
        config_file, _ = temp_config_files
        
        with caplog.at_level(logging.WARNING):
            loader = ConfigLoader(config_file, "nonexistent_logging.yaml")
        
        # Vérifie qu'un avertissement a été émis
        assert any("configuration par défaut" in record.message for record in caplog.records)
    

# ========================================
# Tests d'accès aux valeurs
# ========================================

class TestGetMethods:
    """Tests des méthodes d'accès aux valeurs de configuration."""
    
    def test_get_simple_key(self, temp_config_files):
        """Test l'accès à une clé simple."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.get('paths') is not None
        assert isinstance(loader.get('paths'), dict)
    
    def test_get_nested_key(self, temp_config_files):
        """Test l'accès à une clé imbriquée avec notation pointée."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.get('paths.raw_data') == 'data/raw'
        assert loader.get('database.name') == 'pipeline.db'
        assert loader.get('processing.batch_size') == 100
    
    def test_get_nonexistent_key(self, temp_config_files):
        """Test l'accès à une clé inexistante."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.get('nonexistent.key') is None
        assert loader.get('nonexistent.key', 'default') == 'default'
    
    def test_get_with_list_index(self, temp_config_files):
        """Test l'accès à un élément de liste par index."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        first_table = loader.get('database.tables.0')
        assert first_table is not None
        assert first_table['name'] == 'users'
    
    def test_get_invalid_list_index(self, temp_config_files):
        """Test l'accès à un index de liste invalide."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.get('database.tables.999') is None
        assert loader.get('database.tables.invalid') is None
    
    def test_get_all(self, temp_config_files):
        """Test la récupération de toute la configuration."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        config = loader.get_all()
        assert isinstance(config, dict)
        assert 'paths' in config
        assert 'database' in config
    
    def test_get_db_path(self, temp_config_files):
        """Test la récupération du chemin de la base de données."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        db_path = loader.get_db_path()
        assert db_path == 'data/db/pipeline.db'
    
    def test_get_table_schemas(self, temp_config_files):
        """Test la récupération des schémas de tables."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        schemas = loader.get_table_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) == 2
        assert schemas[0]['name'] == 'users'
        assert schemas[1]['name'] == 'transactions'


# ========================================
# Tests de vérification de clés
# ========================================

class TestHasKey:
    """Tests de la méthode has_key."""
    
    def test_has_key_exists(self, temp_config_files):
        """Test la vérification d'une clé existante."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.has_key('paths.raw_data') is True
        assert loader.has_key('database.name') is True
    
    def test_has_key_not_exists(self, temp_config_files):
        """Test la vérification d'une clé inexistante."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.has_key('nonexistent.key') is False
        assert loader.has_key('paths.nonexistent') is False


# ========================================
# Tests de rechargement
# ========================================

class TestReload:
    """Tests de la méthode reload."""
    
    def test_reload_success(self, temp_config_files, sample_config):
        """Test le rechargement réussi de la configuration."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        # Modifier la configuration
        sample_config['paths']['raw_data'] = 'new_data/raw'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f)
        
        # Recharger
        loader.reload()
        
        assert loader.get('paths.raw_data') == 'new_data/raw'
    
    def test_reload_file_deleted(self, temp_config_files):
        """Test le rechargement après suppression du fichier."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        # Supprimer le fichier
        Path(config_file).unlink()
        
        # Le rechargement devrait échouer
        with pytest.raises(FileNotFoundError):
            loader.reload()


# ========================================
# Tests d'intégration
# ========================================

class TestIntegration:
    """Tests d'intégration complets."""
    
    def test_full_workflow(self, temp_config_files):
        """Test un workflow complet d'utilisation."""
        config_file, logging_file = temp_config_files
        
        # Initialiser
        loader = ConfigLoader(config_file, logging_file)
        
        # Accéder aux valeurs
        assert loader.get('paths.raw_data') == 'data/raw'
        assert loader.get_db_path() == 'data/db/pipeline.db'
        assert len(loader.get_table_schemas()) == 2
        
        # Vérifier les clés
        assert loader.has_key('database.name')
        assert not loader.has_key('nonexistent')
        
        # Obtenir toute la config
        config = loader.get_all()
        assert 'paths' in config
    
    def test_edge_cases(self, temp_config_files):
        """Test les cas limites."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        # Clé vide
        assert loader.get('') is None
        
        # Plusieurs niveaux d'imbrication
        assert loader.get('database.tables.0.name') == 'users'
        
        # Valeur par défaut
        assert loader.get('nonexistent', 42) == 42


# ========================================
# Tests paramétrés
# ========================================

class TestParametrized:
    """Tests paramétrés pour différents scénarios."""
    
    @pytest.mark.parametrize("key,expected", [
        ('paths.raw_data', 'data/raw'),
        ('paths.processed_data', 'data/processed'),
        ('paths.archive', 'data/archive'),
        ('database.name', 'pipeline.db'),
        ('processing.batch_size', 100),
    ])
    def test_multiple_keys(self, temp_config_files, key, expected):
        """Test l'accès à plusieurs clés différentes."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.get(key) == expected
    
    @pytest.mark.parametrize("invalid_key", [
        'nonexistent',
        'paths.nonexistent',
        'database.invalid.key',
        'a.b.c.d.e.f',
    ])
    def test_invalid_keys(self, temp_config_files, invalid_key):
        """Test l'accès à plusieurs clés invalides."""
        config_file, logging_file = temp_config_files
        loader = ConfigLoader(config_file, logging_file)
        
        assert loader.get(invalid_key) is None