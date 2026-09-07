# -*- coding: utf-8 -*-

"""
Tests unitaires pour le module DatabaseConnection.

Author: Jules Courné
Date: 2025-12-31
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Ajouter le chemin parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load.database_connection import (
    DatabaseConnection,
    create_database,
    get_connection,
    close_connection,
    rollback_connection,
    commit_connection
)
from src.utils.config_loader import ConfigLoader


class TestDatabaseConnection:
    """Tests pour la classe DatabaseConnection."""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset le singleton avant chaque test."""
        DatabaseConnection._instance = None
        DatabaseConnection._connection = None
        yield
        # Cleanup après chaque test
        if DatabaseConnection._connection:
            try:
                DatabaseConnection._connection.close()
            except:
                pass
        DatabaseConnection._instance = None
        DatabaseConnection._connection = None
    
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Fixture pour créer une configuration mock."""
        config = Mock(spec=ConfigLoader)
        
        db_path = tmp_path / "test.db"
        
        # Configuration des tables de test
        tables = [
            {
                'name': 'test_table',
                'schema': '''
                    CREATE TABLE IF NOT EXISTS test_table (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        value INTEGER
                    )
                '''
            },
            {
                'name': 'test_table2',
                'schema': '''
                    CREATE TABLE IF NOT EXISTS test_table2 (
                        id INTEGER PRIMARY KEY,
                        test_id INTEGER,
                        FOREIGN KEY (test_id) REFERENCES test_table(id)
                    )
                '''
            }
        ]
        
        # Configuration des index
        indexes = [
            {
                'name': 'idx_test_name',
                'schema': 'CREATE INDEX IF NOT EXISTS idx_test_name ON test_table(name)'
            }
        ]
        
        config.get_db_path.return_value = str(db_path)
        config.get.side_effect = lambda key, default=None: {
            'database.timeout': 30,
            'database.tables': tables,
            'database.indexes': indexes,
        }.get(key, default)
        
        return config
    
    def test_singleton_pattern(self, mock_config):
        """Test que la classe implémente correctement le pattern Singleton."""
        db1 = DatabaseConnection(mock_config)
        db2 = DatabaseConnection(mock_config)
        
        assert db1 is db2
        assert id(db1) == id(db2)
    
    def test_init_first_time(self, mock_config):
        """Test l'initialisation de la première instance."""
        db = DatabaseConnection(mock_config)
        
        assert db.config == mock_config
        assert db.logger is not None
        assert db.initialized is True
        assert db.db_path is None
    
    def test_init_already_initialized(self, mock_config):
        """Test que l'initialisation ne se reproduit pas."""
        db1 = DatabaseConnection(mock_config)
        original_config = db1.config
        
        # Deuxième initialisation avec une config différente
        new_config = Mock()
        db2 = DatabaseConnection(new_config)
        
        # La config ne doit pas changer
        assert db2.config == original_config
        assert db1 is db2
    
    def test_create_database_success(self, mock_config, tmp_path):
        """Test la création réussie de la base de données."""
        db = DatabaseConnection(mock_config)
        conn = db.create_database()
        
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        assert db.db_path is not None
        
        # Vérifier que le fichier existe
        db_file = Path(db.db_path)
        assert db_file.exists()
        
        # Vérifier que les clés étrangères sont activées
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1
    
    def test_create_database_with_explicit_path(self, tmp_path):
        """Test la création avec un chemin explicite."""
        db = DatabaseConnection()
        db_path = tmp_path / "explicit.db"
        
        conn = db.create_database(str(db_path))
        
        assert conn is not None
        assert Path(db_path).exists()
        assert db.db_path == str(db_path)
    
    def test_create_database_creates_parent_directory(self, mock_config, tmp_path):
        """Test que les répertoires parents sont créés."""
        db_path = tmp_path / "nested" / "dir" / "test.db"
        
        db = DatabaseConnection(mock_config)
        db.create_database(str(db_path))
        
        assert db_path.parent.exists()
        assert db_path.exists()
    
    def test_create_database_no_path_no_config(self):
        """Test l'erreur quand aucun chemin n'est fourni."""
        db = DatabaseConnection()
        
        with pytest.raises(ValueError, match="Aucun chemin de base de données fourni"):
            db.create_database()
    
    def test_create_tables_success(self, mock_config):
        """Test la création des tables."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        # Vérifier que les tables existent
        assert db.table_exists('test_table')
        assert db.table_exists('test_table2')
    
    def test_create_tables_no_config(self, tmp_path):
        """Test la création sans configuration."""
        db = DatabaseConnection()
        db_path = tmp_path / "test.db"
        db.create_database(str(db_path))
        
        # Devrait réussir mais sans créer de tables
        conn = db.get_connection()
        assert conn is not None
    
    def test_create_tables_invalid_definition(self, mock_config):
        """Test avec une définition de table invalide."""
        # Modifier la config pour avoir une table invalide
        mock_config.get.side_effect = lambda key, default=None: {
            'database.timeout': 30,
            'database.tables': [
                {'name': 'invalid_table'}  # Pas de schema
            ],
        }.get(key, default)
        
        db = DatabaseConnection(mock_config)
        # Ne devrait pas lever d'exception, juste un warning
        db.create_database()
    
    def test_create_tables_sql_error(self, mock_config):
        """Test avec une erreur SQL dans le schéma."""
        mock_config.get.side_effect = lambda key, default=None: {
            'database.timeout': 30,
            'database.tables': [
                {
                    'name': 'bad_table',
                    'schema': 'CREATE TABLE bad syntax error'
                }
            ],
        }.get(key, default)
        
        db = DatabaseConnection(mock_config)
        
        with pytest.raises(sqlite3.Error):
            db.create_database()
    
    def test_get_connection_success(self, mock_config):
        """Test la récupération de la connexion."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        conn = db.get_connection()
        
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
    
    def test_get_connection_not_initialized(self):
        """Test l'erreur quand la base n'est pas initialisée."""
        db = DatabaseConnection()
        
        with pytest.raises(RuntimeError, match="Base de données non initialisée"):
            db.get_connection()
    
    def test_commit_success(self, mock_config):
        """Test le commit d'une transaction."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        # Insérer des données
        conn = db.get_connection()
        conn.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("Test", 42))
        
        # Commit
        db.commit()
        
        # Vérifier que les données sont persistées
        cursor = conn.execute("SELECT * FROM test_table")
        assert cursor.fetchone() is not None
    
    def test_rollback_success(self, mock_config):
        """Test le rollback d'une transaction."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        conn = db.get_connection()
        
        # Insérer des données
        conn.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("Test", 42))
        
        # Rollback
        db.rollback()
        
        # Vérifier que les données ne sont pas persistées
        cursor = conn.execute("SELECT * FROM test_table")
        assert cursor.fetchone() is None
    
    def test_close_connection(self, mock_config):
        """Test la fermeture de la connexion."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        db.close()
        
        assert DatabaseConnection._connection is None
        
        # Vérifier qu'on ne peut plus utiliser la connexion
        with pytest.raises(RuntimeError):
            db.get_connection()
    
    def test_execute_query_simple(self, mock_config):
        """Test l'exécution d'une requête simple."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        cursor = db.execute_query("SELECT 1")
        result = cursor.fetchone()
        
        assert result == (1,)
    
    def test_execute_query_with_params(self, mock_config):
        """Test l'exécution d'une requête avec paramètres."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        db.execute_query(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("Test", 42)
        )
        db.commit()
        
        cursor = db.execute_query("SELECT name, value FROM test_table WHERE name = ?", ("Test",))
        result = cursor.fetchone()
        
        assert result == ("Test", 42)
    
    def test_execute_query_error(self, mock_config):
        """Test la gestion d'erreur dans execute_query."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        with pytest.raises(sqlite3.Error):
            db.execute_query("SELECT * FROM nonexistent_table")
    
    def test_execute_many(self, mock_config):
        """Test l'insertion multiple de données."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        data = [
            ("Name1", 10),
            ("Name2", 20),
            ("Name3", 30),
        ]
        
        db.execute_many(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            data
        )
        db.commit()
        
        # Vérifier l'insertion
        count = db.get_table_count('test_table')
        assert count == 3
    
    def test_execute_many_error(self, mock_config):
        """Test la gestion d'erreur dans execute_many."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        data = [("Name1", 10)]
        
        with pytest.raises(sqlite3.Error):
            db.execute_many("INSERT INTO nonexistent_table VALUES (?, ?)", data)
    
    def test_transaction_context_manager_success(self, mock_config):
        """Test le context manager transaction avec succès."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        with db.transaction() as conn:
            conn.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("Test", 42))
        
        # Vérifier que les données sont committées
        count = db.get_table_count('test_table')
        assert count == 1
    
    def test_transaction_context_manager_rollback(self, mock_config):
        """Test le context manager transaction avec rollback."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        try:
            with db.transaction() as conn:
                conn.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("Test", 42))
                raise ValueError("Erreur simulée")
        except ValueError:
            pass
        
        # Vérifier que les données ne sont pas committées
        count = db.get_table_count('test_table')
        assert count == 0
    
    def test_create_indexes_success(self, mock_config):
        """Test la création d'index."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        db.create_indexes()
        
        # Vérifier que l'index existe
        cursor = db.get_connection().cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_test_name'"
        )
        assert cursor.fetchone() is not None
    
    def test_create_indexes_no_config(self, tmp_path):
        """Test la création d'index sans configuration."""
        db = DatabaseConnection()
        db.create_database(str(tmp_path / "test.db"))
        
        # Ne devrait pas lever d'exception
        db.create_indexes()
    
    def test_create_indexes_invalid_definition(self, mock_config):
        """Test avec une définition d'index invalide."""
        mock_config.get.side_effect = lambda key, default=None: {
            'database.timeout': 30,
            'database.tables': [],
            'database.indexes': [
                {'name': 'invalid_index'}  # Pas de schema
            ],
        }.get(key, default)
        
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        # Ne devrait pas lever d'exception, juste un warning
        db.create_indexes()
    
    def test_create_indexes_sql_error(self, mock_config):
        """Test avec une erreur SQL dans l'index."""
        mock_config.get.side_effect = lambda key, default=None: {
            'database.timeout': 30,
            'database.tables': [],
            'database.indexes': [
                {
                    'name': 'bad_index',
                    'schema': 'CREATE INDEX bad syntax error'
                }
            ],
        }.get(key, default)
        
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        with pytest.raises(sqlite3.Error):
            db.create_indexes()
    
    def test_get_table_count(self, mock_config):
        """Test le comptage de lignes dans une table."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        # Insérer des données
        data = [("Name1", 10), ("Name2", 20), ("Name3", 30)]
        db.execute_many("INSERT INTO test_table (name, value) VALUES (?, ?)", data)
        db.commit()
        
        count = db.get_table_count('test_table')
        
        assert count == 3
    
    def test_get_table_count_empty(self, mock_config):
        """Test le comptage sur une table vide."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        count = db.get_table_count('test_table')
        
        assert count == 0
    
    def test_table_exists_true(self, mock_config):
        """Test la vérification d'existence d'une table existante."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        assert db.table_exists('test_table') is True
    
    def test_table_exists_false(self, mock_config):
        """Test la vérification d'existence d'une table inexistante."""
        db = DatabaseConnection(mock_config)
        db.create_database()
        
        assert db.table_exists('nonexistent_table') is False


class TestUtilityFunctions:
    """Tests pour les fonctions utilitaires."""
    
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
    def mock_config(self, tmp_path):
        """Fixture pour créer une configuration mock."""
        config = Mock(spec=ConfigLoader)
        db_path = tmp_path / "test.db"
        
        config.get_db_path.return_value = str(db_path)
        config.get.side_effect = lambda key, default=None: {
            'database.timeout': 30,
            'database.tables': [],
            'database.indexes': [],
        }.get(key, default)
        
        return config
    
    def test_create_database_utility(self, mock_config):
        """Test la fonction utilitaire create_database."""
        conn = create_database(mock_config)
        
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
    
    def test_get_connection_utility(self, mock_config):
        """Test la fonction utilitaire get_connection."""
        create_database(mock_config)
        conn = get_connection()
        
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
    
    def test_close_connection_utility(self, mock_config):
        """Test la fonction utilitaire close_connection."""
        create_database(mock_config)
        close_connection()
        
        assert DatabaseConnection._connection is None
    
    def test_commit_connection_utility(self, mock_config):
        """Test la fonction utilitaire commit_connection."""
        create_database(mock_config)
        
        # Ne devrait pas lever d'exception
        commit_connection()
    
    def test_rollback_connection_utility(self, mock_config):
        """Test la fonction utilitaire rollback_connection."""
        create_database(mock_config)
        
        # Ne devrait pas lever d'exception
        rollback_connection()


class TestDatabaseConnectionIntegration:
    """Tests d'intégration pour DatabaseConnection."""
    
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
    def full_config(self, tmp_path):
        """Configuration complète pour tests d'intégration."""
        config = Mock(spec=ConfigLoader)
        db_path = tmp_path / "integration.db"
        
        tables = [
            {
                'name': 'users',
                'schema': '''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE
                    )
                '''
            },
            {
                'name': 'posts',
                'schema': '''
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                '''
            }
        ]
        
        indexes = [
            {
                'name': 'idx_users_email',
                'schema': 'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'
            },
            {
                'name': 'idx_posts_user',
                'schema': 'CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)'
            }
        ]
        
        config.get_db_path.return_value = str(db_path)
        config.get.side_effect = lambda key, default=None: {
            'database.timeout': 30,
            'database.tables': tables,
            'database.indexes': indexes,
        }.get(key, default)
        
        return config
    
    def test_full_workflow(self, full_config):
        """Test le workflow complet de création et utilisation."""
        # Créer la base
        db = DatabaseConnection(full_config)
        db.create_database()
        
        # Créer les index
        db.create_indexes()
        
        # Insérer des utilisateurs
        users = [
            ("Alice", "alice@example.com"),
            ("Bob", "bob@example.com"),
            ("Charlie", "charlie@example.com"),
        ]
        db.execute_many(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            users
        )
        db.commit()
        
        # Vérifier les utilisateurs
        assert db.get_table_count('users') == 3
        
        # Insérer des posts
        with db.transaction():
            for i in range(1, 4):
                db.execute_query(
                    "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
                    (i, f"Title {i}", f"Content {i}")
                )
        
        # Vérifier les posts
        assert db.get_table_count('posts') == 3
        
        # Vérifier les clés étrangères
        cursor = db.execute_query(
            "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id"
        )
        results = cursor.fetchall()
        assert len(results) == 3
        
        # Fermer
        db.close()