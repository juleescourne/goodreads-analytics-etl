# -*- coding: utf-8 -*-
"""
Module de transformation des données de livres.

Ce module fournit un pipeline complet de nettoyage et transformation
des données brutes de livres, incluant la validation, le nettoyage,
la gestion des valeurs manquantes et des outliers.

Features:
    - Validation des colonnes requises
    - Suppression des lignes corrompues
    - Conversion automatique des types
    - Gestion intelligente des valeurs manquantes
    - Détection et correction des outliers
    - Élimination des doublons
    - Statistiques détaillées de transformation

Author:
    Jules Courné

Date:
    2025-12-31
"""

import logging
from typing import Dict, Optional

import pandas as pd

from src.utils.config_loader import ConfigLoader


class BooksTransformer:
    """
    Transformateur spécialisé pour les données de livres.
    
    Cette classe implémente un pipeline complet de transformation et nettoyage
    des données brutes de livres, avec validation des colonnes, gestion des
    valeurs manquantes, correction des outliers et élimination des doublons.
    
    Attributes:
        config (ConfigLoader): Configuration du pipeline.
        logger (logging.Logger): Logger pour les opérations de transformation.
        genres (list): Liste des genres valides depuis la configuration.
        default_values (Dict): Valeurs par défaut pour remplacer les manquants.
        BOOKID (str): Nom de la colonne ID du livre.
        TITLE (str): Nom de la colonne titre.
        AUTHORS (str): Nom de la colonne auteurs.
        AVG_RATING (str): Nom de la colonne note moyenne.
        ISBN (str): Nom de la colonne ISBN13.
        LANGUE_CODE (str): Nom de la colonne code langue.
        NUM_PAGES (str): Nom de la colonne nombre de pages.
        RATING_COUNT (str): Nom de la colonne nombre de notes.
        REVIEWS_COUNT (str): Nom de la colonne nombre de critiques.
        PUBLICATION_DATE (str): Nom de la colonne date de publication.
        PUBLISHER_NAME (str): Nom de la colonne éditeur.
        GENRE_NAME (str): Nom de la colonne genre.
    
    Note:
        Les transformations sont appliquées dans un ordre spécifique pour
        garantir la cohérence des données. Chaque étape est loggée.
    
    """
    
    # Constantes de colonnes
    _COLUMN_NAMES = {
        'BOOKID': 'bookID',
        'TITLE': 'title',
        'AUTHORS': 'authors',
        'AVG_RATING': 'average_rating',
        'ISBN': 'isbn13',
        'LANGUE_CODE': 'language_code',
        'NUM_PAGES': 'num_pages',
        'RATING_COUNT': 'ratings_count',
        'REVIEWS_COUNT': 'text_reviews_count',
        'PUBLICATION_DATE': 'publication_date',
        'PUBLISHER_NAME': 'publisher_name',
        'GENRE_NAME': 'genre_name'
    }
    
    def __init__(self, config: ConfigLoader) -> None:
        """
        Initialise le transformateur de livres.
        
        Args:
            config (ConfigLoader): Instance de ConfigLoader contenant
                les paramètres de transformation et les valeurs par défaut.
        """
        self.config = config
        self.logger = logging.getLogger('transform')
        
        # Charger les configurations
        self.genres = self.config.get('books.genres', [])
        self.default_values = self.config.get('transformations.default_values', {})
        
        # Assigner les noms de colonnes
        for attr_name, col_name in self._COLUMN_NAMES.items():
            setattr(self, attr_name, col_name)
        
        self.logger.info("BooksTransformer initialisé avec succès")
    
    def transform_books(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Pipeline complet de transformation pour les livres.
        
        Applique toutes les étapes de transformation dans l'ordre suivant :
        1. Validation des colonnes
        2. Suppression des lignes corrompues
        3. Conversion des types
        4. Gestion des valeurs manquantes
        5. Nettoyage des chaînes
        6. Gestion des outliers
        7. Suppression des doublons
        
        Args:
            df (pd.DataFrame): DataFrame brut à transformer.
            
        Returns:
            Optional[pd.DataFrame]: DataFrame transformé, ou None en cas d'erreur.
        
        Note:
            Chaque étape log ses opérations. Les statistiques finales sont
            affichées à la fin de la transformation.
        
        """
        self.logger.info(f"Début transformation des livres - {len(df)} lignes")
        
        try:
            initial_count = len(df)
            
            # Pipeline de transformation
            transformations = [
                (self._validate_columns, "Validation des colonnes"),
                (self._remove_corrupted_rows, "Suppression des corrompues"),
                (self._convert_types, "Conversion des types"),
                (self._handle_missing_values, "Gestion des manquants"),
                (self._clean_strings, "Nettoyage des chaînes"),
                (self._handle_outliers, "Gestion des outliers"),
                (self._remove_duplicates, "Suppression des doublons")
            ]
            
            # Validation initiale
            if not self._validate_columns(df):
                return None
            
            # Appliquer les transformations
            for transform_func, desc in transformations[1:]:
                df = transform_func(df)
                if df is None or len(df) == 0:
                    self.logger.error(f"Transformation échouée à l'étape : {desc}")
                    return None
            
            # Statistiques finales
            final_count = len(df)
            removed = initial_count - final_count
            percentage = (removed / initial_count * 100) if initial_count > 0 else 0
            
            self.logger.info(
                f"Transformation terminée : {final_count} lignes "
                f"({removed} supprimées, {percentage:.1f}%)"
            )
            
            self._log_final_stats(df)
            
            return df
            
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la transformation : {e}", 
                exc_info=True
            )
            return None
    
    def _validate_columns(self, df: pd.DataFrame) -> bool:
        """
        Valide la présence des colonnes obligatoires.
        
        Nettoie d'abord les noms de colonnes (espaces, caractères spéciaux),
        puis vérifie que toutes les colonnes requises sont présentes.
        
        Args:
            df (pd.DataFrame): DataFrame à valider.
            
        Returns:
            bool: True si toutes les colonnes sont présentes, False sinon.
        
        Note:
            Cette méthode modifie les noms de colonnes du DataFrame en place.
        
        """
        self.logger.debug("Vérification des colonnes...")
        
        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(';', '', regex=False)
        df.columns = df.columns.str.replace('"', '', regex=False)
        
        # Liste des colonnes requises
        required_cols = list(self._COLUMN_NAMES.values())
        
        # Vérifier les colonnes manquantes
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            self.logger.error(f"Colonnes manquantes : {missing}")
            self.logger.error(f"Colonnes disponibles : {list(df.columns)}")
            return False
        
        self.logger.info("  Toutes les colonnes obligatoires présentes")
        return True
    
    def _remove_corrupted_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les lignes avec bookID ou ISBN non numériques.
        
        Args:
            df (pd.DataFrame): DataFrame à nettoyer.
            
        Returns:
            pd.DataFrame: DataFrame sans lignes corrompues.
        
        Note:
            Les colonnes bookID et isbn13 doivent contenir uniquement des chiffres.
        

        """
        self.logger.debug("Suppression des lignes corrompues...")
        
        initial_count = len(df)
        
        try:
            if self.BOOKID in df.columns:
                df = df.copy()
                df[self.BOOKID] = df[self.BOOKID].astype('string')
                df = df[df[self.BOOKID].str.isnumeric().fillna(False)].copy()
            
            # Filtrer ISBN
            if self.ISBN in df.columns:
                df[self.ISBN] = df[self.ISBN].astype('string')
                df = df[df[self.ISBN].str.isnumeric().fillna(False)].copy()
            
            df[self.GENRE_NAME] = (
                df[self.GENRE_NAME]
                .astype('string')
                .str.replace(';', '', regex=False)
            )

                
            removed = initial_count - len(df)
            if removed > 0:
                self.logger.info(f"  {removed} lignes corrompues supprimées")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du filtrage des lignes corrompues : {e}")
        
        return df
    
    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convertit les colonnes aux types de données appropriés.
        
        Conversions appliquées :
        - bookID : Int64
        - average_rating : Float64
        - ratings_count : Int64
        - text_reviews_count : Int64
        - num_pages : Int64
        - publication_date : datetime
        
        Args:
            df (pd.DataFrame): DataFrame à convertir.
            
        Returns:
            pd.DataFrame: DataFrame avec types convertis.
        
        Note:
            Les erreurs de conversion sont gérées avec 'coerce' (→ NaN).
        
        """
        self.logger.debug("Conversion des types...")
        
        try:
            # Conversions numériques
            numeric_conversions = {
                self.BOOKID: 'Int64',
                self.AVG_RATING: 'Float64',
                self.RATING_COUNT: 'Int64',
                self.REVIEWS_COUNT: 'Int64',
                self.NUM_PAGES: 'Int64'
            }
            
            for col, dtype in numeric_conversions.items():
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
            
            # Conversion datetime
            if self.PUBLICATION_DATE in df.columns:
                df[self.PUBLICATION_DATE] = pd.to_datetime(
                    df[self.PUBLICATION_DATE], 
                    format='%Y-%m-%d', 
                    errors='coerce'
                )
            
            self.logger.info("  → Types convertis avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion des types : {e}")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gère les valeurs manquantes selon des stratégies prédéfinies.
        
        Stratégies par colonne :
        - bookID, isbn13 : Supprimer la ligne
        - average_rating : Remplacer par la moyenne
        - ratings_count, text_reviews_count, num_pages : Remplacer par la médiane
        - publication_date : Remplacer par '2000-01-01'
        - language_code : Remplacer par 'eng'
        - publisher_name, authors : Remplacer par 'Unknown'
        - genre_name : Valider et remplacer par 'Other' si invalide
        
        Args:
            df (pd.DataFrame): DataFrame à traiter.
            
        Returns:
            pd.DataFrame: DataFrame avec valeurs manquantes gérées.
        
        """
        self.logger.debug("Gestion des valeurs manquantes...")
        
        try:
            # Supprimer lignes avec bookID/ISBN manquant
            if self.BOOKID in df.columns and self.ISBN in df.columns:
                initial_len = len(df)
                df = df.dropna(subset=[self.BOOKID, self.ISBN], how='any').copy()
                removed = initial_len - len(df)
                if removed > 0:
                    self.logger.info(
                        f"  {removed} lignes avec BOOKID/ISBN manquant supprimées"
                    )
            
            # Stratégies de remplacement
            strategies = [
                (self.AVG_RATING, 'mean', 'moyenne'),
                (self.RATING_COUNT, 'median', 'médiane'),
                (self.NUM_PAGES, 'median', 'médiane'),
                (self.REVIEWS_COUNT, 'median', 'médiane'),
            ]
            
            for col, strategy, label in strategies:
                if col in df.columns and df[col].isna().any():
                    na_count = df[col].isna().sum()
                    if strategy == 'mean':
                        fill_value = df[col].mean()
                    else:  # median
                        fill_value = int(df[col].median())
                    
                    df[col] = df[col].fillna(fill_value)
                    self.logger.info(
                        f"  → {col}: {na_count} NA remplacés par {label} ({fill_value})"
                    )
            
            # Valeurs par défaut depuis config
            default_mappings = {
                self.PUBLICATION_DATE: 'publication_date',
                self.LANGUE_CODE: 'language_code',
                self.PUBLISHER_NAME: 'publisher',
                self.AUTHORS: 'author'
            }
            
            for col, config_key in default_mappings.items():
                if col in df.columns and df[col].isna().any():
                    default_val = self.default_values.get(
                        config_key, 
                        'Unknown' if config_key in ['publisher', 'author'] else '2000-01-01'
                    )
                    na_count = df[col].isna().sum()
                    df[col] = df[col].fillna(default_val)
                    self.logger.info(
                        f"  → {col}: {na_count} NA remplacés par '{default_val}'"
                    )
            
            # Genre : validation spéciale
            if self.GENRE_NAME in df.columns:
                if self.genres:
                    df[self.GENRE_NAME] = df[self.GENRE_NAME].apply(
                        lambda x: x if x in self.genres else "Other"
                    )
                df[self.GENRE_NAME] = df[self.GENRE_NAME].fillna('Other')
                self.logger.info(
                    f"  {self.GENRE_NAME}: valeurs invalides/NA remplacées par 'Other'"
                )
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la gestion des valeurs manquantes : {e}")
        
        return df
    
    def _clean_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les chaînes et sélectionne les colonnes utiles.
        
        Args:
            df (pd.DataFrame): DataFrame à nettoyer.
            
        Returns:
            pd.DataFrame: DataFrame avec chaînes nettoyées et colonnes filtrées.
        
        Note:
            Supprime les espaces en début/fin de toutes les colonnes textuelles.
        """
        self.logger.debug("Nettoyage des chaînes...")
        
        try:
            # Nettoyer les strings
            for col in df.select_dtypes(include="object").columns:
                df[col] = df[col].str.strip()
            
            # Sélectionner colonnes utiles
            features = list(self._COLUMN_NAMES.values())
            df = df[features]
            
            self.logger.info("  Chaînes nettoyées et colonnes sélectionnées")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage : {e}")
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Détecte et corrige les valeurs aberrantes.
        
        Règles appliquées :
        - average_rating : Limiter entre 0 et 5
        - ratings_count, text_reviews_count : Pas de valeurs négatives
        - num_pages : Remplacer <= 0 par la médiane
        - publication_date : Supprimer dates futures
        
        Args:
            df (pd.DataFrame): DataFrame à corriger.
            
        Returns:
            pd.DataFrame: DataFrame avec outliers corrigés.
        
        """
        self.logger.debug("Gestion des outliers...")
        
        try:
            current_date = pd.Timestamp.now()
            
            # Règles de clipping
            clip_rules = [
                (self.AVG_RATING, 0, 5, "[0-5]"),
                (self.RATING_COUNT, 0, None, "≥0"),
                (self.REVIEWS_COUNT, 0, None, "≥0")
            ]
            
            for col, lower, upper, desc in clip_rules:
                if col in df.columns:
                    outliers_count = len(
                        df[(df[col] < (lower if lower else float('-inf'))) | 
                           (df[col] > (upper if upper else float('inf')))]
                    )
                    df[col] = df[col].clip(lower=lower, upper=upper)
                    if outliers_count > 0:
                        self.logger.info(
                            f"  {col}: {outliers_count} valeurs corrigées {desc}"
                        )
            
            # NUM_PAGES : médiane pour <= 0
            if self.NUM_PAGES in df.columns:
                outliers_count = len(df[df[self.NUM_PAGES] <= 0])
                if outliers_count > 0:
                    median_pages = df[df[self.NUM_PAGES] > 0][self.NUM_PAGES].median()
                    df.loc[df[self.NUM_PAGES] <= 0, self.NUM_PAGES] = median_pages
                    self.logger.info(
                        f"  {self.NUM_PAGES}: {outliers_count} valeurs "
                        f"<= 0 remplacées par médiane"
                    )
            
            # Dates futures
            if self.PUBLICATION_DATE in df.columns:
                initial_len = len(df)
                df = df[df[self.PUBLICATION_DATE] <= current_date]
                removed = initial_len - len(df)
                if removed > 0:
                    self.logger.info(
                        f"  {self.PUBLICATION_DATE}: {removed} dates futures supprimées"
                    )
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la gestion des outliers : {e}")
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les doublons basés sur bookID et ISBN.
        
        Args:
            df (pd.DataFrame): DataFrame à dédupliquer.
            
        Returns:
            pd.DataFrame: DataFrame sans doublons.
        
        Note:
            En cas de doublon, garde la première occurrence.
        """
        self.logger.debug("Suppression des doublons...")
        
        try:
            duplicates_count = df.duplicated(
                subset=[self.BOOKID, self.ISBN], 
                keep=False
            ).sum() // 2
            
            if duplicates_count > 0:
                df = df.drop_duplicates(
                    subset=[self.BOOKID, self.ISBN], 
                    keep='first'
                )
                self.logger.info(f"  {duplicates_count} paires de doublons supprimées")
            else:
                self.logger.info("  Aucun doublon trouvé")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression des doublons : {e}")
        
        return df
    
    def _log_final_stats(self, df: pd.DataFrame) -> None:
        """
        Affiche les statistiques finales après transformation.
        
        Args:
            df (pd.DataFrame): DataFrame transformé.
        
        Note:
            Affiche le nombre de lignes, colonnes, et les valeurs manquantes.
        """
        self.logger.info("─" * 60)
        self.logger.info("STATISTIQUES FINALES")
        self.logger.info("─" * 60)
        self.logger.info(f"Lignes : {len(df)}")
        self.logger.info(f"Colonnes : {len(df.columns)}")
        
        # Valeurs manquantes ou vides
        empty_counts = df.isna().sum() + (df == '').sum()
        if empty_counts.sum() > 0:
            self.logger.warning("Valeurs manquantes/vides :")
            for col, count in empty_counts[empty_counts > 0].items():
                self.logger.warning(f"  - {col}: {count}")
        else:
            self.logger.info("  Aucune valeur manquante")
        
        self.logger.info("─" * 60)