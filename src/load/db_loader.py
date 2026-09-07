# -*- coding: utf-8 -*-
# src/load/db_loader.py
"""
Module de chargement des données dans SQLite avec logique incrémentale.

Ce module gère l'insertion et la mise à jour intelligente des données dans
la base SQLite avec détection des changements et recalcul conditionnel de la PCA.

Features:
    - UPSERT pour DimBooks basé sur ISBN13
    - Insertion incrémentale pour les autres dimensions
    - Gestion automatique des colonnes auto-incrémentées
    - Synchronisation de BridgeAuthorBook
    - Recalcul PCA uniquement si modifications détectées
    - Vérification d'intégrité référentielle
    - Encodage UTF-8 forcé pour SQLite

Author:
    Jules Courné

Date:
    2025-12-31
"""

import logging
from datetime import datetime
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd

from src.load.database_connection import DatabaseConnection
from src.utils.config_loader import ConfigLoader
from src.utils.pca_calculator import PCACalculator


class DatabaseLoader:
    """
    Chargeur intelligent de données vers SQLite.
    
    Cette classe gère le chargement incrémental des données avec logique
    UPSERT pour les livres et insertion conditionnelle pour les dimensions.
    Elle détecte automatiquement les changements et déclenche le recalcul
    de la PCA uniquement si nécessaire.
    
    Attributes:
        config (ConfigLoader): Configuration du pipeline.
        logger (logging.Logger): Logger pour les opérations de chargement.
        db_conn (DatabaseConnection): Gestionnaire de connexion à la base.
        batch_size (int): Taille des batchs pour les insertions en masse.
        changes_detected (bool): Flag indiquant si des modifications ont été faites.
        auto_id_columns (Dict[str, str]): Mapping des colonnes auto-incrémentées.
    
    Note:
        Le recalcul de la PCA est coûteux et n'est effectué que si des
        modifications ont été détectées dans les données.
    
    """
    
    def __init__(self, config: ConfigLoader) -> None:
        """
        Initialise le chargeur de données.
        
        Args:
            config (ConfigLoader): Instance de ConfigLoader contenant
                les paramètres du pipeline.
        """
        self.config = config
        self.logger = logging.getLogger('load')
        self.db_conn = DatabaseConnection(config)
        self.batch_size = config.get('pipeline.batch_size', 1000)
        self.changes_detected = False
        
        # Colonnes ID auto-incrémentées par table
        # None = l'ID vient des données source
        self.auto_id_columns = {
            'DimBooks': None,
            'DimAuthors': 'authorID',
            'DimPublishers': 'publisherID',
            'DimLanguages': 'languageID',
            'DimDates': 'dateID',
            'DimGenres': 'genreID',
            'FactBooks': None
        }
        
        self.logger.info("DatabaseLoader initialisé")

    def load_all_tables(
        self, 
        tables: Dict[str, pd.DataFrame], 
        source_df: pd.DataFrame
    ) -> bool:
        """
        Charge toutes les tables avec logique UPSERT et recalcul PCA conditionnel.
        
        Traite les tables dans l'ordre approprié pour respecter les contraintes
        de clés étrangères. Détecte les modifications et recalcule la PCA
        uniquement si nécessaire.
        
        Args:
            tables (Dict[str, pd.DataFrame]): Dictionnaire contenant les tables
                dimensionnelles et de faits à charger. Clés attendues:
                'dim_books', 'dim_authors', 'dim_publishers', 'dim_languages',
                'dim_dates', 'dim_genres', 'fact_books'.
            source_df (pd.DataFrame): DataFrame source contenant les données
                brutes avec la colonne 'authors' pour créer BridgeAuthorBook.
        
        Returns:
            bool: True si toutes les opérations ont réussi, False sinon.
        
        Raises:
            Exception: En cas d'erreur lors du chargement (rollback automatique).
        
        """
        # Ordre d'insertion respectant les dépendances FK
        insert_order = [
            ('DimBooks', 'dim_books'),
            ('DimAuthors', 'dim_authors'),
            ('DimPublishers', 'dim_publishers'),
            ('DimLanguages', 'dim_languages'),
            ('DimDates', 'dim_dates'),
            ('DimGenres', 'dim_genres'),
            ('FactBooks', 'fact_books'),
        ]
        
        try:
            # Initialiser la base et les tables
            conn = self.db_conn.create_database()
            
            # IMPORTANT: Forcer l'encodage UTF-8 pour SQLite
            conn.execute("PRAGMA encoding = 'UTF-8'")
            self.logger.info("  Encodage UTF-8 activé pour SQLite")
            
            self.db_conn._create_tables()
            
            self.changes_detected = False
            
            # 1. Charger dimensions et faits avec UPSERT
            for table_db, table_name in insert_order:
                self.logger.info(f"Traitement de '{table_db}'...")
                changed = self._upsert_table(table_db, tables[table_name])
                if changed:
                    self.changes_detected = True
            
            # 2. Synchroniser BridgeAuthorBook
            self.logger.info("\nTraitement de BridgeAuthorBook...")
            bridge_changed = self._upsert_bridge_from_source(source_df)
            if bridge_changed:
                self.changes_detected = True
            
            # IMPORTANT: Commit avant PCA pour que les données soient visibles
            if self.changes_detected:
                self.db_conn.commit()
                self.logger.info("  Données committées avant calcul PCA")
            
            # 3. Recalculer PCA si nécessaire
            if self.changes_detected:
                self.logger.info(
                    "\n⚠ Modifications détectées → Recalcul PCA nécessaire"
                )
                calculator = PCACalculator(self.db_conn._connection)
                success = calculator.calculate_and_load_all()
                
                if success:
                    self.logger.info("  PCA recalculée et tables mises à jour")
                else:
                    self.logger.warning("   Erreur lors du recalcul PCA")
            else:
                self.logger.info("\n    Aucune modification → PCA conservée")
            
            # Vérifier l'intégrité
            self._check_data_integrity()
            
            self.db_conn.commit()
            self.logger.info("  Toutes les tables traitées avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement : {e}", exc_info=True)
            self.db_conn.rollback()
            return False
    
    def _upsert_table(self, table_name: str, df: pd.DataFrame) -> bool:
        """
        Route vers la bonne stratégie UPSERT selon la table.
        
        Args:
            table_name (str): Nom de la table de destination.
            df (pd.DataFrame): DataFrame à charger.
            
        Returns:
            bool: True si des modifications ont été apportées.
        
        Note:
            DimBooks utilise une stratégie UPSERT basée sur ISBN13,
            les autres tables utilisent une insertion incrémentale.
        """
        if table_name == 'DimBooks':
            return self._upsert_dim_books(df)
        else:
            return self._insert_new_records(table_name, df)
    
    def _upsert_dim_books(self, df: pd.DataFrame) -> bool:
        """
        UPSERT pour DimBooks basé sur ISBN13.
        
        Compare les livres existants par ISBN13 et :
        - Insère les nouveaux livres
        - Met à jour les livres modifiés (si titre différent)
        - Ignore les livres inchangés
        
        Args:
            df (pd.DataFrame): DataFrame contenant les livres à charger.
                Doit contenir au minimum: bookID, isbn13, title.
        
        Returns:
            bool: True si des insertions ou mises à jour ont été effectuées.
        
        Note:
            Le bookID vient des données source et n'est pas auto-généré.
        
        """
        self.logger.info(f"UPSERT DimBooks ({len(df)} livres)...")
        
        cursor = self.db_conn._connection.cursor()
        
        # Récupérer les livres existants
        cursor.execute("SELECT isbn13, title FROM DimBooks")
        existing_books = {row[0]: row[1] for row in cursor.fetchall()}
        
        self.logger.info(f"  Livres en BDD : {len(existing_books)}")
        
        # Classifier les livres
        to_insert = []
        to_update = []
        unchanged = 0
        
        for _, row in df.iterrows():
            isbn13 = row['isbn13']
            current_title = row['title']
            
            if isbn13 in existing_books:
                if existing_books[isbn13] != current_title:
                    to_update.append(tuple(row))
                else:
                    unchanged += 1
            else:
                to_insert.append(tuple(row))
        
        changes_made = False
        
        # Insérer nouveaux livres
        if to_insert:
            self.logger.info(f"  Insertion de {len(to_insert)} nouveaux livres")
            columns = ', '.join(df.columns)
            placeholders = ', '.join(['?' for _ in df.columns])
            query = f"INSERT INTO DimBooks ({columns}) VALUES ({placeholders})"
            cursor.executemany(query, to_insert)
            changes_made = True
        
        # Mettre à jour livres modifiés
        if to_update:
            self.logger.info(f"  Mise à jour de {len(to_update)} livres")
            update_cols = [col for col in df.columns if col not in ['bookID', 'isbn13']]
            set_clause = ', '.join([f"{col} = ?" for col in update_cols])
            query = f"UPDATE DimBooks SET {set_clause} WHERE isbn13 = ?"
            
            update_data = [
                tuple([dict(zip(df.columns, row))[col] for col in update_cols] + 
                      [dict(zip(df.columns, row))['isbn13']])
                for row in to_update
            ]
            
            cursor.executemany(query, update_data)
            changes_made = True
        
        self.logger.info(
            f"  Nouveaux: {len(to_insert)}, "
            f"Modifiés: {len(to_update)}, "
            f"Inchangés: {unchanged}"
        )
        
        return changes_made
    
    def _insert_new_records(self, table_name: str, df: pd.DataFrame) -> bool:
        """
        Insertion incrémentale basée sur les colonnes UNIQUE.
        
        Insère uniquement les nouvelles lignes qui n'existent pas déjà.
        Les colonnes ID auto-incrémentées sont automatiquement exclues.
        
        Args:
            table_name (str): Nom de la table de destination.
            df (pd.DataFrame): DataFrame contenant les enregistrements.
        
        Returns:
            bool: True si des lignes ont été insérées.
        
        Note:
            Les colonnes uniques par table :
            - DimAuthors: author_name
            - DimPublishers: publisher_name
            - DimLanguages: language_code
            - DimDates: publication_date
            - DimGenres: genre_name
            - FactBooks: bookID
        
        """
        cursor = self.db_conn._connection.cursor()
        
        # Mapping des colonnes uniques
        unique_col_map = {
            'DimAuthors': 'author_name',
            'DimPublishers': 'publisher_name',
            'DimLanguages': 'language_code',
            'DimDates': 'publication_date',
            'DimGenres': 'genre_name',
            'FactBooks': 'bookID'
        }
        
        unique_col = unique_col_map.get(table_name)
        if not unique_col:
            self.logger.warning(f"Colonne unique inconnue pour {table_name}")
            return False
        
        # Récupérer valeurs existantes
        cursor.execute(f"SELECT {unique_col} FROM {table_name}")
        existing_values = {row[0] for row in cursor.fetchall()}
        
        # Filtrer nouvelles lignes
        new_rows = df[~df[unique_col].isin(existing_values)].copy()
        
        if len(new_rows) == 0:
            self.logger.info(f"  {table_name}: Aucune nouvelle ligne")
            return False
        
        # Exclure colonne auto-incrémentée
        auto_id_col = self.auto_id_columns.get(table_name)
        if auto_id_col and auto_id_col in new_rows.columns:
            self.logger.debug(
                f"  Exclusion de la colonne auto-incrémentée '{auto_id_col}'"
            )
            new_rows = new_rows.drop(columns=[auto_id_col])
        
        # Insérer
        self.logger.info(
            f"  Insertion de {len(new_rows)} nouvelles lignes dans {table_name}"
        )
        data = self._prepare_data(new_rows)
        columns = ', '.join(new_rows.columns)
        placeholders = ', '.join(['?' for _ in new_rows.columns])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        cursor.executemany(query, data)
        
        self.logger.info(f"  {table_name}: {len(new_rows)} lignes insérées")
        return True
    
    def _upsert_bridge_from_source(self, df: pd.DataFrame) -> bool:
        """
        Synchronisation intelligente de la table BridgeAuthorBook.
        
        Crée les relations livre-auteur en se basant sur les données source.
        Ajoute uniquement les nouvelles relations manquantes.
        
        Args:
            df (pd.DataFrame): DataFrame source contenant les colonnes
                'bookID' et 'authors' (auteurs séparés par '/').
        
        Returns:
            bool: True si de nouvelles relations ont été ajoutées.
        
        Note:
            Les auteurs multiples sont séparés par '/' dans la colonne 'authors'.
            Exemple: "J.K. Rowling / Mary GrandPré"
        
        """
        self.logger.info("Synchronisation de BridgeAuthorBook...")
        
        cursor = self.db_conn._connection.cursor()
        
        # Charger données existantes
        cursor.execute("SELECT bookID FROM DimBooks")
        existing_books = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT authorID, author_name FROM DimAuthors")
        author_mapping = {row[1]: row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT bookID, authorID FROM BridgeAuthorBook")
        existing_relations = {(row[0], row[1]) for row in cursor.fetchall()}
        
        # Construire nouvelles relations
        new_relations = set()
        
        for _, row in df.iterrows():
            book_id = row['bookID']
            authors_str = row['authors']
            
            if book_id not in existing_books or pd.isna(authors_str):
                continue
            
            authors = [a.strip() for a in str(authors_str).split('/')]
            
            for author_name in authors:
                if author_name in author_mapping:
                    author_id = author_mapping[author_name]
                    new_relations.add((book_id, author_id))
        
        # Calculer différences
        to_insert = new_relations - existing_relations
        
        if to_insert:
            self.logger.info(f"  Ajout de {len(to_insert)} nouvelles relations")
            cursor.executemany(
                "INSERT INTO BridgeAuthorBook (bookID, authorID) VALUES (?, ?)",
                list(to_insert)
            )
            return True
        else:
            self.logger.info("  BridgeAuthorBook à jour")
            return False
    
    def _prepare_data(self, df: pd.DataFrame) -> List[Tuple]:
        """Normalize DataFrame values for safe SQLite insertion.

        Missing values become ``None``, pandas/numpy scalar values are converted
        to their native Python equivalents, and datetimes are serialized using
        an ISO-like ``YYYY-MM-DD HH:MM:SS`` representation. Numeric values are
        deliberately kept numeric even when a pandas column has ``object``
        dtype because it also contains missing values.
        """

        def normalize(value):
            if pd.isna(value):
                return None
            if isinstance(value, (pd.Timestamp, datetime)):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(value, np.generic):
                return value.item()
            return value

        return [
            tuple(normalize(value) for value in row)
            for row in df.itertuples(index=False, name=None)
        ]

    def _check_data_integrity(self) -> None:
        """
        Vérifie l'intégrité référentielle des données.
        
        Effectue plusieurs vérifications :
        - Livres sans auteur dans BridgeAuthorBook
        - Faits avec clés étrangères invalides
        - Relations bridge avec bookID invalide
        
        Les violations sont loggées en warning mais n'interrompent pas
        le traitement.
        
        """
        self.logger.info("Vérification de l'intégrité des données...")
        
        integrity_checks = [
            {
                'name': 'Livres sans auteur',
                'query': """
                    SELECT COUNT(*) 
                    FROM DimBooks 
                    WHERE bookID NOT IN (
                        SELECT DISTINCT bookID FROM BridgeAuthorBook
                    )
                """
            },
            {
                'name': 'Faits avec FK invalides',
                'query': """
                    SELECT COUNT(*) 
                    FROM FactBooks
                    WHERE bookID NOT IN (SELECT bookID FROM DimBooks)
                """
            },
            {
                'name': 'Bridge avec bookID invalide',
                'query': """
                    SELECT COUNT(*) 
                    FROM BridgeAuthorBook
                    WHERE bookID NOT IN (SELECT bookID FROM DimBooks)
                """
            }
        ]
        
        all_ok = True
        
        for check in integrity_checks:
            cursor = self.db_conn.execute_query(check['query'])
            count = cursor.fetchone()[0]
            
            if count > 0:
                self.logger.warning(f"  {check['name']} : {count}")
                all_ok = False
            else:
                self.logger.info(f"  {check['name']} : OK")
        
        if all_ok:
            self.logger.info("Intégrité des données vérifiée")