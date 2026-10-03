# Dictionnaire des données et KPI

**Grain principal : une fiche Goodreads conservée après contrôle, identifiée par `IdLivre`.** Les sources et leurs empreintes sont décrites dans [data/README.md](../data/README.md).

## 1. Champs sources

| Champ | Sens et utilisation |
|---|---|
| Id | Identifiant Goodreads de la fiche ; clé, jamais une mesure à additionner |
| Name | Titre de la fiche ; devient Titre |
| Authors | Champ texte des auteurs/contributeurs ; conservé entier, sans déduire les rôles |
| ISBN | Identifiant fourni, conservé en texte avec ses zéros ; pas utilisé comme clé unique ni validé ici par sa clé de contrôle |
| Rating | Note moyenne annoncée, de 0 à 5 ; devient NoteSource |
| RatingDist1 à RatingDist5 | Effectifs par note, stockés sous la forme `1:123` à `5:123` |
| RatingDistTotal | Compteur total annoncé, sous la forme `total:123` ; devient NbNotes |
| pagesNumber / PagesNumber | Pagination annoncée ; les deux noms sont harmonisés en PagesSource |
| PublishYear | Année annoncée ; devient AnneeSource |
| PublishMonth / PublishDay | Champs jour/mois ambigus, non utilisés pour fabriquer une date |
| Publisher | Éditeur renseigné sur la fiche ; devient Editeur |
| Language | Code langue, parfois absent ; devient CodeLangueSource |
| CountsOfReview | Compteur de critiques conservé pour l'audit ; son articulation avec les autres compteurs n'est pas assez claire pour calculer un taux d'engagement |

Les descriptions et `Count of text reviews`, absents de certains fichiers, ne sont pas chargés. Aucun genre, pays ou score d'engagement n'est créé.

## 2. Champs préparés

| Champ | Règle |
|---|---|
| IdLivre | Id entier positif, unique après retrait des répétitions et quarantaine des conflits |
| FichierSource / LigneSource | Fichier et position de l'enregistrement lu, à partir de 1 |
| DistributionValide | Cinq effectifs présents et non négatifs, dont la somme égale NbNotes |
| NoteRecalculee | Somme de (note × effectif) / NbNotes ; vide si zéro note |
| NoteExploitable | Distribution valide, NbNotes > 0, NoteSource entre 1 et 5, écart avec la note recalculée ≤ 0,01 |
| Note | NoteSource si exploitable, sinon vide ; aucune imputation par une moyenne |
| CodeLangue | Code normalisé ; variantes anglaises réunies dans eng, variantes françaises dans fre |
| Langue | Libellé regroupé pour le rapport ; une langue absente reste Non renseignée |
| Pages | Pagination entière strictement positive, sinon vide |
| PagesAtypiques | Pagination > 5 000 ; alerte à vérifier, pas suppression du catalogue |
| AnneePublication | Année entière comprise entre 1 et 2020, sinon vide |
| LangueAbsente / EditeurAbsent / AuteurAbsent | Indicateurs de métadonnée absente avant ajout d'un libellé de présentation |
| PagesAbsentes / AnneeInvalide | Valeurs non exploitables après contrôle |
| CleTitreAuteur | Titre et auteurs en minuscules, espaces normalisés et ponctuation du titre ignorée ; rapprochement textuel limité |
| TitreAuteurRepete | Plusieurs fiches conservées partagent cette clé ; ne prouve pas un doublon à supprimer |

Les libellés « Non renseigné » servent à afficher les catégories manquantes. Les données numériques manquantes restent vides.

## 3. Segments

| Segment | Bornes |
|---|---|
| TrancheNotes | 0 ; 1-99 ; 100-999 ; 1 000-9 999 ; 10 000 et plus ; non renseigné |
| TranchePages | 1-150 ; 151-300 ; 301-600 ; 601 et plus ; non renseigné |
| PeriodePublication | Avant 1950 ; 1950-1979 ; 1980-1999 ; 2000-2009 ; 2010-2020 ; non renseignée |

Les colonnes `OrdreNotes`, `OrdrePages` et `OrdrePeriode` servent uniquement au tri dans Power BI. L'année de publication ne mesure pas une évolution de l'activité Goodreads.

## 4. KPI

Sauf indication contraire, les mesures portent sur les fiches conservées dans le contexte de filtre courant.

| KPI | Calcul et dénominateur | Lecture |
|---|---|---|
| Nombre de fiches | Nombre de lignes de Livres, avec IdLivre unique | Taille du périmètre, pas nombre d'œuvres uniques |
| Fiches avec note exploitable | Nombre de NoteExploitable = vrai | Couverture des notes |
| Part avec note exploitable | Fiches avec note exploitable / nombre de fiches | Pourcentage |
| Note moyenne des fiches | Moyenne des Note non vides | Chaque fiche a le même poids ; pas une note moyenne de lecteurs uniques |
| Note médiane des fiches | Médiane des Note non vides | Complément à la moyenne |
| Médiane du nombre de notes | Médiane de NbNotes, zéros inclus et compteur invalide exclu | Volume typique associé à une fiche |
| Part avec au moins 100 notes | Fiches avec NbNotes ≥ 100 / nombre de fiches | Seuil descriptif, sans garantie de représentativité |
| Part de langue absente | LangueAbsente = vrai / nombre de fiches | La langue inconnue reste au dénominateur |
| Part de pagination inexploitable | PagesAbsentes = vrai / nombre de fiches | Donnée manquante ou non positive/non entière |
| Part de titre et auteur répétés | TitreAuteurRepete = vrai / nombre de fiches | Fiches appartenant à un groupe répété, pas nombre de répétitions retirées |
| Nombre de candidats | Candidat = vrai | Critères éditoriaux ci-dessous |
| Nombre de représentants | RepresentantSelection = vrai | Une fiche candidate par clé titre/auteur |
| Liste de travail | DansTop20 = vrai | Jusqu'à 20 fiches classées sur la source complète |
| Candidats du scénario | Effectif de Sensibilite pour le couple note minimum / nombre minimum de notations | Catalogue français complet, avant rapprochement ; ne pas sommer les scénarios |

Dans les CSV de contrôle, les pourcentages sont multipliés par 100. Les mesures DAX renvoient une fraction formatée en `%`. Un ratio sans dénominateur reste vide.

## 5. Règles de sélection

`Candidat` vaut vrai si : français renseigné, Note ≥ 4, NbNotes ≥ 100, auteur et éditeur renseignés, Pages positive et ≤ 5 000. L'ISBN, l'année et la disponibilité doivent être examinés avant une publication commerciale ; ils ne sont pas inventés.

`RepresentantSelection` conserve, parmi les candidats d'une même clé titre/auteur, le plus grand NbNotes, puis le plus petit IdLivre en cas d'égalité. Les autres fiches restent dans le catalogue.

`RangSelection` classe ces représentants par Note décroissante, NbNotes décroissant, puis IdLivre croissant. `DansTop20` marque les 20 premiers. **Ces marqueurs sont calculés sur la source complète : un filtre du dashboard réduit la liste affichée, sans refaire le classement.**

Le rapprochement textuel ne garantit pas une œuvre unique : une variation de titre peut masquer une autre édition. Les seuils de note, de volume, de pagination et de 30 fiches par groupe dans les graphiques sont des choix de travail, pas des tests statistiques.

## 6. Modèle Power BI

`Langues[Langue]` filtre `Livres[Langue]` en relation **1 vers plusieurs**, à sens unique. Les mesures restent au grain fiche. Les auteurs ne sont pas éclatés, ce qui évite de multiplier les notes et les fiches dans une jointure.

`AuditImport` est une petite table indépendante issue du journal de contrôle. Ses indicateurs d'import ne suivent pas les filtres du catalogue. Les taux de qualité filtrables sont recalculés depuis les colonnes de `Livres`.

`Sensibilite` importe les neuf couples de seuils du notebook approfondi : `NoteMinimum`, `NotesMinimum`, `NbFiches` et `NbTitresAuteurs`. Elle n'a pas de relation au catalogue. La page de sélection fixe la note minimale à 4 et compare 100, 500 et 1 000 notations, avec les mêmes critères de métadonnées. Les effectifs ne se cumulent pas. La mesure `Candidats du scenario` utilise `SELECTEDVALUE(NbFiches)` et reste vide quand plusieurs effectifs sont présents.

Le graphique des auteurs utilise `Liste de travail` par libellé `Auteurs`, avec `DansTop20 = vrai`. Les auteurs/contributeurs ne sont pas éclatés. Sans filtre : 20 fiches et 12 libellés ; Hiromu Arakawa représente 6 fiches, soit 30 %. Les menus réduisent ce graphique et le tableau de la liste, sans recalcul du classement. Les clics sur les graphiques de cette page ne filtrent pas les autres visuels.
