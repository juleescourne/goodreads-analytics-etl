# -*- coding: utf-8 -*-
"""
Module de chargement des configurations et initialisation du logging.

Ce module fournit une classe ConfigLoader pour charger les fichiers de
configuration YAML (config.yaml et logging_config.yaml), initialiser
le système de logging, et créer automatiquement les répertoires nécessaires.

Features:
    - Chargement YAML avec gestion d'erreurs
    - Configuration centralisée du logging
    - Création automatique des répertoires
    - Accès aux paramètres avec notation pointée
    - Validation de l'existence des fichiers

Author:
    Jules Courné

Date:
    2025-12-30
"""

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigLoader:
    """
    Gestionnaire de configuration YAML avec initialisation du logging.
    
    Cette classe charge les configurations depuis des fichiers YAML,
    initialise le système de logging selon la configuration fournie,
    et crée automatiquement les répertoires nécessaires au pipeline.
    
    Attributes:
        config_path (Path): Chemin vers le fichier de configuration principal.
        logging_config_path (Path): Chemin vers le fichier de configuration logging.
        config (Dict[str, Any]): Dictionnaire contenant toute la configuration.
    
    Note:
        Les répertoires spécifiés dans la configuration sont créés automatiquement
        lors de l'initialisation.
    
    """
    
    DEFAULT_CONFIG_PATH = "config/config.yaml"
    DEFAULT_LOGGING_PATH = "config/logging_config.yaml"
    
    def __init__(
        self, 
        config_path: str = DEFAULT_CONFIG_PATH,
        logging_config_path: str = DEFAULT_LOGGING_PATH
    ) -> None:
        """
        Initialise le chargeur de configuration.
        
        Charge les fichiers YAML, configure le logging et crée les répertoires.
        
        Args:
            config_path (str): Chemin vers config.yaml.
            logging_config_path (str): Chemin vers logging_config.yaml.
        
        Raises:
            FileNotFoundError: Si config.yaml n'est pas trouvé.
            ValueError: Si le fichier YAML est mal formaté.
        
        Examples:
            >>> # Configuration par défaut
            >>> config = ConfigLoader()
            
            >>> # Configuration personnalisée
            >>> config = ConfigLoader('custom/config.yaml', 'custom/logging.yaml')
        """
        self.config_path = Path(config_path)
        self.logging_config_path = Path(logging_config_path)
        self.config: Optional[Dict[str, Any]] = None
        
        # Pipeline d'initialisation
        self._load_config()
        self._setup_logging()
        self._create_directories()
    
    def _load_config(self) -> None:
        """
        Charge le fichier config.yaml.
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            ValueError: Si le YAML est invalide.
        
        Note:
            Affiche un message de confirmation lors du chargement réussi.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            print(f"Configuration chargée depuis {self.config_path}")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Fichier de configuration non trouvé : {self.config_path}"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Erreur lors du parsing du YAML : {e}")
    
    def _setup_logging(self) -> None:
        """
        Configure le système de logging depuis logging_config.yaml.
        
        Si le fichier n'existe pas, utilise une configuration par défaut.
        Crée automatiquement le répertoire 'logs' si nécessaire.
        
        Note:
            En cas d'absence du fichier de configuration, une configuration
            par défaut (INFO level) est utilisée.
        
        """
        try:
            with open(self.logging_config_path, 'r', encoding='utf-8') as f:
                logging_config = yaml.safe_load(f)
            
            # Créer le dossier logs
            Path("logs").mkdir(exist_ok=True)
            
            # Configurer le logging
            logging.config.dictConfig(logging_config)
            print(f"Logging configuré depuis {self.logging_config_path}")
            
        except FileNotFoundError:
            # Fallback : configuration par défaut
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logging.warning(
                f"Fichier logging non trouvé : {self.logging_config_path}, "
                "configuration par défaut utilisée"
            )
    
    def _create_directories(self) -> None:
        """
        Crée les répertoires nécessaires au pipeline.
        
        Crée automatiquement tous les répertoires spécifiés dans la
        configuration (raw_data, processed_data, archive, logs, database).
        
        Note:
            Utilise parents=True pour créer les répertoires parents si nécessaire.
            Ignore les erreurs si les répertoires existent déjà.
        """
        directories = [
            self.config['paths']['raw_data'],
            self.config['paths']['processed_data'],
            self.config['paths']['archive'],
            self.config['paths']['logs'],
            Path(self.config['paths']['database']).parent
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration avec notation pointée.
        
        Permet d'accéder aux valeurs imbriquées en utilisant la notation
        pointée (ex: 'database.name' pour accéder à config['database']['name']).
        
        Args:
            key (str): Clé de configuration avec notation pointée.
            default (Any): Valeur par défaut si la clé n'existe pas.
        
        Returns:
            Any: Valeur de configuration ou valeur par défaut.
        
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            elif isinstance(value, list):
                # Support des index de liste
                try:
                    index = int(k)
                    value = value[index]
                except (ValueError, IndexError):
                    return default
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Retourne l'intégralité de la configuration.
        
        Returns:
            Dict[str, Any]: Dictionnaire complet de configuration.

        """
        return self.config
    
    def get_db_path(self) -> str:
        """
        Retourne le chemin complet de la base de données.
        
        Returns:
            str: Chemin vers le fichier de base de données SQLite.
        
        """
        return self.config['paths']['database']
    
    def get_table_schemas(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des schémas de tables définis dans la configuration.
        
        Returns:
            List[Dict[str, Any]]: Liste des définitions de tables avec
                leurs schémas SQL.
        
        Note:
            Chaque élément contient typiquement 'name' et 'schema'.
        
            ...
        """
        return self.config['database']['tables']
    
    def has_key(self, key: str) -> bool:
        """
        Vérifie si une clé existe dans la configuration.
        
        Args:
            key (str): Clé avec notation pointée.
        
        Returns:
            bool: True si la clé existe, False sinon.
        
        """
        return self.get(key) is not None
    
    def reload(self) -> None:
        """
        Recharge la configuration depuis les fichiers YAML.
        
        Utile pour recharger la configuration sans redémarrer l'application.
        
        Raises:
            FileNotFoundError: Si les fichiers n'existent plus.
            ValueError: Si le YAML est invalide.
        
        """
        self._load_config()
        self._setup_logging()

