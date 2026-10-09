"""Règles simples utilisées par les notebooks et testées sur de petits exemples."""
import pandas as pd


def lire_compteur(serie, prefixe):
    """Un compteur absent, mal formé ou négatif reste inconnu, distinct de zéro."""
    nombres = serie.astype('string').str.extract('^' + prefixe + r':(\d+)$')[0]
    return pd.to_numeric(nombres, errors='coerce')


def isoler_versions(table, colonnes):
    """Retirer les répétitions exactes et isoler toutes les versions en conflit."""
    repetitions = int(table.duplicated(colonnes).sum())
    uniques = table.drop_duplicates(colonnes).copy()
    id_invalide = uniques['Id'].isna() | uniques['Id'].le(0) | uniques['Id'].mod(1).ne(0)
    conflit = uniques['Id'].duplicated(keep=False) & ~id_invalide
    titre_absent = uniques['Name'].fillna('').str.strip().eq('')
    uniques['MotifQuarantaine'] = ''
    uniques.loc[titre_absent, 'MotifQuarantaine'] = 'Titre absent'
    uniques.loc[conflit, 'MotifQuarantaine'] = 'Versions différentes pour un même Id'
    uniques.loc[id_invalide, 'MotifQuarantaine'] = 'Identifiant invalide'
    exclus = uniques['MotifQuarantaine'].ne('')
    return (uniques.loc[~exclus].drop(columns='MotifQuarantaine').copy(),
            uniques.loc[exclus].copy(), repetitions)


def normaliser_langues(serie):
    """Harmoniser les codes renseignés, sans déduire la langue du titre."""
    return serie.astype('string').str.strip().str.lower().replace({
        '': pd.NA, 'en-us': 'eng', 'en-gb': 'eng', 'en-ca': 'eng', 'en': 'eng',
        'fra': 'fre', 'fr': 'fre',
    }).fillna('non_renseigne')


def cle_titre_auteur(table):
    titre = (table['Titre'].astype('string').str.casefold()
             .str.replace(r'[^\w\s]', ' ', regex=True)
             .str.replace(r'\s+', ' ', regex=True).str.strip())
    auteur = (table['Auteurs'].astype('string').str.casefold()
              .str.replace(r'\s+', ' ', regex=True).str.strip())
    return titre + ' | ' + auteur


def selectionner(table, minimum_notes=100, minimum_note=4, maximum_par_auteur=None, taille=20):
    """Filtrer, choisir une édition représentante, classer, puis plafonner par auteur.

    Le plafond porte sur le libellé auteur normalisé, pas sur chaque contributeur.
    Les entrées restent intactes. Une liste trop petite n'est pas complétée hors critères.
    """
    if minimum_notes < 1 or not 1 <= minimum_note <= 5 or taille < 1:
        raise ValueError('Seuils de sélection invalides')
    if maximum_par_auteur is not None and maximum_par_auteur < 1:
        raise ValueError('Le plafond auteur doit être positif')
    masque = (table['Langue'].eq('Français') & table['Note'].ge(minimum_note)
              & table['NbNotes'].ge(minimum_notes) & ~table['AuteurAbsent']
              & ~table['EditeurAbsent'] & table['Pages'].between(1, 5000))
    candidats = table.loc[masque].copy()
    candidats['CleTitreAuteur'] = cle_titre_auteur(candidats)
    representants = (candidats.sort_values(['NbNotes', 'IdLivre'], ascending=[False, True])
                    .drop_duplicates('CleTitreAuteur')
                    .sort_values(['Note', 'NbNotes', 'IdLivre'], ascending=[False, False, True]))
    eligibles = representants
    if maximum_par_auteur is not None:
        auteurs = (representants['Auteurs'].astype('string').str.casefold()
                   .str.replace(r'\s+', ' ', regex=True).str.strip())
        eligibles = representants.loc[representants.groupby(auteurs).cumcount().lt(maximum_par_auteur)]
    selection = eligibles.head(taille).copy()
    selection['RangSelection'] = range(1, len(selection) + 1)
    return candidats, representants, selection
