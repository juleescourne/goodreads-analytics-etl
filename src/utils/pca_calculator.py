# -*- coding: utf-8 -*-
"""
Module de calcul et chargement PCA avec clustering.

Le module prépare les variables, gère les valeurs non finies, calcule une PCA
et applique un clustering K-means pour enrichir les données analytiques.

Author:
    Jules Courné

Date:
    2025-12-31
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler


class PCACalculator:
    """
    Calculateur d'ACP et de clustering pour livres, auteurs et éditeurs.
    
    Gestion robuste des valeurs NaN/inf et des cas limites.
    """
    
    # Constantes de configuration
    N_COMPONENTS = 2
    N_CLUSTERS = 3
    RANDOM_STATE = 42
    
    # Features par entité
    BOOK_FEATURES = ["average_rating", "ratings_count", "engagement", "num_pages"]
    BOOK_LOG_FEATURES = ["ratings_count", "engagement", "num_pages"]
    
    AUTHOR_FEATURES = ["average_rating", "ratings_count", "engagement", "num_pages", "book_count"]
    AUTHOR_LOG_FEATURES = ["ratings_count", "engagement", "num_pages", "book_count"]
    
    PUBLISHER_FEATURES = ["average_rating", "ratings_count", "engagement", "num_pages", "book_count"]
    PUBLISHER_LOG_FEATURES = ["ratings_count", "engagement", "num_pages", "book_count"]
    
    # Labels de clusters par type d'entité
    CLUSTER_LABELS = {
        'book': ["Best-sellers", "Livres émergents", "Livres de niche"],
        'author': ["Auteurs populaires", "Auteurs émergents", "Auteurs de niche"],
        'publisher': ["Grandes maisons d'édition", "Éditeurs intermédiaires", "Éditeurs spécialisés"]
    }
    
    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialise le calculateur PCA."""
        self.conn = conn
        self.logger = logging.getLogger('pca')
        
        # Paramètres PCA/Clustering
        self.n_components = self.N_COMPONENTS
        self.n_clusters = self.N_CLUSTERS
        self.random_state = self.RANDOM_STATE
        
        # Features par entité
        self.book_features = self.BOOK_FEATURES
        self.book_log_features = self.BOOK_LOG_FEATURES
        self.author_features = self.AUTHOR_FEATURES
        self.author_log_features = self.AUTHOR_LOG_FEATURES
        self.publisher_features = self.PUBLISHER_FEATURES
        self.publisher_log_features = self.PUBLISHER_LOG_FEATURES
        
        self.logger.info("PCACalculator initialisé avec succès")
    
    def calculate_and_load_all(self) -> bool:
        """Calcule PCA et charge directement dans les tables dédiées."""
        self.logger.info("=" * 60)
        self.logger.info("CALCUL ET CHARGEMENT PCA")
        self.logger.info("=" * 60)
        
        try:
            # 1. Calculer PCA pour toutes les entités
            results = self.calculate_all()
            
            if not results:
                self.logger.error("Échec du calcul PCA")
                return False
            
            # 2. Charger dans les tables
            self.logger.info("\n" + "─" * 60)
            self.logger.info("CHARGEMENT DANS LES TABLES PCA")
            self.logger.info("─" * 60)
            
            success = True
            success &= self._load_book_pca(results['book_pca'])
            success &= self._load_author_pca(results['author_pca'])
            success &= self._load_publisher_pca(results['publisher_pca'])
            
            if success:
                self.logger.info("=" * 60)
                self.logger.info("PCA CALCULÉE ET CHARGÉE AVEC SUCCÈS")
                self.logger.info("=" * 60)
            
            return success
            
        except Exception as e:
            self.logger.error(
                f"Erreur lors du calcul/chargement PCA : {e}", 
                exc_info=True
            )
            return False
    
    def calculate_all(self) -> Optional[Dict[str, pd.DataFrame]]:
        """Calcule l'ACP et les clusters pour toutes les entités."""
        self.logger.info("\nCALCUL DES COMPOSANTES PRINCIPALES")
        self.logger.info("─" * 60)
        
        try:
            # 1. Récupérer données depuis DB
            books_df = self._get_books_metrics()
            authors_df = self._get_authors_aggregated()
            publishers_df = self._get_publishers_aggregated()
            
            if books_df.empty or authors_df.empty or publishers_df.empty:
                self.logger.error("Données insuffisantes pour le calcul PCA")
                return None
            
            # 2. Calculer PCA pour chaque entité
            results = {}
            
            self.logger.info("\n1. Calcul PCA Livres...")
            results['book_pca'] = self._calculate_pca_for_books(books_df)
            
            self.logger.info("\n2. Calcul PCA Auteurs...")
            results['author_pca'] = self._calculate_pca_for_authors(authors_df)
            
            self.logger.info("\n3. Calcul PCA Éditeurs...")
            results['publisher_pca'] = self._calculate_pca_for_publishers(publishers_df)
            
            self.logger.info("\nCalcul PCA terminé")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul PCA : {e}", exc_info=True)
            return None
    
    # ========================================================================
    # RÉCUPÉRATION DES DONNÉES
    # ========================================================================
    
    def _get_books_metrics(self) -> pd.DataFrame:
        """Récupère les métriques des livres depuis FactBooks."""
        query = """
            SELECT 
                bookID,
                average_rating,
                ratings_count,
                engagement,
                num_pages
            FROM FactBooks
            WHERE ratings_count > 0 
              AND num_pages > 0
              AND average_rating > 0
        """
        
        df = pd.read_sql_query(query, self.conn)
        self.logger.info(f"  {len(df)} livres récupérés")
        
        return df
    
    def _get_authors_aggregated(self) -> pd.DataFrame:
        """Agrège les métriques par auteur."""
        query = """
            SELECT 
                b.authorID,
                AVG(f.average_rating) as average_rating,
                AVG(f.ratings_count) as ratings_count,
                AVG(f.engagement) as engagement,
                AVG(f.num_pages) as num_pages,
                COUNT(DISTINCT f.bookID) as book_count
            FROM BridgeAuthorBook b
            JOIN FactBooks f ON b.bookID = f.bookID
            GROUP BY b.authorID
            HAVING book_count >= 2
                AND AVG(f.ratings_count) > 0
                AND AVG(f.num_pages) > 0
                AND AVG(f.average_rating) > 0
        """
        
        df = pd.read_sql_query(query, self.conn)
        self.logger.info(f"  {len(df)} auteurs agrégés")
        
        return df
    
    def _get_publishers_aggregated(self) -> pd.DataFrame:
        """Agrège les métriques par éditeur."""
        query = """
            SELECT 
                publisherID,
                AVG(average_rating) as average_rating,
                AVG(ratings_count) as ratings_count,
                AVG(engagement) as engagement,
                AVG(num_pages) as num_pages,
                COUNT(DISTINCT bookID) as book_count
            FROM FactBooks
            GROUP BY publisherID
            HAVING book_count >= 2
                AND AVG(ratings_count) > 0
                AND AVG(num_pages) > 0
                AND AVG(average_rating) > 0
        """
        
        df = pd.read_sql_query(query, self.conn)
        self.logger.info(f" {len(df)} éditeurs agrégés")
        
        return df
    
    # ========================================================================
    # CALCUL PCA PAR ENTITÉ
    # ========================================================================
    
    def _calculate_pca_for_books(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule PCA et clusters pour les livres."""
        scaled_data, valid_indices, df_transformed = self._prepare_features(
            df, 
            self.book_features,
            self.book_log_features,
            id_column="bookID"
        )
        
        result_df = self._apply_pca_kmeans(
            df_transformed,
            scaled_data,
            valid_indices,
            "bookID"
        )
        
        result_df = self._assign_cluster_labels(
            result_df,
            "ratings_count",
            entity_type='book'
        )
        
        self.logger.info(f"  {len(result_df)} livres avec PCA/clusters")
        
        return result_df
    
    def _calculate_pca_for_authors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule PCA et clusters pour les auteurs."""
        scaled_data, valid_indices, df_transformed = self._prepare_features(
            df,
            self.author_features,
            self.author_log_features,
            id_column="authorID"
        )
        
        result_df = self._apply_pca_kmeans(
            df_transformed,
            scaled_data,
            valid_indices,
            "authorID"
        )
        
        result_df = self._assign_cluster_labels(
            result_df,
            "ratings_count",
            entity_type='author'
        )
        
        self.logger.info(f"  {len(result_df)} auteurs avec PCA/clusters")
        
        return result_df
    
    def _calculate_pca_for_publishers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule PCA et clusters pour les éditeurs."""
        scaled_data, valid_indices, df_transformed = self._prepare_features(
            df,
            self.publisher_features,
            self.publisher_log_features,
            id_column="publisherID"
        )
        
        result_df = self._apply_pca_kmeans(
            df_transformed,
            scaled_data,
            valid_indices,
            "publisherID"
        )
        
        result_df = self._assign_cluster_labels(
            result_df,
            "ratings_count",
            entity_type='publisher'
        )
        
        self.logger.info(f"  {len(result_df)} éditeurs avec PCA/clusters")
        
        return result_df
    
    # ========================================================================
    # PRÉPARATION DES FEATURES - VERSION CORRIGÉE
    # ========================================================================
    
    def _prepare_features(
        self,
        df: pd.DataFrame,
        features: List[str],
        log_features: Optional[List[str]] = None,
        id_column: Optional[str] = None
    ) -> Tuple[np.ndarray, pd.Index, pd.DataFrame]:
        """
        Prépare les features avec transformation log et normalisation.
        
        Nettoie les NaN/inf après chaque transformation.
        """
        # 1. Nettoyer et filtrer
        df_clean = df[features].copy().dropna()
        
        # Filtres spécifiques
        if "ratings_count" in features:
            df_clean = df_clean[df_clean["ratings_count"] > 0]
        if "num_pages" in features:
            df_clean = df_clean[df_clean["num_pages"] > 0]
        if "book_count" in features:
            df_clean = df_clean[df_clean["book_count"] >= 2]
        if "average_rating" in features:
            df_clean = df_clean[df_clean["average_rating"] > 0]
        
        self.logger.debug(f"    Après filtrage: {len(df_clean)} lignes")
        
        # 2. Transformation log
        df_log = df_clean.copy()
        if log_features:
            for col in log_features:
                if col in df_log.columns:
                    df_log[col] = np.log1p(df_log[col])
        
        # Vérifier NaN/inf après log
        df_log = df_log.replace([np.inf, -np.inf], np.nan).dropna()
        self.logger.debug(f"    Après log: {len(df_log)} lignes valides")
        
        if len(df_log) == 0:
            raise ValueError("Aucune donnée valide après transformation log")
        
        # 3. Normalisation
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df_log)
        
        # Vérification rapide NaN/inf
        # Au lieu de vérifier ligne par ligne, on vérifie globalement
        has_nan = np.isnan(scaled_data).any()
        has_inf = np.isinf(scaled_data).any()
        
        if has_nan or has_inf:
            # Seulement si nécessaire, on filtre ligne par ligne
            self.logger.debug(f"    NaN/inf détectés, nettoyage en cours...")
            mask_valid = ~(np.isnan(scaled_data).any(axis=1) | np.isinf(scaled_data).any(axis=1))
            scaled_data_clean = scaled_data[mask_valid]
            valid_indices_clean = df_log.index[mask_valid]
            self.logger.debug(f"    {len(scaled_data_clean)}/{len(scaled_data)} lignes conservées")
        else:
            # Pas de NaN/inf, on garde tout (cas le plus courant)
            scaled_data_clean = scaled_data
            valid_indices_clean = df_log.index
        
        self.logger.debug(f"    Après scaling: {len(scaled_data_clean)} lignes valides")
        
        if len(scaled_data_clean) == 0:
            raise ValueError("Aucune donnée valide après nettoyage des NaN/inf")
        
        # 4. DataFrame avec valeurs normalisées
        df_scaled = pd.DataFrame(
            scaled_data_clean,
            index=valid_indices_clean,
            columns=features
        )
        
        # Ajouter ID si spécifié
        if id_column and id_column in df.columns:
            df_scaled[id_column] = df.loc[valid_indices_clean, id_column].values
        
        return scaled_data_clean, valid_indices_clean, df_scaled
    
    # ========================================================================
    # APPLICATION PCA ET CLUSTERING
    # ========================================================================
    
    def _apply_pca_kmeans(
        self,
        df: pd.DataFrame,
        scaled_data: np.ndarray,
        valid_indices: pd.Index,
        id_column: str
    ) -> pd.DataFrame:
        """Apply PCA and K-means while handling small/degenerate datasets."""
        n_samples, n_features = scaled_data.shape
        result_df = df.copy()

        # Degenerate datasets (one row or zero variance) do not contain
        # meaningful directions for PCA or multiple K-means clusters. Keeping
        # zero-valued components makes the pipeline deterministic and avoids
        # noisy numerical warnings while preserving the rows.
        unique_rows = np.unique(scaled_data, axis=0)
        zero_variance = np.all(np.var(scaled_data, axis=0) == 0)

        if n_samples < 2 or zero_variance:
            self.logger.warning(
                "    Dataset too small or constant for PCA/K-means; "
                "using neutral components and a single cluster."
            )
            result_df["PC1"] = 0.0
            result_df["PC2"] = 0.0
            result_df["Cluster"] = 0
            return result_df

        # PCA: compute as many components as the data supports, then pad PC2
        # with zeros if only one component can be estimated.
        n_components_actual = min(self.n_components, n_samples, n_features)
        self.logger.info(
            f"    Calcul PCA sur {n_samples} lignes "
            f"({n_components_actual} composantes)..."
        )
        pca = PCA(n_components=n_components_actual, random_state=self.random_state)
        pca_result = pca.fit_transform(scaled_data)

        result_df["PC1"] = pca_result[:, 0]
        result_df["PC2"] = (
            pca_result[:, 1] if n_components_actual > 1 else np.zeros(n_samples)
        )

        # K-means cannot create more meaningful clusters than there are unique
        # observations.
        n_clusters_actual = min(self.n_clusters, len(unique_rows), n_samples)
        self.logger.info(f"    Calcul K-means ({n_clusters_actual} clusters)...")

        if n_clusters_actual == 1:
            clusters = np.zeros(n_samples, dtype=int)
        else:
            kmeans = KMeans(
                n_clusters=n_clusters_actual,
                random_state=self.random_state,
                n_init=10
            )
            clusters = kmeans.fit_predict(scaled_data)

        result_df["Cluster"] = clusters

        variance_ratio = pca.explained_variance_ratio_
        pc1 = variance_ratio[0] if len(variance_ratio) > 0 else 0.0
        pc2 = variance_ratio[1] if len(variance_ratio) > 1 else 0.0
        self.logger.info(
            f"    Variance expliquée : PC1={pc1:.2%}, PC2={pc2:.2%}"
        )

        return result_df

    # ========================================================================
    # ATTRIBUTION DES LABELS
    # ========================================================================
    
    def _assign_cluster_labels(
        self,
        df: pd.DataFrame,
        ranking_metric: str,
        entity_type: str
    ) -> pd.DataFrame:
        """Attribue des labels descriptifs aux clusters."""
        # Calculer moyenne de la métrique par cluster
        cluster_stats = df.groupby("Cluster")[ranking_metric].mean().sort_values(
            ascending=False
        )
        
        # Mapping cluster → label
        cluster_to_label = {}
        sorted_clusters = cluster_stats.index.tolist()
        labels = self.CLUSTER_LABELS.get(entity_type, [])
        
        for rank, cluster_id in enumerate(sorted_clusters):
            if rank < len(labels):
                cluster_to_label[cluster_id] = labels[rank]
            else:
                cluster_to_label[cluster_id] = f"Cluster {cluster_id}"
        
        df["Cluster_Label"] = df["Cluster"].map(cluster_to_label)
        
        # Log distribution
        for cluster_id, label in cluster_to_label.items():
            count = len(df[df["Cluster"] == cluster_id])
            percentage = count / len(df) * 100
            self.logger.info(f"      • {label}: {count} ({percentage:.1f}%)")
        
        return df
    
    # ========================================================================
    # CHARGEMENT DANS LES TABLES
    # ========================================================================
    
    def _load_book_pca(self, df: pd.DataFrame) -> bool:
        """Charge les résultats PCA livres dans BookPCA."""
        try:
            self.logger.info("\n→ Chargement BookPCA...")
            
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM BookPCA")
            
            columns = [
                "bookID", "PC1", "PC2", "Cluster", "Cluster_Label",
                "average_rating", "ratings_count", "engagement", "num_pages"
            ]
            
            data = df[columns].copy()
            records = [tuple(row) for row in data.values]
            
            placeholders = ", ".join(["?" for _ in columns])
            query = f"INSERT INTO BookPCA ({', '.join(columns)}) VALUES ({placeholders})"
            
            cursor.executemany(query, records)
            self.conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM BookPCA")
            count = cursor.fetchone()[0]
            
            self.logger.info(
                f"  ✓ {count} lignes insérées dans BookPCA"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"  Erreur lors du chargement BookPCA : {e}")
            self.conn.rollback()
            return False
    
    def _load_author_pca(self, df: pd.DataFrame) -> bool:
        """Charge les résultats PCA auteurs dans AuthorPCA."""
        try:
            self.logger.info("\nChargement AuthorPCA...")
            
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM AuthorPCA")
            
            columns = [
                "authorID", "PC1", "PC2", "Cluster", "Cluster_Label",
                "average_rating", "ratings_count", "engagement", "num_pages", "book_count"
            ]
            
            data = df[columns].copy()
            records = [tuple(row) for row in data.values]
            
            placeholders = ", ".join(["?" for _ in columns])
            query = f"INSERT INTO AuthorPCA ({', '.join(columns)}) VALUES ({placeholders})"
            
            cursor.executemany(query, records)
            self.conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM AuthorPCA")
            count = cursor.fetchone()[0]
            
            self.logger.info(
                f"  {count} lignes insérées dans AuthorPCA"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"  Erreur lors du chargement AuthorPCA : {e}")
            self.conn.rollback()
            return False
    
    def _load_publisher_pca(self, df: pd.DataFrame) -> bool:
        """Charge les résultats PCA éditeurs dans PublisherPCA."""
        try:
            self.logger.info("\nChargement PublisherPCA...")
            
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM PublisherPCA")
            
            columns = [
                "publisherID", "PC1", "PC2", "Cluster", "Cluster_Label",
                "average_rating", "ratings_count", "engagement", "num_pages", "book_count"
            ]
            
            data = df[columns].copy()
            records = [tuple(row) for row in data.values]
            
            placeholders = ", ".join(["?" for _ in columns])
            query = f"INSERT INTO PublisherPCA ({', '.join(columns)}) VALUES ({placeholders})"
            
            cursor.executemany(query, records)
            self.conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM PublisherPCA")
            count = cursor.fetchone()[0]
            
            self.logger.info(
                f"  {count} lignes insérées dans PublisherPCA"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"  Erreur lors du chargement PublisherPCA : {e}")
            self.conn.rollback()
            return False


# ============================================================================
# FONCTIONS WRAPPER POUR COMPATIBILITÉ
# ============================================================================

def calculate_pca_clusters(conn: sqlite3.Connection) -> Optional[Dict[str, pd.DataFrame]]:
    """Calcule PCA sans charger dans la DB (fonction de compatibilité)."""
    calculator = PCACalculator(conn)
    return calculator.calculate_all()


def calculate_and_load_pca(conn: sqlite3.Connection) -> bool:
    """Calcule PCA ET charge dans les tables (fonction de compatibilité)."""
    calculator = PCACalculator(conn)
    return calculator.calculate_and_load_all()