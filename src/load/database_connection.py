# -*- coding: utf-8 -*-
# src/load/database_connection.py
"""
Module de gestion de la connexion à la base de données SQLite.

Ce module fournit une classe singleton pour gérer la connexion SQLite,
les transactions, et les opérations de base de données avec gestion
automatique des erreurs et du logging.

Author:
    
    Jules Courné

Date:
    2025-12-31
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Tuple

from src.utils.config_loader import ConfigLoader


class DatabaseConnection:
    """
    Gestionnaire de connexion SQLite avec pattern Singleton.
    
    Cette classe implémente le pattern Singleton pour garantir une seule
    instance de connexion à la base de données. Elle gère les transactions,
    la création de tables et d'index, ainsi que les opérations CRUD.
    
    Attributes:
        config (ConfigLoader): Instance de configuration.
        logger (logging.Logger): Logger pour les opérations de base de données.
        db_path (Optional[str]): Chemin vers le fichier de base de données.
        initialized (bool): Indicateur d'initialisation.
    
    Note:
        Cette classe utilise le pattern Singleton. Toutes les instances
        partagent la même connexion à la base de données.

    """
    
    _instance: Optional['DatabaseConnection'] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls, config: Optional[ConfigLoader] = None) -> 'DatabaseConnection':
        """
        Implémente le pattern Singleton.
        
        Args:
            config (Optional[ConfigLoader]): Instance de configuration.
        
        Returns:
            DatabaseConnection: Instance unique de la classe.
        """
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[ConfigLoader] = None) -> None:
        """
        Initialise la connexion à la base de données.
        
        Args:
            config (Optional[ConfigLoader]): Instance de ConfigLoader pour
                charger les paramètres de configuration.
        
        Note:
            L'initialisation ne se produit qu'une seule fois grâce au
            pattern Singleton.
        """
        if not hasattr(self, 'initialized'):
            self.config = config
            self.logger = logging.getLogger('load')
            self.db_path: Optional[str] = None
            self.initialized = True
    
    def create_database(self, db_path: Optional[str] = None) -> sqlite3.Connection:
        """
        Crée la base de données et toutes les tables définies.
        
        Crée le fichier de base de données SQLite, active les clés étrangères,
        et crée toutes les tables définies dans la configuration.
        
        Args:
            db_path (Optional[str]): Chemin vers le fichier de base de données.
                Si None, utilise le chemin de la configuration.
        
        Returns:
            sqlite3.Connection: Connexion active à la base de données.
        
        Raises:
            ValueError: Si aucun chemin n'est fourni et aucune config n'existe.
            sqlite3.Error: En cas d'erreur lors de la création de la base.
        

        """
        # Déterminer le chemin de la base
        if db_path is None:
            if self.config:
                db_path = self.config.get_db_path()
            else:
                raise ValueError("Aucun chemin de base de données fourni")
        
        self.db_path = db_path
        
        # Créer le répertoire parent si nécessaire
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Création de la base de données : {db_path}")
        
        try:
            # Obtenir le timeout depuis la config
            timeout = 30
            if self.config:
                timeout = self.config.get('database.timeout', 30)
            
            # Créer la connexion
            self._connection = sqlite3.connect(
                db_path,
                timeout=timeout,
                check_same_thread=False
            )
            
            # Activer les clés étrangères
            self._connection.execute("PRAGMA foreign_keys = ON")
            
            # Créer les tables
            self._create_tables()
            
            self.logger.info("✓ Base de données créée avec succès")
            
            return self._connection
            
        except sqlite3.Error as e:
            self.logger.error(f"Erreur lors de la création de la base : {e}")
            raise
    
    def _create_tables(self) -> None:
        """
        Crée toutes les tables définies dans la configuration.
        
        Parcourt la liste des tables dans la configuration et exécute
        leur schéma SQL pour les créer.
        
        Raises:
            sqlite3.Error: En cas d'erreur lors de la création d'une table.
        
        Note:
            Les erreurs de création de tables sont loggées et propagées.
        """
        self.logger.info("Création des tables...")
        
        if not self.config:
            self.logger.warning("Aucune configuration fournie, tables non créées")
            return
        
        cursor = self._connection.cursor()
        tables = self.config.get('database.tables', [])
        
        for table_def in tables:
            table_name = table_def.get('name')
            schema = table_def.get('schema')
            
            if not table_name or not schema:
                self.logger.warning(f"Définition de table invalide : {table_def}")
                continue
            
            try:
                cursor.execute(schema)
                self.logger.info(f"   Table '{table_name}' créée")
            except sqlite3.Error as e:
                self.logger.error(f"    Erreur création table '{table_name}': {e}")
                raise
        
        self._connection.commit()
        self.logger.info("✓ Toutes les tables créées")

    def get_connection(self) -> sqlite3.Connection:
        """
        Retourne la connexion active à la base de données.
        
        Returns:
            sqlite3.Connection: Connexion SQLite active.
        
        Raises:
            RuntimeError: Si la base de données n'a pas été initialisée.
        
        """
        if self._connection is None:
            raise RuntimeError(
                "Base de données non initialisée. "
                "Appelez create_database() d'abord."
            )
        
        return self._connection
    
    def commit(self) -> None:
        """
        Valide les changements en cours (commit).
        
        Raises:
            sqlite3.Error: En cas d'erreur lors du commit.
        
        """
        if self._connection:
            try:
                self._connection.commit()
                self.logger.debug("Transaction committée")
            except sqlite3.Error as e:
                self.logger.error(f"Erreur lors du commit : {e}")
                raise
    
    def rollback(self) -> None:
        """
        Annule les changements en cours (rollback).
        
        Raises:
            sqlite3.Error: En cas d'erreur lors du rollback.
        

        """
        if self._connection:
            try:
                self._connection.rollback()
                self.logger.warning("Transaction annulée (rollback)")
            except sqlite3.Error as e:
                self.logger.error(f"Erreur lors du rollback : {e}")
                raise
    
    def close(self) -> None:
        """
        Ferme la connexion à la base de données.
        
        Ferme proprement la connexion SQLite et libère les ressources.
        
        Raises:
            sqlite3.Error: En cas d'erreur lors de la fermeture.
        
        Note:
            Après fermeture, il faudra rappeler create_database() pour
            réutiliser la connexion.
        """
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                self.logger.info("  Connexion à la base de données fermée")
            except sqlite3.Error as e:
                self.logger.error(f"Erreur lors de la fermeture : {e}")
                raise
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> sqlite3.Cursor:
        """
        Exécute une requête SQL unique.
        
        Args:
            query (str): Requête SQL à exécuter.
            params (Optional[Tuple]): Paramètres de la requête préparée.
        
        Returns:
            sqlite3.Cursor: Curseur contenant les résultats.
        
        Raises:
            sqlite3.Error: En cas d'erreur lors de l'exécution.
        
        """
        cursor = self._connection.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.Error as e:
            self.logger.error(f"Erreur lors de l'exécution de la requête : {e}")
            self.logger.error(f"Requête : {query}")
            raise
    
    def execute_many(self, query: str, data: List[Tuple]) -> None:
        """
        Exécute une requête pour plusieurs lignes de données.
        
        Utilise executemany() pour des insertions en masse plus performantes.
        
        Args:
            query (str): Requête SQL avec placeholders (?).
            data (List[Tuple]): Liste de tuples contenant les données.
        
        Raises:
            sqlite3.Error: En cas d'erreur lors de l'insertion.
        
        """
        cursor = self._connection.cursor()
        
        try:
            cursor.executemany(query, data)
            self.logger.debug(f"Insertion de {len(data)} lignes")
        except sqlite3.Error as e:
            self.logger.error(f"Erreur lors de l'insertion multiple : {e}")
            self.logger.error(f"Requête : {query}")
            raise
    
    @contextmanager
    def transaction(self):
        """
        Context manager pour gérer automatiquement les transactions.
        
        Commit automatique en cas de succès, rollback en cas d'exception.
        
        Yields:
            sqlite3.Connection: Connexion active pour la transaction.
        
        Raises:
            Exception: Propage toute exception après rollback.
        
        """
        try:
            yield self._connection
            self.commit()
            self.logger.debug("Transaction réussie")
        except Exception as e:
            self.rollback()
            self.logger.error(f"Transaction échouée : {e}")
            raise
    
    def create_indexes(self) -> None:
        """
        Crée les index définis dans la configuration.
        
        Parcourt la liste des index dans la configuration et les crée
        pour améliorer les performances des requêtes.
        
        Raises:
            sqlite3.Error: En cas d'erreur lors de la création d'un index.
        
        """
        self.logger.info("Création des index...")
        
        if not self.config:
            self.logger.warning("Aucune configuration fournie, index non créés")
            return
        
        cursor = self._connection.cursor()
        indexes = self.config.get('database.indexes', [])
        
        for index in indexes:
            index_name = index.get('name')
            schema = index.get('schema')
            
            if not index_name or not schema:
                self.logger.warning(f"Définition d'index invalide : {index}")
                continue
            
            try:
                cursor.execute(schema)
                self.logger.info(f"  Index '{index_name}' créé")
            except sqlite3.Error as e:
                self.logger.error(f"    Erreur création index '{index_name}': {e}")
                raise
        
        self._connection.commit()
        self.logger.info("  Index créés")
    
    def get_table_count(self, table_name: str) -> int:
        """
        Retourne le nombre de lignes dans une table.
        
        Args:
            table_name (str): Nom de la table à compter.
        
        Returns:
            int: Nombre de lignes dans la table.
        
        """
        cursor = self._connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return count
    
    def table_exists(self, table_name: str) -> bool:
        """
        Vérifie si une table existe dans la base de données.
        
        Args:
            table_name (str): Nom de la table à vérifier.
        
        Returns:
            bool: True si la table existe, False sinon.
        
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None


# ============================================================================
# Fonctions utilitaires pour compatibilité avec le code existant
# ============================================================================

def create_database(config: Optional[ConfigLoader] = None) -> sqlite3.Connection:
    """
    Crée la base de données (fonction utilitaire).
    
    Args:
        config (Optional[ConfigLoader]): Instance de configuration.
    
    Returns:
        sqlite3.Connection: Connexion à la base de données.
    
    """
    db_conn = DatabaseConnection(config)
    return db_conn.create_database()


def get_connection() -> sqlite3.Connection:
    """
    Retourne la connexion active (fonction utilitaire).
    
    Returns:
        sqlite3.Connection: Connexion SQLite active.
    
    """
    db_conn = DatabaseConnection()
    return db_conn.get_connection()


def close_connection(conn: Optional[sqlite3.Connection] = None) -> None:
    """
    Ferme la connexion (fonction utilitaire).
    
    Args:
        conn (Optional[sqlite3.Connection]): Connexion (ignoré, pour compatibilité).
    
    """
    db_conn = DatabaseConnection()
    db_conn.close()


def rollback_connection(conn: Optional[sqlite3.Connection] = None) -> None:
    """
    Annule la transaction (fonction utilitaire).
    
    Args:
        conn (Optional[sqlite3.Connection]): Connexion (ignoré, pour compatibilité).
    
    """
    db_conn = DatabaseConnection()
    db_conn.rollback()


def commit_connection(conn: Optional[sqlite3.Connection] = None) -> None:
    """
    Valide la transaction (fonction utilitaire).
    
    Args:
        conn (Optional[sqlite3.Connection]): Connexion (ignoré, pour compatibilité).
    
    """
    db_conn = DatabaseConnection()
    db_conn.commit()