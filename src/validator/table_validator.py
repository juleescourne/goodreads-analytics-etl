# -*- coding: utf-8 -*-
# src/validator/table_validator.py
"""
Module de validation des tables avec modèles Pydantic.

Ce module fournit des modèles Pydantic pour valider l'intégrité des données
avant insertion en base de données. Il vérifie les types, les contraintes
de domaine et l'intégrité référentielle entre les tables.

Features:
    - Validation par ligne avec Pydantic
    - Vérification des contraintes de domaine (ranges, non-null, etc.)
    - Validation de l'intégrité référentielle (FK → PK)
    - Détection des doublons sur clés primaires
    - Rapports d'erreurs détaillés

Author:
    Jules Courné

Date:
    2025-12-30
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Type, TypeVar, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


# ==================== MODÈLES PYDANTIC ====================


class DimBooks(BaseModel):
    """
    Modèle de validation pour la dimension Books.
    
    Attributes:
        bookID (int): Identifiant unique du livre (> 0).
        title (str): Titre du livre (non vide).
    
        1
    """
    bookID: int
    title: str
    
    @field_validator('bookID')
    @classmethod
    def check_bookid(cls, v: int) -> int:
        """Valide que bookID est positif."""
        if v <= 0:
            raise ValueError('bookID must be a positive integer')
        return v
    
    @field_validator('title')
    @classmethod
    def check_title(cls, v: str) -> str:
        """Valide que title n'est pas vide."""
        if not v.strip():
            raise ValueError('title must not be empty')
        return v


class DimPublishers(BaseModel):
    """
    Modèle de validation pour la dimension Publishers.
    
    Attributes:
        publisherID (int): Identifiant unique de l'éditeur (> 0).
        publisher_name (str): Nom de l'éditeur (non vide).
    """
    publisherID: int
    publisher_name: str

    @field_validator('publisherID')
    @classmethod
    def check_publisherid(cls, v: int) -> int:
        """Valide que publisherID est positif."""
        if v <= 0:
            raise ValueError('publisherID must be a positive integer')
        return v

    @field_validator('publisher_name')
    @classmethod
    def check_publisher_name(cls, v: str) -> str:
        """Valide que publisher_name n'est pas vide."""
        if not v or not str(v).strip():
            raise ValueError('publisher_name must not be empty')
        return v


class DimAuthors(BaseModel):
    """
    Modèle de validation pour la dimension Authors.
    
    Attributes:
        authorID (int): Identifiant unique de l'auteur (> 0).
        author_name (str): Nom de l'auteur (non vide).
    """
    authorID: int
    author_name: str

    @field_validator('authorID')
    @classmethod
    def check_authorid(cls, v: int) -> int:
        """Valide que authorID est positif."""
        if v <= 0:
            raise ValueError('authorID must be a positive integer')
        return v

    @field_validator('author_name')
    @classmethod
    def check_author_name(cls, v: str) -> str:
        """Valide que author_name n'est pas vide."""
        if not v.strip():
            raise ValueError('author_name must not be empty')
        return v


class DimGenres(BaseModel):
    """
    Modèle de validation pour la dimension Genres.
    
    Attributes:
        genreID (int): Identifiant unique du genre (> 0).
        genre_name (str): Nom du genre (non vide).
    """
    genreID: int
    genre_name: str

    @field_validator('genreID')
    @classmethod
    def check_genreid(cls, v: int) -> int:
        """Valide que genreID est positif."""
        if v <= 0:
            raise ValueError('genreID must be a positive integer')
        return v

    @field_validator('genre_name')
    @classmethod
    def check_genre_name(cls, v: str) -> str:
        """Valide que genre_name n'est pas vide."""
        if not v.strip():
            raise ValueError('genre_name must not be empty')
        return v


class DimLanguages(BaseModel):
    """
    Modèle de validation pour la dimension Languages.
    
    Attributes:
        languageID (int): Identifiant unique de la langue (> 0).
        language_code (str): Code de la langue (non vide).
        language_name (str): Nom complet de la langue.
        country (str): Pays associé à la langue.
    """
    languageID: int
    language_code: str
    language_name: str
    country: str

    @field_validator('languageID')
    @classmethod
    def check_languageid(cls, v: int) -> int:
        """Valide que languageID est positif."""
        if v <= 0:
            raise ValueError('languageID must be a positive integer')
        return v

    @field_validator('language_code')
    @classmethod
    def check_language_code(cls, v: str) -> str:
        """Valide que language_code n'est pas vide."""
        if not v.strip():
            raise ValueError('language_code must not be empty')
        return v


class DimDates(BaseModel):
    """
    Modèle de validation pour la dimension Dates.
    
    Attributes:
        dateID (int): Identifiant unique de la date (> 0).
        publication_date (datetime): Date de publication (≤ aujourd'hui).
        year (int): Année (≤ année actuelle).
        month (int): Mois (1-12).
        day (int): Jour (1-31).
        month_name (str): Nom du mois.
        day_name (str): Nom du jour.
        quarter (int): Trimestre (1-4).
    
    Note:
        Valide que la date est cohérente (day valide pour month/year).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dateID: int
    publication_date: datetime
    year: int
    month: int
    day: int
    month_name: str
    day_name: str
    quarter: int
    
    @field_validator('dateID')
    @classmethod
    def check_dateid(cls, v: int) -> int:
        """Valide que dateID est positif."""
        if v <= 0:
            raise ValueError('dateID must be a positive integer')
        return v
    
    @field_validator('publication_date')
    @classmethod
    def check_publication_date(cls, v: datetime) -> datetime:
        """Valide que publication_date n'est pas dans le futur."""
        if v > datetime.now():
            raise ValueError('publication_date must be <= today date')
        return v

    @field_validator('year')
    @classmethod
    def check_year(cls, v: int) -> int:
        """Valide que year n'est pas dans le futur."""
        current_year = datetime.now().year
        if v > current_year:
            raise ValueError(f'year must be <= current year ({current_year})')
        return v

    @field_validator('month')
    @classmethod
    def check_month(cls, v: int) -> int:
        """Valide que month est entre 1 et 12."""
        if not 1 <= v <= 12:
            raise ValueError('month must be in interval [1;12]')
        return v

    @field_validator('day')
    @classmethod
    def check_day(cls, v: int, info: ValidationInfo) -> int:
        """Valide que day est valide pour le mois/année."""
        year = info.data.get('year')
        month = info.data.get('month')
        
        # Validation avec la date complète si disponible
        if year is not None and month is not None:
            try:
                datetime(year=year, month=month, day=v)
            except ValueError:
                raise ValueError(
                    f'day {v} is not valid for month {month} and year {year}'
                )
        
        # Validation basique
        if not 1 <= v <= 31:
            raise ValueError('day must be in interval [1;31]')
        
        return v

    @field_validator('quarter')
    @classmethod
    def check_quarter(cls, v: int) -> int:
        """Valide que quarter est entre 1 et 4."""
        if not 1 <= v <= 4:
            raise ValueError('quarter must be in interval [1;4]')
        return v


class BridgeAuthorBook(BaseModel):
    """
    Modèle de validation pour la table de pont Author-Book.
    
    Attributes:
        bookID (int): Identifiant du livre (> 0).
        authorID (int): Identifiant de l'auteur (> 0).
    
    Note:
        Cette table associe les auteurs aux livres (relation N:N).
    """
    bookID: int
    authorID: int

    @field_validator('bookID')
    @classmethod
    def check_bookid(cls, v: int) -> int:
        """Valide que bookID est positif."""
        if v <= 0:
            raise ValueError('bookID must be a positive integer')
        return v

    @field_validator('authorID')
    @classmethod
    def check_authorid(cls, v: int) -> int:
        """Valide que authorID est positif."""
        if v <= 0:
            raise ValueError('authorID must be a positive integer')
        return v


class FactBooks(BaseModel):
    """
    Modèle de validation pour la table de faits Books.
    
    Attributes:
        bookID (int): Identifiant du livre (> 0).
        publisherID (Optional[int]): FK vers Publishers (> 0 ou None).
        languageID (Optional[int]): FK vers Languages (> 0 ou None).
        dateID (Optional[int]): FK vers Dates (> 0 ou None).
        genreID (Optional[int]): FK vers Genres (> 0 ou None).
        average_rating (float): Note moyenne (0-5).
        ratings_count (int): Nombre de notes (≥ 0).
        text_reviews_count (int): Nombre de critiques (≥ 0).
        num_pages (int): Nombre de pages (≥ 0).
        engagement (float): Métrique d'engagement (≥ 0).
    
    Note:
        Les FK peuvent être None (données manquantes tolérées).
    """
    bookID: int
    publisherID: Optional[int] = None
    languageID: Optional[int] = None
    dateID: Optional[int] = None
    genreID: Optional[int] = None
    average_rating: float
    ratings_count: int
    text_reviews_count: int
    num_pages: int
    engagement: float

    @field_validator('bookID')
    @classmethod
    def check_bookid(cls, v: int) -> int:
        """Valide que bookID est positif."""
        if v <= 0:
            raise ValueError('bookID must be a positive integer')
        return v

    @field_validator('publisherID', 'languageID', 'dateID', 'genreID')
    @classmethod
    def check_ids(cls, v: Optional[int]) -> Optional[int]:
        """Valide que les FK sont positives ou None."""
        if v is not None and v <= 0:
            raise ValueError('ID must be a positive integer or None')
        return v

    @field_validator('average_rating')
    @classmethod
    def check_average_rating(cls, v: float) -> float:
        """Valide que average_rating est entre 0 et 5."""
        if not 0 <= v <= 5:
            raise ValueError('average_rating must be in interval [0;5]')
        return v

    @field_validator('ratings_count', 'text_reviews_count', 'num_pages')
    @classmethod
    def check_positive_integer(cls, v: int) -> int:
        """Valide que les compteurs sont positifs."""
        if v < 0:
            raise ValueError('must be a positive integer')
        return v

    @field_validator('engagement')
    @classmethod
    def check_engagement(cls, v: float) -> float:
        """Valide que engagement est positif."""
        if v < 0:
            raise ValueError('engagement must be >= 0')
        return v


# ==================== VALIDATEUR ====================

T = TypeVar('T', bound=BaseModel)


class TableValidator:
    """
    Validateur de tables avec Pydantic et vérification d'intégrité référentielle.
    
    Cette classe valide les DataFrames pandas en utilisant des modèles Pydantic,
    vérifie l'unicité des clés primaires, et contrôle l'intégrité référentielle
    entre les tables (clés étrangères).
    
    Attributes:
        logger (logging.Logger): Logger pour les opérations de validation.
        validation_errors (List[str]): Liste des erreurs critiques détectées.
        validation_warnings (List[str]): Liste des avertissements.
        models (Dict): Mapping table_name → (PydanticModel, id_columns).

    """
    
    # Mapping table → (modèle, colonnes ID)
    MODELS_MAPPING = {
        'dim_books': (DimBooks, 'bookID'),
        'dim_authors': (DimAuthors, 'authorID'),
        'dim_publishers': (DimPublishers, 'publisherID'),
        'dim_languages': (DimLanguages, 'languageID'),
        'dim_dates': (DimDates, 'dateID'),
        'dim_genres': (DimGenres, 'genreID'),
        'bridge_author_book': (BridgeAuthorBook, ['bookID', 'authorID']),
        'fact_books': (FactBooks, 'bookID')
    }
    
    def __init__(self) -> None:
        """Initialise le validateur."""
        self.logger = logging.getLogger('validator')
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
        self.models = self.MODELS_MAPPING
    
    def validate_all(
        self, 
        tables: Dict[str, pd.DataFrame]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Valide toutes les tables avec Pydantic et vérifie l'intégrité référentielle.
        
        Args:
            tables (Dict[str, pd.DataFrame]): Dictionnaire des tables à valider.
                Clés attendues: 'dim_books', 'dim_authors', 'dim_publishers',
                'dim_languages', 'dim_dates', 'dim_genres', 'bridge_author_book',
                'fact_books'.
        
        Returns:
            Tuple[bool, List[str], List[str]]: Tuple contenant :
                - is_valid: True si aucune erreur critique
                - errors: Liste des erreurs critiques
                - warnings: Liste des avertissements

        """
        self.logger.info("=" * 60)
        self.logger.info("VALIDATION DES TABLES AVEC PYDANTIC")
        self.logger.info("=" * 60)
        
        self.validation_errors = []
        self.validation_warnings = []
        
        # Valider chaque table
        for table_name, df in tables.items():
            if table_name not in self.models:
                self.validation_warnings.append(
                    f"Table '{table_name}' sans modèle de validation"
                )
                continue
            
            model_class, id_columns = self.models[table_name]
            self.logger.info(f"Validation de {table_name}...")
            
            try:
                validated_df = self._validate_dimension(df, model_class, id_columns)
                self.logger.info(
                    f"  {table_name} : {len(validated_df)} lignes validées"
                )
            except Exception as e:
                self.validation_errors.append(f"{table_name} : {str(e)}")
                self.logger.error(f"  {table_name} : {str(e)}")
        
        # Vérifier l'intégrité référentielle
        self._check_referential_integrity(tables)
        
        # Résumé
        is_valid = len(self.validation_errors) == 0
        self._log_validation_summary(is_valid)
        
        return is_valid, self.validation_errors, self.validation_warnings
    
    def _validate_dimension(
        self,
        df: pd.DataFrame,
        model_class: Type[T],
        id_columns: Union[str, List[str]]
    ) -> pd.DataFrame:
        """
        Valide un DataFrame avec un modèle Pydantic.
        
        Valide chaque ligne individuellement, vérifie l'unicité des clés
        primaires, et retourne un DataFrame validé.
        
        Args:
            df (pd.DataFrame): DataFrame à valider.
            model_class (Type[T]): Classe Pydantic pour la validation.
            id_columns (Union[str, List[str]]): Colonne(s) d'identifiant unique.
        
        Returns:
            pd.DataFrame: DataFrame avec données validées.
        
        Raises:
            ValueError: Si des erreurs de validation sont détectées ou si
                des doublons sur les clés primaires sont trouvés.
        
        """
        errors = []
        validated_rows = []
        
        # Normaliser id_columns en liste
        if isinstance(id_columns, str):
            id_columns = [id_columns]
        
        # Valider chaque ligne
        for idx, row in df.iterrows():
            try:
                # Convertir types numpy → types Python
                row_dict = self._convert_numpy_types(row.to_dict())
                
                # Valider avec Pydantic
                validated_row = model_class(**row_dict)
                validated_rows.append(validated_row.model_dump())
                
            except Exception as e:
                errors.append(f"Ligne {idx} : {str(e)}")
        
        # Lever exception si erreurs
        if errors:
            error_sample = errors[:5]
            error_msg = "\n".join(error_sample)
            if len(errors) > 5:
                error_msg += f"\n... et {len(errors) - 5} autres erreurs"
            raise ValueError(f"Erreurs de validation:\n{error_msg}")
        
        # Vérifier unicité des IDs
        self._check_unique_ids(df, id_columns)
        
        return pd.DataFrame(validated_rows)
    
    def _check_unique_ids(
        self, 
        df: pd.DataFrame, 
        id_columns: List[str]
    ) -> None:
        """
        Vérifie l'unicité des clés primaires.
        
        Args:
            df (pd.DataFrame): DataFrame à vérifier.
            id_columns (List[str]): Colonnes formant la clé primaire.
        
        Raises:
            ValueError: Si des doublons sont détectés.
        """
        if not id_columns:
            return
        
        duplicates = df.duplicated(subset=id_columns, keep=False)
        if duplicates.any():
            duplicate_pairs = df[duplicates].drop_duplicates(subset=id_columns)
            raise ValueError(
                f"Combinaisons d'IDs dupliquées dans {id_columns}.\n"
                f"Exemples: {duplicate_pairs[id_columns].head(3).to_dict('records')}"
            )
    
    def _convert_numpy_types(self, row_dict: dict) -> dict:
        """
        Convertit les types numpy en types Python natifs.
        
        Args:
            row_dict (dict): Dictionnaire avec types numpy.
        
        Returns:
            dict: Dictionnaire avec types Python natifs.
        
        Note:
            Pydantic ne gère pas nativement les types numpy.
        """
        converted = {}
        for k, v in row_dict.items():
            if isinstance(v, (np.int64, np.int32, np.integer)):
                converted[k] = int(v)
            elif isinstance(v, (np.float64, np.float32, np.floating)):
                converted[k] = float(v)
            elif isinstance(v, np.str_):
                converted[k] = str(v)
            elif pd.isna(v):
                converted[k] = None
            else:
                converted[k] = v
        return converted
    
    def _check_referential_integrity(
        self, 
        tables: Dict[str, pd.DataFrame]
    ) -> None:
        """
        Vérifie l'intégrité référentielle entre les tables.
        
        Contrôle que toutes les clés étrangères de fact_books et
        bridge_author_book référencent des clés primaires existantes
        dans leurs dimensions respectives.
        
        Args:
            tables (Dict[str, pd.DataFrame]): Dictionnaire des tables.
        
        Note:
            Les violations sont ajoutées à validation_errors.
        """
        self.logger.debug("Vérification de l'intégrité référentielle...")
        
        # Vérifier fact_books
        if 'fact_books' in tables:
            self._check_fact_integrity(tables)
        
        # Vérifier bridge_author_book
        if 'bridge_author_book' in tables:
            self._check_bridge_integrity(tables)
        
        if not self.validation_errors:
            self.logger.info("  ✓ Intégrité référentielle respectée")
    
    def _check_fact_integrity(self, tables: Dict[str, pd.DataFrame]) -> None:
        """Vérifie l'intégrité référentielle de fact_books."""
        fact = tables['fact_books']
        
        integrity_checks = [
            ('dim_books', 'bookID'),
            ('dim_publishers', 'publisherID'),
            ('dim_languages', 'languageID'),
            ('dim_dates', 'dateID'),
            ('dim_genres', 'genreID')
        ]
        
        for dim_name, fk_col in integrity_checks:
            if dim_name not in tables or fk_col not in fact.columns:
                continue
            
            dim = tables[dim_name]
            orphan_fks = fact[~fact[fk_col].isin(dim[fk_col])][fk_col].dropna()
            
            if len(orphan_fks) > 0:
                self.validation_errors.append(
                    f"Intégrité référentielle : {len(orphan_fks)} valeurs de "
                    f"fact_books.{fk_col} absentes de {dim_name}.{fk_col}"
                )
    
    def _check_bridge_integrity(self, tables: Dict[str, pd.DataFrame]) -> None:
        """Vérifie l'intégrité référentielle de bridge_author_book."""
        bridge = tables['bridge_author_book']
        
        # Vérifier bookID
        if 'dim_books' in tables and 'bookID' in bridge.columns:
            dim_books = tables['dim_books']
            orphan_books = bridge[~bridge['bookID'].isin(dim_books['bookID'])]['bookID']
            if len(orphan_books) > 0:
                self.validation_errors.append(
                    f"Bridge : {len(orphan_books)} bookID absents de dim_books"
                )
        
        # Vérifier authorID
        if 'dim_authors' in tables and 'authorID' in bridge.columns:
            dim_authors = tables['dim_authors']
            orphan_authors = bridge[
                ~bridge['authorID'].isin(dim_authors['authorID'])
            ]['authorID']
            if len(orphan_authors) > 0:
                self.validation_errors.append(
                    f"Bridge : {len(orphan_authors)} authorID absents de dim_authors"
                )
    
    def _log_validation_summary(self, is_valid: bool) -> None:
        """Affiche le résumé de validation."""
        self.logger.info("")
        self.logger.info("─" * 60)
        self.logger.info("RÉSUMÉ DE LA VALIDATION")
        self.logger.info("─" * 60)
        
        if is_valid:
            self.logger.info("VALIDATION RÉUSSIE - Aucune erreur critique")
        else:
            self.logger.error(
                f"VALIDATION ÉCHOUÉE - {len(self.validation_errors)} erreurs"
            )
        
        if self.validation_warnings:
            self.logger.warning(f"⚠ {len(self.validation_warnings)} avertissements")
        
        self.logger.info("─" * 60)
        
        # Détails erreurs
        if self.validation_errors:
            self.logger.error("\nERREURS CRITIQUES :")
            for i, error in enumerate(self.validation_errors, 1):
                self.logger.error(f"  {i}. {error}")
        
        # Détails warnings
        if self.validation_warnings:
            self.logger.warning("\nAVERTISSEMENTS :")
            for i, warning in enumerate(self.validation_warnings, 1):
                self.logger.warning(f"  {i}. {warning}")
        
        self.logger.info("=" * 60)


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def validate_dimension(
    df: pd.DataFrame,
    model_class: Type[T],
    id_columns: Union[str, List[str]]
) -> pd.DataFrame:
    """
    Fonction utilitaire pour valider une dimension.
    
    Args:
        df (pd.DataFrame): DataFrame à valider.
        model_class (Type[T]): Classe Pydantic de validation.
        id_columns (Union[str, List[str]]): Colonne(s) d'ID unique.
    
    Returns:
        pd.DataFrame: DataFrame validé.
    
    """
    validator = TableValidator()
    return validator._validate_dimension(df, model_class, id_columns)