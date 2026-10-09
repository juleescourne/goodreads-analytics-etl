# Données Goodreads

Source : [dataset Kaggle de Bahram Jannesar](https://www.kaggle.com/datasets/bahramjannesarr/goodreads-book-datasets-10m), **version 18**, mise à jour le **3 décembre 2020**. Téléchargement le **1er octobre 2026**. Licence déclarée par Kaggle : **CC0: Public Domain**.

Le [manifeste sources.json](sources.json) contient le nom, la taille, l'URL versionnée et l'empreinte SHA-256 de chacun des **23 fichiers de livres**. Leur réunion compte **1 850 310 lignes brutes**. Les sept fichiers `user_rating*.csv` sont hors périmètre : l'étude porte sur le catalogue, pas sur une recommandation personnalisée.

## Source brute

Les CSV se trouvent dans `raw/kaggle_v18`. Ils sont conservés intacts et exclus de Git. Depuis la racine, `python scripts/telecharger_donnees.py` les télécharge ou vérifie les copies déjà présentes. Aucun identifiant Kaggle n'est stocké dans le dépôt.

Si l'accès automatisé n'est plus disponible, télécharger manuellement **la version 18**, extraire ses 23 fichiers `book*.csv` dans ce dossier puis relancer le script pour vérifier les empreintes. Un fichier dont l'empreinte diffère provoque un arrêt explicite.

Le [dictionnaire](../docs/Dictionnaire.md) donne le sens des champs utilisés. Le nom `PagesNumber` est harmonisé avec `pagesNumber`. Les descriptions et les champs variables de critiques textuelles ne sont pas chargés. Aucune source de genre, de prix ou de stock n'est ajoutée.

## Exports

Exécuter les trois notebooks avec `python main.py`. Le séparateur des exports est `;`, l'encodage UTF-8 avec BOM, et le séparateur décimal est le point. Les valeurs numériques manquantes restent vides. L'ISBN doit rester du texte.

| Fichier dans processed | Grain et usage |
|---|---|
| livres.csv | Une fiche conservée par IdLivre ; base du nettoyage et des analyses |
| quarantaine.csv | Une version source isolée ; 166 lignes pour 83 identifiants contradictoires |
| audit_sources.csv | Un fichier source avec son volume lu ; 23 lignes |
| controle_qualite.csv | Un contrôle de qualité et son effectif ; bilan de l'import complet |
| controle_kpi.csv | Une ligne de KPI globaux ; les pourcentages sont déjà multipliés par 100 |
| livres_powerbi.csv | Une fiche conservée avec segments, indicateurs de qualité et marqueurs de sélection |
| langues.csv | Une catégorie de langue par ligne ; dimension du rapport |
| selection_initiale.csv | Les 20 fiches initiales sans plafond auteur |
| comparaison_selections.csv | Six scénarios : stabilité, diversité, notes et tailles des groupes |
| listes_scenarios.csv | Les six listes recalculées, soit 120 lignes |
| mouvements_selections.csv | Les entrées et sorties par rapport au seuil 100 de chaque règle |
| sensibilite.csv | Un couple de seuils de note et de volume ; 9 combinaisons |
| selection_francais.csv | Une proposition par ligne ; 20 fiches, maximum deux par libellé auteur |

Le modèle Power BI importe `livres_powerbi.csv`, `langues.csv`, `controle_qualite.csv` et `sensibilite.csv`. La table de sensibilité est indépendante : ses neuf scénarios décrivent le catalogue français complet, avant rapprochement titre/auteur. Les menus du rapport ne les recalculent pas. Les autres exports servent à l'analyse et au contrôle. `python scripts/verifier_exports.py` rapproche les exports, les règles de sélection et les neuf scénarios.

Les exports sont régénérables et exclus de Git. Les chiffres à commenter sont dans les notebooks exécutés et dans [Analyse.md](../docs/Analyse.md). Ne pas confondre « fiche Goodreads », « œuvre unique », « lecteur » et « vente ».


Le modèle importe aussi comparaison_selections.csv dans ComparaisonSelections, indépendante des menus. Le script scripts/preparer_livrables.py copie uniquement les petites listes dans docs/livrables, génère les figures, la synthèse PDF et parcours.json pour le portfolio. Les 1,85 million de fiches ne sont pas embarquées dans le site.
