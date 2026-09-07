# -*- coding: utf-8 -*-
"""
Module d'extraction des données CSV.

Ce module fournit la classe CSVExtractor pour extraire et valider
des données depuis des fichiers CSV avec gestion de l'archivage.

Author:
    Jules Courné

Date:
    2025-12-30
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from src.utils.config_loader import ConfigLoader


class CSVExtractor:
    """
    Extracteur de données CSV avec validation et archivage.
    
    Cette classe permet d'extraire des données depuis des fichiers CSV,
    de valider les colonnes attendues et d'archiver automatiquement
    les fichiers sources.
    
    Attributes:
        config (ConfigLoader): Instance de configuration.
        logger (logging.Logger): Logger pour le module d'extraction.
        raw_data_path (Path): Chemin vers les données brutes.
        processed_path (Path): Chemin vers les données traitées.
        archive_path (Path): Chemin vers les archives.
        encoding (str): Encodage des fichiers CSV.
        delimiter (str): Délimiteur CSV.
        decimal (str): Séparateur décimal.
        skip_rows (int): Nombre de lignes à ignorer.
        enable_archive (bool): Active/désactive l'archivage.
        archive_format (str): Format du timestamp pour l'archivage.

    """
    
    def __init__(self, config: ConfigLoader) -> None:
        """
        Initialise l'extracteur CSV avec la configuration.
        
        Args:
            config (ConfigLoader): Instance de ConfigLoader contenant
                les paramètres du pipeline.
        
        Raises:
            KeyError: Si une clé de configuration est manquante.
        """
        self.config = config
        self.logger = logging.getLogger('extract')
        
        # Chemins
        self.raw_data_path = Path(self.config.get('paths.raw_data'))
        self.processed_path = Path(self.config.get('paths.processed_data'))
        self.archive_path = Path(self.config.get('paths.archive'))
        
        # Paramètres CSV
        self.encoding = self.config.get('csv.encoding', 'utf-8')
        self.delimiter = self.config.get('csv.delimiter', ',')
        self.decimal = self.config.get('csv.decimal', '.')
        self.skip_rows = self.config.get('csv.skip_rows', 0)
        
        # Archivage
        self.enable_archive = self.config.get('pipeline.enable_archive', True)
        self.archive_format = self.config.get('pipeline.archive_format', '%Y%m%d_%H%M%S')
        
        self.logger.info("CSVExtractor initialisé avec succès")
    
    def extract_csv(
        self, 
        filename: str, 
        table_name: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Extrait les données d'un fichier CSV avec validation.
        
        Lit un fichier CSV, valide ses colonnes si spécifié, et archive
        le fichier source si l'archivage est activé.
        
        Args:
            filename (str): Nom du fichier CSV à extraire (ex: 'books.csv').
            table_name (Optional[str]): Nom de la table pour valider les
                colonnes attendues. Si None, aucune validation n'est effectuée.
        
        Returns:
            Optional[pd.DataFrame]: DataFrame contenant les données extraites,
                ou None en cas d'erreur.
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            pd.errors.EmptyDataError: Si le fichier est vide.
            UnicodeDecodeError: Si l'encodage est incorrect.

        """
        filepath = self.raw_data_path / filename
        self.logger.info(f"Début de l'extraction : {filename}")
        
        # Vérifier l'existence du fichier
        if not filepath.exists():
            self.logger.error(f"Fichier non trouvé : {filepath}")
            return None
        
        try:
            # Lire le CSV
            df = self._read_csv(filepath)
            
            # Logger les informations
            self.logger.info(
                f"  Fichier lu : {len(df)} lignes, {len(df.columns)} colonnes"
            )
            self.logger.debug(f"Colonnes trouvées : {list(df.columns)}")
            
            # Valider les colonnes
            if table_name:
                self._validate_columns(df, table_name)
            
            # Archiver le fichier
            if self.enable_archive:
                self._archive_file(filepath)
            
            return df
            
        except pd.errors.EmptyDataError:
            self.logger.error(f"Le fichier {filename} est vide")
            return None
        
        except UnicodeDecodeError as e:
            self.logger.error(
                f"Erreur d'encodage pour {filename}: {e}. "
                f"Encodage actuel: {self.encoding}"
            )
            return None
        
        except Exception as e:
            self.logger.error(
                f"Erreur lors de l'extraction de {filename}: {str(e)}", 
                exc_info=True
            )
            return None
    
    def _read_csv(self, filepath: Path) -> pd.DataFrame:
        """
        Lit un fichier CSV avec les paramètres configurés.
        
        Args:
            filepath (Path): Chemin complet du fichier CSV.
        
        Returns:
            pd.DataFrame: DataFrame contenant les données du CSV.
        
        Raises:
            pd.errors.EmptyDataError: Si le fichier est vide.
            UnicodeDecodeError: Si l'encodage est incorrect.
        """
        return pd.read_csv(
            filepath,
            encoding=self.encoding,
            delimiter=self.delimiter,
            decimal=self.decimal,
            skiprows=self.skip_rows
        )
    
    def _validate_columns(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Valide que toutes les colonnes attendues sont présentes.
        
        Args:
            df (pd.DataFrame): DataFrame à valider.
            table_name (str): Nom de la table dans la configuration.
        
        Note:
            Les colonnes manquantes sont loggées en warning mais
            n'interrompent pas le traitement.
        """
        expected_cols = self.config.get(f'csv.expected_columns.{table_name}')
        
        if not expected_cols:
            return
        
        missing_cols = set(expected_cols) - set(df.columns)
        
        if missing_cols:
            self.logger.warning(f"Colonnes manquantes : {missing_cols}")
        else:
            self.logger.info("  Toutes les colonnes attendues sont présentes")
    
    def _archive_file(self, filepath: Path) -> None:
        """
        Archive le fichier source avec un timestamp.
        
        Copie le fichier dans le répertoire d'archive avec un suffixe
        timestamp pour conserver l'historique des extractions.
        
        Args:
            filepath (Path): Chemin du fichier à archiver.
        
        Examples:
            Le fichier 'books.csv' devient 'books_20251230_143025.csv'
        """
        try:
            timestamp = datetime.now().strftime(self.archive_format)
            archive_filename = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            archive_filepath = self.archive_path / archive_filename
            
            shutil.copy2(filepath, archive_filepath)
            self.logger.info(f" Fichier archivé : {archive_filename}")
            
        except Exception as e:
            self.logger.warning(f"Impossible d'archiver {filepath.name}: {e}")
    
    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Génère des statistiques descriptives sur le DataFrame.
        
        Calcule diverses métriques sur le DataFrame pour faciliter
        l'analyse de la qualité des données.
        
        Args:
            df (pd.DataFrame): DataFrame à analyser.
        
        Returns:
            Dict: Dictionnaire contenant les statistiques suivantes:
                - nb_lignes (int): Nombre total de lignes
                - nb_colonnes (int): Nombre total de colonnes
                - colonnes (list): Liste des noms de colonnes
                - nb_valeurs_manquantes (dict): Compte des NaN par colonne
                - nb_doublons (int): Nombre de lignes dupliquées
                - types_donnees (dict): Types de données par colonne
        
        """
        stats = {
            'nb_lignes': len(df),
            'nb_colonnes': len(df.columns),
            'colonnes': list(df.columns),
            'nb_valeurs_manquantes': df.isnull().sum().to_dict(),
            'nb_doublons': df.duplicated().sum(),
            'types_donnees': df.dtypes.astype(str).to_dict()
        }
        
        self.logger.info(
            f"Statistiques : {stats['nb_lignes']} lignes, "
            f"{stats['nb_doublons']} doublons"
        )
        
        return stats