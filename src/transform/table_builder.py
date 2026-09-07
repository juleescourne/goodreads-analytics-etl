
# -*- coding: utf-8 -*-
"""
Module de création des tables dimensionnelles et de faits.

Ce module implémente un modèle en étoile (Star Schema) pour l'analyse
des données de livres, avec création de dimensions et d'une table de faits
incluant validation de l'intégrité référentielle.

Architecture:
    - Dimensions: Books, Authors, Publishers, Languages, Dates, Genres
    - Fait: FactBooks (métriques et clés étrangères)

Features:
    - Validation de l'intégrité référentielle
    - Attributs temporels enrichis (année, mois, trimestre)
    - Calcul de métriques dérivées (engagement)
    - Gestion multilingue des noms de langues
    - Logs détaillés de la création

Author:
    Jules Courné

Date:
    2025-12-30
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

from src.utils.config_loader import ConfigLoader


class TableBuilder:
    """
    Constructeur de tables dimensionnelles pour modèle en étoile.
    
    Cette classe crée toutes les tables nécessaires à un data warehouse
    en architecture Star Schema, incluant les dimensions et la table de faits,
    avec validation complète de l'intégrité référentielle.
    
    Attributes:
        config (ConfigLoader): Configuration du pipeline.
        logger (logging.Logger): Logger pour les opérations de transformation.
        
    Note:
        Les noms de colonnes sont définis comme constantes de classe pour
        faciliter la maintenance et éviter les erreurs de typage.
    
    """
    
    # Constantes de colonnes - Source
    BOOKID = 'bookID'
    TITLE = 'title'
    AUTHORS = 'authors'
    AVG_RATING = 'average_rating'
    ISBN = 'isbn13'
    LANGUE_CODE = 'language_code'
    NUM_PAGES = 'num_pages'
    RATING_COUNT = 'ratings_count'
    REVIEWS_COUNT = 'text_reviews_count'
    PUBLICATION_DATE = 'publication_date'
    PUBLISHER_NAME = 'publisher_name'
    GENRE_NAME = 'genre_name'
    
    # Constantes de colonnes - IDs dimensionnels
    PUBLISHERID = 'publisherID'
    LANGUEID = 'languageID'
    DATEID = 'dateID'
    AUTHORID = 'authorID'
    GENREID = 'genreID'
    
    # Constantes de colonnes - Attributs dérivés
    YEAR = 'year'
    MONTH = 'month'
    DAY = 'day'
    MONTH_NAME = 'month_name'
    DAY_NAME = 'day_name'
    QUARTER = 'quarter'
    ENGAGEMENT = 'engagement'
    AUTHOR_NAME = 'author_name'
    LANGUAGE_NAME = 'language_name'
    COUNTRY = 'country'
    
    # Mapping langues → noms complets et pays
    LANGUAGE_MAPPING = {
        "eng": ["English", "United States"],
        "en-US": ["English (United States)", "United States"],
        "spa": ["Spanish", "Spain"],
        "en-GB": ["English (United Kingdom)", "United Kingdom"],
        "fre": ["French", "France"],
        "ger": ["German", "Germany"],
        "zho": ["Chinese (Mandarin)", "China"],
        "jpn": ["Japanese", "Japan"],
        "rus": ["Russian", "Russia"],
        "mul": ["Multiple languages", "International"],
        "lat": ["Latin", "Vatican City"],
        "nor": ["Norwegian", "Norway"],
        "ita": ["Italian", "Italy"],
        "por": ["Portuguese", "Portugal"],
        "enm": ["Middle English", "United Kingdom"],
        "grc": ["Ancient Greek", "Greece"],
        "nl": ["Dutch", "Netherlands"],
        "en-CA": ["English (Canada)", "Canada"],
        "swe": ["Swedish", "Sweden"],
        "glg": ["Galician", "Spain (Galicia)"],
        "msa": ["Malay", "Malaysia"],
        "ara": ["Arabic", "Saudi Arabia"],
        "gla": ["Scottish Gaelic", "United Kingdom (Scotland)"],
        "ale": ["Aleut", "United States (Alaska)"],
        "tur": ["Turkish", "Türkiye"],
        "wel": ["Welsh", "United Kingdom (Wales)"],
        "srp": ["Serbian", "Serbia"]
    }
    
    def __init__(self, config: ConfigLoader) -> None:
        """
        Initialise le constructeur de tables.
        
        Args:
            config (ConfigLoader): Instance de ConfigLoader contenant
                les paramètres de configuration.
        """
        self.config = config
        self.logger = logging.getLogger('transform')
        self.logger.info("TableBuilder initialisé avec succès")
    
    def create_all_tables(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Crée toutes les tables du modèle en étoile.
        
        Construit les dimensions et la table de faits dans l'ordre approprié,
        avec validation de l'intégrité référentielle à chaque étape.
        
        Args:
            df (pd.DataFrame): DataFrame source nettoyé contenant toutes
                les colonnes nécessaires.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionnaire contenant toutes les tables :
                - 'dim_books': Dimension des livres
                - 'dim_authors': Dimension des auteurs
                - 'dim_publishers': Dimension des éditeurs
                - 'dim_languages': Dimension des langues
                - 'dim_dates': Dimension temporelle
                - 'dim_genres': Dimension des genres
                - 'fact_books': Table de faits
        
        Raises:
            ValueError: Si validation de l'intégrité référentielle échoue.
            Exception: Pour toute autre erreur lors de la création.

        """
        self.logger.info("=" * 60)
        self.logger.info("CRÉATION DES TABLES DIMENSIONNELLES")
        self.logger.info("=" * 60)
        
        try:
            # Vérification préalable
            self._check_missing_values(df)
            
            # Créer dimensions
            self.logger.info("Création des dimensions...")
            dimensions = {
                'dim_publishers': self._create_dim_publishers(df),
                'dim_languages': self._create_dim_languages(df),
                'dim_dates': self._create_dim_dates(df),
                'dim_genres': self._create_dim_genres(df),
                'dim_books': self._create_dim_books(df),
                'dim_authors': self._create_dim_authors(df)
            }
            
            # Créer table de faits
            self.logger.info("Création de la table de faits...")
            dimensions['fact_books'] = self._create_fact_books(df, dimensions)
            
            # Résumé
            self._log_tables_summary(dimensions)
            
            self.logger.info("=" * 60)
            self.logger.info("TOUTES LES TABLES CRÉÉES AVEC SUCCÈS")
            self.logger.info("=" * 60)
            
            return dimensions
            
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la création des tables : {e}", 
                exc_info=True
            )
            raise
    
    def _check_missing_values(self, df: pd.DataFrame) -> None:
        """
        Vérifie et log les valeurs manquantes dans le DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame à vérifier.
        
        Note:
            Affiche un warning pour les 5 premières lignes contenant des NaN.
        """
        
        
        if df.empty:
            self.logger.error("DataFrame vide")
            raise ValueError("DataFrame vide : aucune donnée à traiter")

            
        missing_rows = df[df.isna().any(axis=1) | df.isnull().any(axis=1)]
        
        if len(missing_rows) > 0:
            self.logger.warning(
                f"Attention : {len(missing_rows)} lignes avec valeurs manquantes"
            )
            
            for idx, row in missing_rows.head(5).iterrows():
                nan_cols = row[row.isna()].index.tolist()
                self.logger.warning(f"  Ligne {idx} : colonnes manquantes = {nan_cols}")
                
    
    def _create_dim_publishers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée la dimension Publishers.
        
        Args:
            df (pd.DataFrame): DataFrame source.
        
        Returns:
            pd.DataFrame: Dimension avec colonnes [publisherID, publisher_name].
        
        """
        self.logger.debug("  dim_publishers...")
        
        dim = df[[self.PUBLISHER_NAME]].drop_duplicates().reset_index(drop=True)
        dim[self.PUBLISHERID] = dim.index + 1
        
        self.logger.info(f"  dim_publishers : {len(dim)} éditeurs")
        return dim
    
    def _create_dim_languages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée la dimension Languages avec noms complets et pays.
        
        Enrichit les codes de langue (ex: 'eng') avec leur nom complet
        ('English') et le pays associé ('United States').
        
        Args:
            df (pd.DataFrame): DataFrame source.
        
        Returns:
            pd.DataFrame: Dimension avec colonnes [languageID, language_code,
                language_name, country].
        
        Note:
            Utilise le mapping LANGUAGE_MAPPING pour l'enrichissement.
            Les langues inconnues conservent leur code comme nom.
        
        """
        self.logger.debug("  dim_languages...")
        
        # Extraire et nettoyer codes
        dim = df[[self.LANGUE_CODE]].drop_duplicates().reset_index(drop=True)
        dim[self.LANGUE_CODE] = (
            dim[self.LANGUE_CODE]
            .astype("string")
            .str.strip()
            .fillna("unknown")
        )
        dim[self.LANGUEID] = dim.index + 1
        
        # Enrichir avec noms et pays
        dim[self.LANGUAGE_NAME] = dim[self.LANGUE_CODE].map(
            lambda x: self.LANGUAGE_MAPPING.get(x, ['Unknown', 'Unknown'])[0]
        )
        dim[self.COUNTRY] = dim[self.LANGUE_CODE].map(
            lambda x: self.LANGUAGE_MAPPING.get(x, ['Unknown', 'Unknown'])[1]
        )
        
        # Fallback pour langues inconnues
        dim[self.LANGUAGE_NAME] = dim[self.LANGUAGE_NAME].fillna(dim[self.LANGUE_CODE])
        dim[self.COUNTRY] = dim[self.COUNTRY].fillna(dim[self.LANGUE_CODE])
        
        self.logger.info(f"  dim_languages : {len(dim)} langues")
        return dim
    
    def _create_dim_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée la dimension Dates avec attributs temporels enrichis.
        
        Génère une dimension temporelle complète avec année, mois, jour,
        trimestre, et noms des mois/jours.
        
        Args:
            df (pd.DataFrame): DataFrame source.
        
        Returns:
            pd.DataFrame: Dimension avec colonnes [dateID, publication_date,
                year, month, day, quarter, month_name, day_name].
        
        Note:
            Tente d'utiliser la locale française pour les noms de mois/jours.
            Fallback en anglais si la locale n'est pas disponible.
        
        """
        self.logger.debug("  dim_dates...")
        
        dim = df[[self.PUBLICATION_DATE]].copy()
        
        # Conversion et nettoyage
        dim[self.PUBLICATION_DATE] = pd.to_datetime(
            dim[self.PUBLICATION_DATE],
            errors='coerce'
        )
        dim = dim.dropna(subset=[self.PUBLICATION_DATE])
        dim = dim.drop_duplicates().reset_index(drop=True)
        
        # ID technique
        dim[self.DATEID] = dim.index + 1
        
        # Attributs temporels
        dim[self.YEAR] = dim[self.PUBLICATION_DATE].dt.year.astype('Int64')
        dim[self.MONTH] = dim[self.PUBLICATION_DATE].dt.month.astype('Int64')
        dim[self.DAY] = dim[self.PUBLICATION_DATE].dt.day.astype('Int64')
        dim[self.QUARTER] = dim[self.PUBLICATION_DATE].dt.quarter.astype('Int64')
        
        # Noms localisés
        try:
            dim[self.MONTH_NAME] = dim[self.PUBLICATION_DATE].dt.month_name(locale='fr_FR')
            dim[self.DAY_NAME] = dim[self.PUBLICATION_DATE].dt.day_name(locale='fr_FR')
        except:
            # Fallback anglais
            dim[self.MONTH_NAME] = dim[self.PUBLICATION_DATE].dt.month_name()
            dim[self.DAY_NAME] = dim[self.PUBLICATION_DATE].dt.day_name()
            self.logger.warning(
                "  Locale française non disponible, utilisation de l'anglais"
            )
        
        self.logger.info(f"  dim_dates : {len(dim)} dates uniques")
        return dim
    
    def _create_dim_genres(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée la dimension Genres.
        
        Args:
            df (pd.DataFrame): DataFrame source.
        
        Returns:
            pd.DataFrame: Dimension avec colonnes [genreID, genre_name].
        """
        self.logger.debug("  dim_genres...")
        dim = df[[self.GENRE_NAME]].drop_duplicates().reset_index(drop=True)
        dim[self.GENREID] = dim.index + 1
        
        self.logger.info(f"  dim_genres : {len(dim)} genres")
        return dim
    
    def _create_dim_books(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée la dimension Books sans doublons.
        
        Args:
            df (pd.DataFrame): DataFrame source.
        
        Returns:
            pd.DataFrame: Dimension avec colonnes [bookID, isbn13, title].
        
        Note:
            En cas de doublon sur bookID, garde la première occurrence.
        
        """
        self.logger.debug("  dim_books...")
        
        dim = (
            df[[self.BOOKID, self.ISBN, self.TITLE]]
            .drop_duplicates(subset=[self.BOOKID], keep='first')
            .reset_index(drop=True)
        )
        
        dim[self.BOOKID] = dim[self.BOOKID].astype("int64")
        
        self.logger.info(f"  dim_books : {len(dim)} livres")
        return dim
    
    def _create_dim_authors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crée la dimension Authors en extrayant les auteurs multiples.
        
        Extrait tous les auteurs uniques depuis la colonne 'authors' où
        les auteurs multiples sont séparés par '/'.
        
        Args:
            df (pd.DataFrame): DataFrame source.
        
        Returns:
            pd.DataFrame: Dimension avec colonnes [authorID, author_name].
        
        Note:
            Les auteurs co-écrits (ex: "Author A / Author B") sont séparés
            et chaque auteur reçoit un ID unique.
        
        """
        self.logger.debug("  → dim_authors...")
        
        # Extraire et exploser auteurs
        authors_series = (
            df[self.AUTHORS]
            .dropna()
            .str.split('/')
            .explode()
            .str.strip()
            .drop_duplicates()
            .reset_index(drop=True)
        )
        
        dim = pd.DataFrame({self.AUTHOR_NAME: authors_series})
        dim[self.AUTHORID] = (dim.index + 1).astype("int64")
        
        # Réorganiser : clé primaire en premier
        dim = dim[[self.AUTHORID, self.AUTHOR_NAME]]
        
        self.logger.info(f"  dim_authors : {len(dim)} auteurs")
        return dim
    
    def _create_fact_books(
        self,
        df: pd.DataFrame,
        dimensions: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Crée la table de faits avec validation des clés étrangères.
        
        Joint le DataFrame source avec toutes les dimensions pour créer
        les clés étrangères, calcule les métriques dérivées, et valide
        l'intégrité référentielle.
        
        Args:
            df (pd.DataFrame): DataFrame source.
            dimensions (Dict[str, pd.DataFrame]): Dictionnaire des dimensions
                créées précédemment.
        
        Returns:
            pd.DataFrame: Table de faits avec colonnes [bookID, publisherID,
                languageID, dateID, genreID, average_rating, ratings_count,
                text_reviews_count, num_pages, engagement].
        
        Raises:
            ValueError: Si des clés étrangères référencent des IDs inexistants.
        
        Note:
            La métrique 'engagement' est calculée comme le ratio
            text_reviews_count / ratings_count.
        
        """
        self.logger.debug("  fact_books...")
        
        fact = df.copy()
        fact[self.PUBLICATION_DATE] = pd.to_datetime(
            fact[self.PUBLICATION_DATE], 
            errors='coerce'
        )
        
        # Jointures avec dimensions
        join_configs = [
            (dimensions['dim_publishers'], self.PUBLISHER_NAME, self.PUBLISHERID),
            (dimensions['dim_languages'], self.LANGUE_CODE, self.LANGUEID),
            (dimensions['dim_genres'], self.GENRE_NAME, self.GENREID)
        ]
        
        for dim_df, on_col, id_col in join_configs:
            fact = fact.merge(
                dim_df[[on_col, id_col]],
                on=on_col,
                how='left'
            )
            fact[id_col] = fact[id_col].astype('Int64')
        
        # Jointure dates avec normalisation
        fact['date_normalized'] = fact[self.PUBLICATION_DATE].dt.normalize()
        dim_dates = dimensions['dim_dates'].copy()
        dim_dates['date_normalized'] = pd.to_datetime(
            dim_dates[self.PUBLICATION_DATE]
        ).dt.normalize()
        
        fact = fact.merge(
            dim_dates[['date_normalized', self.DATEID]],
            on='date_normalized',
            how='left'
        )
        fact = fact.drop(columns=['date_normalized', self.PUBLICATION_DATE])
        fact[self.DATEID] = fact[self.DATEID].astype('Int64')
        
        fact[self.ENGAGEMENT] = fact[self.REVIEWS_COUNT] / fact[self.RATING_COUNT]
        fact[self.ENGAGEMENT] = fact[self.ENGAGEMENT].replace([np.inf, -np.inf], np.nan)
        fact[self.ENGAGEMENT] = fact[self.ENGAGEMENT].astype(float).fillna(0.0)
        
        # Sélectionner colonnes finales
        final_columns = [
            self.BOOKID, self.PUBLISHERID, self.LANGUEID, self.DATEID,
            self.GENREID, self.AVG_RATING, self.RATING_COUNT,
            self.REVIEWS_COUNT, self.NUM_PAGES, self.ENGAGEMENT
        ]
        fact = fact[final_columns].copy()
        
        # Validation intégrité référentielle
        self._validate_foreign_keys(fact, dimensions)
        
        self.logger.info(f"  fact_books : {len(fact)} faits")
        return fact
    
    def _validate_foreign_keys(
        self,
        fact: pd.DataFrame,
        dimensions: Dict[str, pd.DataFrame]
    ) -> None:
        """
        Valide l'intégrité référentielle de la table de faits.
        
        Vérifie que :
        1. Pas trop de valeurs NULL dans les FK
        2. Toutes les FK non-NULL existent dans leurs dimensions respectives
        
        Args:
            fact (pd.DataFrame): Table de faits à valider.
            dimensions (Dict[str, pd.DataFrame]): Dictionnaire des dimensions.
        
        Raises:
            ValueError: Si des FK invalides sont détectées.
        
        Note:
            Les warnings sont émis pour les FK NULL mais ne bloquent pas.
        """
        # Vérifier NULL dans FK
        fk_columns = {
            'publisherID': self.PUBLISHERID,
            'languageID': self.LANGUEID,
            'dateID': self.DATEID,
            'genreID': self.GENREID
        }
        
        for name, col in fk_columns.items():
            null_count = fact[col].isna().sum()
            if null_count > 0:
                self.logger.warning(f"  {null_count} valeurs NULL dans {name}")
        
        # Vérifier existence des IDs dans dimensions
        fk_validations = [
            (self.BOOKID, dimensions['dim_books']),
            (self.PUBLISHERID, dimensions['dim_publishers']),
            (self.LANGUEID, dimensions['dim_languages']),
            (self.DATEID, dimensions['dim_dates']),
            (self.GENREID, dimensions['dim_genres'])
        ]
        
        for id_col, dim_df in fk_validations:
            fact_ids = set(fact[fact[id_col].notna()][id_col].unique())
            dim_ids = set(dim_df[id_col].unique())
            invalid = fact_ids - dim_ids
            
            if invalid:
                self.logger.error(f"  {id_col}: {len(invalid)} IDs invalides!")
                raise ValueError(
                    f"Des {id_col} dans fact_books n'existent pas dans la dimension!"
                )
    
    def _log_tables_summary(self, tables: Dict[str, pd.DataFrame]) -> None:
        """
        Affiche un résumé de toutes les tables créées.
        
        Args:
            tables (Dict[str, pd.DataFrame]): Dictionnaire des tables créées.
        
        Note:
            Affiche également des statistiques de qualité (NULL dans fact_books).
        """
        self.logger.info("")
        self.logger.info("─" * 60)
        self.logger.info("RÉSUMÉ DES TABLES CRÉÉES")
        self.logger.info("─" * 60)
        
        for name, df in tables.items():
            self.logger.info(
                f"  {name:25s} : {len(df):>6} lignes, {len(df.columns):>2} colonnes"
            )
        
        self.logger.info("─" * 60)
        
        # Statistiques globales
        total_rows = sum(len(df) for df in tables.values())
        self.logger.info(f"Total lignes : {total_rows}")
        
        # Qualité des données
        fact_books = tables.get('fact_books')
        if fact_books is not None:
            null_count = fact_books.isnull().sum().sum()
            if null_count > 0:
                self.logger.warning(f"{null_count} valeurs NULL dans fact_books")
            else:
                self.logger.info("Aucune valeur NULL dans fact_books")