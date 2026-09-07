# -*- coding: utf-8 -*-
# main.py
"""
Script principal du pipeline ETL pour l'analyse de livres.

Ce module orchestre l'intégralité du pipeline ETL : extraction des données
CSV, transformation et nettoyage, création du modèle en étoile, validation,
et chargement dans une base SQLite pour analyse dans Power BI.

Pipeline:
    1. Initialisation et chargement de la configuration
    2. Extraction des données depuis CSV
    3. Transformation et nettoyage des données
    4. Création des tables dimensionnelles (Star Schema)
    5. Validation avec Pydantic
    6. Chargement dans SQLite avec recalcul PCA conditionnel

Features:
    - Configuration centralisée via YAML
    - Logging structuré à chaque étape
    - Validation stricte des données
    - Gestion d'erreurs robuste
    - Mode retry optionnel
    - Métriques de performance

Author:
    Jules Courné

Date:
    2025-12-31
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from src.extract.csv_extractor import CSVExtractor
from src.load.db_loader import DatabaseLoader
from src.transform.book_transformer import BooksTransformer
from src.transform.table_builder import TableBuilder
from src.utils.config_loader import ConfigLoader
from src.validator.table_validator import TableValidator


class ETLPipeline:
    """
    Orchestrateur du pipeline ETL complet.
    
    Cette classe encapsule toutes les étapes du pipeline ETL et gère
    leur exécution séquentielle avec logging et gestion d'erreurs.
    
    Attributes:
        config (ConfigLoader): Configuration chargée depuis YAML.
        logger (logging.Logger): Logger principal du pipeline.
        start_time (datetime): Horodatage de début d'exécution.

    """
    
    def __init__(
        self,
        config_path: str = "config/config.yaml",
        logging_config_path: str = "config/logging_config.yaml"
    ) -> None:
        """
        Initialise le pipeline ETL.
        
        Args:
            config_path (str): Chemin vers le fichier de configuration.
            logging_config_path (str): Chemin vers la configuration logging.
        """
        self.config = ConfigLoader(config_path, logging_config_path)
        self.logger = logging.getLogger(__name__)
        self.start_time: Optional[datetime] = None
        
    def run(self) -> int:
        """
        Exécute le pipeline ETL complet.
        
        Orchestre toutes les phases du pipeline : extraction, transformation,
        validation et chargement. Gère les erreurs et log les performances.
        
        Returns:
            int: Code de sortie (0 = succès, 1 = échec).
        
        """
        self._print_header()
        self.start_time = datetime.now()
        
        try:
            # Phase 1 : Initialisation
            self._log_initialization()
            
            # Phase 2 : Extraction
            df_raw = self._extract_data()
            if df_raw is None:
                return 1
            
            # Phase 3 : Transformation
            df_clean = self._transform_data(df_raw)
            if df_clean is None:
                return 1
            
            # Phase 4 : Création tables
            tables = self._build_tables(df_clean)
            if tables is None:
                return 1
            
            # Phase 5 : Validation
            if not self._validate_tables(tables):
                return 1
            
            # Phase 6 : Chargement
            if not self._load_data(tables, df_clean):
                return 1
            
            # Résumé final
            self._print_summary(df_clean)
            
            return 0
            
        except FileNotFoundError as e:
            self.logger.error(f"Fichier non trouvé : {e}")
            print(f"\n  ERREUR : {e}")
            return 1
            
        except Exception as e:
            self.logger.critical(
                f"Erreur critique dans le pipeline : {e}", 
                exc_info=True
            )
            print(f"\n  ERREUR CRITIQUE : {e}")
            print("Consultez les logs pour plus de détails")
            return 1
    
    def _print_header(self) -> None:
        """Affiche l'en-tête du pipeline."""
        print("=" * 60)
        print("PIPELINE ETL - Extraction vers SQLite pour Power BI")
        print("=" * 60)
    
    def _log_initialization(self) -> None:
        """Log les informations d'initialisation."""
        print("\n[1/6] Chargement de la configuration...")
        self.logger.info("=" * 60)
        self.logger.info("DÉMARRAGE DU PIPELINE ETL")
        self.logger.info("=" * 60)
        
        # Paramètres clés
        self.logger.info(f"Mode d'exécution : {self.config.get('execution.mode')}")
        self.logger.info(f"Base de données : {self.config.get_db_path()}")
        self.logger.info(f"Batch size : {self.config.get('pipeline.batch_size')}")
    
    def _extract_data(self) -> Optional[pd.DataFrame]:
        """
        Extrait les données depuis le CSV.
        
        Returns:
            Optional[pd.DataFrame]: DataFrame extrait ou None si erreur.
        """
        print("\n[2/6] Extraction des données CSV...")
        self.logger.info("-" * 60)
        self.logger.info("PHASE D'EXTRACTION")
        self.logger.info("-" * 60)
        
        extractor = CSVExtractor(self.config)
        df = extractor.extract_csv("books.csv")
        
        if df is None:
            self.logger.error("Échec de l'extraction")
            return None
        
        # Statistiques
        stats = extractor.get_statistics(df)
        self.logger.info(f"Extraction réussie : {stats['nb_lignes']} lignes extraites")
        
        return df
    
    def _transform_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Transforme et nettoie les données.
        
        Args:
            df (pd.DataFrame): DataFrame brut à transformer.
        
        Returns:
            Optional[pd.DataFrame]: DataFrame transformé ou None si erreur.
        """
        print("\n[3/6] Transformation des données...")
        self.logger.info("-" * 60)
        self.logger.info("PHASE DE TRANSFORMATION")
        self.logger.info("-" * 60)
        
        transformer = BooksTransformer(self.config)
        df_clean = transformer.transform_books(df)
        
        if df_clean is None:
            self.logger.error("Échec de la transformation")
            return None
        
        self.logger.info("Transformation terminée avec succès")
        
        return df_clean
    
    def _build_tables(self, df: pd.DataFrame) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Crée les tables dimensionnelles (Star Schema).
        
        Args:
            df (pd.DataFrame): DataFrame nettoyé.
        
        Returns:
            Optional[Dict[str, pd.DataFrame]]: Dictionnaire des tables ou None.
        """
        print("\n[4/6] Création des tables dimensionnelles...")
        self.logger.info("-" * 60)
        self.logger.info("PHASE DE CRÉATION DES TABLES")
        self.logger.info("-" * 60)
        
        builder = TableBuilder(self.config)
        tables = builder.create_all_tables(df)
        
        self.logger.info("Tables créées avec succès")
        
        return tables
    
    def _validate_tables(self, tables: Dict[str, pd.DataFrame]) -> bool:
        """
        Valide les tables avec Pydantic.
        
        Args:
            tables (Dict[str, pd.DataFrame]): Dictionnaire des tables à valider.
        
        Returns:
            bool: True si validation réussie, False sinon.
        """
        print("\n[5/6] Validation des tables...")
        self.logger.info("-" * 60)
        self.logger.info("PHASE DE VALIDATION")
        self.logger.info("-" * 60)
        
        validator = TableValidator()
        is_valid, errors, warnings = validator.validate_all(tables)
        
        if not is_valid:
            self.logger.error("Validation des tables échouée")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
        
        self.logger.info("Tables validées avec succès")
        
        return True
    
    def _load_data(
        self, 
        tables: Dict[str, pd.DataFrame], 
        df_source: pd.DataFrame
    ) -> bool:
        """
        Charge les données dans SQLite avec logique incrémentale.
        
        Args:
            tables (Dict[str, pd.DataFrame]): Tables à charger.
            df_source (pd.DataFrame): DataFrame source pour BridgeAuthorBook.
        
        Returns:
            bool: True si chargement réussi, False sinon.
        """
        print("\n[6/6] Chargement dans la base de données...")
        self.logger.info("-" * 60)
        self.logger.info("PHASE DE CHARGEMENT")
        self.logger.info("-" * 60)
        
        loader = DatabaseLoader(self.config)
        success = loader.load_all_tables(tables, df_source)
        
        if not success:
            self.logger.error("Échec du chargement")
            return False
        
        self.logger.info("Chargement terminé avec succès")
        
        return True
    
    def _print_summary(self, df_clean: pd.DataFrame) -> None:
        """
        Affiche le résumé d'exécution du pipeline.
        
        Args:
            df_clean (pd.DataFrame): DataFrame final traité.
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("PIPELINE TERMINÉ AVEC SUCCÈS")
        print("=" * 60)
        print(f"Durée d'exécution : {duration:.2f} secondes")
        print(f"Lignes traitées : {len(df_clean):,}")
        print(f"\nBase de données créée : {self.config.get_db_path()}")
        print(f"Logs disponibles dans : {self.config.get('paths.logs')}")
        
        self.logger.info("=" * 60)
        self.logger.info(f"PIPELINE TERMINÉ - Durée: {duration:.2f}s")
        self.logger.info("=" * 60)


def main() -> int:
    """
    Fonction principale pour exécuter le pipeline ETL.
    
    Point d'entrée principal du script. Initialise et exécute le pipeline.
    
    Returns:
        int: Code de sortie (0 = succès, 1 = échec).
    
    """
    pipeline = ETLPipeline()
    return pipeline.run()


def run_with_retry(
    max_retries: Optional[int] = None,
    retry_delay: Optional[int] = None
) -> int:
    """
    Exécute le pipeline avec mécanisme de retry en cas d'échec.
    
    Utile pour gérer les échecs temporaires (problèmes réseau, fichiers
    verrouillés, etc.).
    
    Args:
        max_retries (Optional[int]): Nombre maximum de tentatives.
            Si None, utilise la valeur de la configuration.
        retry_delay (Optional[int]): Délai entre tentatives en secondes.
            Si None, utilise la valeur de la configuration.
    
    Returns:
        int: Code de sortie (0 = succès, 1 = échec).
    
    """
    config = ConfigLoader()
    logger = logging.getLogger(__name__)
    
    # Paramètres de retry
    max_retries = max_retries or config.get('pipeline.max_retries', 3)
    retry_delay = retry_delay or config.get('pipeline.retry_delay', 5)
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Tentative {attempt}/{max_retries}")
        
        result = main()
        
        if result == 0:
            return 0
        
        if attempt < max_retries:
            logger.warning(
                f"Échec - Nouvelle tentative dans {retry_delay}s..."
            )
            time.sleep(retry_delay)
    
    logger.error(f"Pipeline échoué après {max_retries} tentatives")
    return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)