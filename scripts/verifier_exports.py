"""Vérifier les exports et les règles métier après l'exécution des notebooks."""
from pathlib import Path
import json
import math

import nbformat
import pandas as pd

racine = Path(__file__).resolve().parents[1]
dossier = racine / 'data/processed'

print('Lecture des exports...', flush=True)
livres = pd.read_csv(dossier / 'livres_powerbi.csv', sep=';', dtype={'ISBN': 'string'})
qualite = pd.read_csv(dossier / 'controle_qualite.csv', sep=';').set_index('Controle')['Effectif']
kpi = pd.read_csv(dossier / 'controle_kpi.csv', sep=';').iloc[0]
sources = pd.read_csv(dossier / 'audit_sources.csv', sep=';')
quarantaine = pd.read_csv(dossier / 'quarantaine.csv', sep=';')
langues = pd.read_csv(dossier / 'langues.csv', sep=';')
selection = pd.read_csv(dossier / 'selection_francais.csv', sep=';', dtype={'ISBN': 'string'})
sensibilite = pd.read_csv(dossier / 'sensibilite.csv', sep=';')

# Retrouver les lignes et les clés, sans mélanger catalogue et quarantaine.
assert len(livres) == qualite['Fiches conservées'] == kpi['NbFiches']
assert qualite['Lignes brutes'] == len(livres) + qualite['Répétitions retirées'] + len(quarantaine)
assert len(quarantaine) == qualite['Lignes en quarantaine']
assert livres['IdLivre'].notna().all() and livres['IdLivre'].is_unique
assert not livres['IdLivre'].isin(quarantaine['Id']).any()
assert langues['Langue'].is_unique and langues['Langue'].notna().all()
assert livres['Langue'].isin(langues['Langue']).all()
assert len(sources) == 23
assert sources['LignesBrutes'].sum() == qualite['Lignes brutes']

# Les notes vides, les zéros et les compteurs invalides ont des sens différents.
assert livres.loc[~livres['NoteExploitable'], 'Note'].isna().all()
assert livres.loc[livres['NoteExploitable'], 'Note'].between(1, 5).all()
assert livres.loc[livres['NoteExploitable'], 'NbNotes'].gt(0).all()
assert livres['NbNotes'].dropna().ge(0).all()
assert livres.loc[livres['NbNotes'].eq(0), 'Note'].isna().all()
assert livres['NbNotes'].eq(0).sum() == qualite['Sans notation']
assert (~livres['DistributionValide']).sum() == qualite['Distribution incohérente']
assert livres['LangueAbsente'].sum() == qualite['Langue absente']
assert livres['PagesAtypiques'].sum() == qualite['Pagination supérieure à 5 000 pages']
assert livres['TitreAuteurRepete'].sum() == qualite['Titre et auteur répétés']
assert livres['NoteExploitable'].sum() == kpi['NbFichesNoteExploitable']
assert math.isclose(livres['Note'].mean(), kpi['NoteMoyenneFiches'], abs_tol=1e-10)
assert livres['Note'].median() == kpi['NoteMedianeFiches']
assert livres['NbNotes'].median() == kpi['MedianeNbNotes']
assert math.isclose(100 * livres['NbNotes'].ge(100).mean(), kpi['PartAvec100NotesPct'], abs_tol=1e-10)
assert math.isclose(100 * livres['LangueAbsente'].mean(), kpi['PartLangueAbsentePct'], abs_tol=1e-10)
assert livres['Langue'].eq('Français').sum() == kpi['NbFichesFrancais']

# Recalculer la candidature depuis les données, puis contrôler la liste.
candidat_attendu = (
    livres['Langue'].eq('Français') & livres['Note'].ge(4) & livres['NbNotes'].ge(100)
    & ~livres['AuteurAbsent'] & ~livres['EditeurAbsent']
    & livres['Pages'].between(1, 5000)
)
assert livres['Candidat'].equals(candidat_attendu)
candidats = livres.loc[candidat_attendu].copy()
candidats['Cle'] = (
    candidats['Titre'].str.casefold().str.replace(r'[^\w\s]', ' ', regex=True)
    .str.replace(r'\s+', ' ', regex=True).str.strip()
    + ' | ' + candidats['Auteurs'].str.casefold().str.replace(r'\s+', ' ', regex=True).str.strip()
)
representants = candidats.sort_values(['NbNotes', 'IdLivre'], ascending=[False, True]).drop_duplicates('Cle')
classes = representants.sort_values(['Note', 'NbNotes', 'IdLivre'], ascending=[False, False, True])
auteurs = classes['Auteurs'].str.casefold().str.replace(r'\s+', ' ', regex=True).str.strip()
attendus = classes.loc[classes.groupby(auteurs).cumcount().lt(2)].head(20)
assert set(livres.loc[livres['RepresentantSelection'], 'IdLivre']) == set(representants['IdLivre'])
assert selection['IdLivre'].tolist() == attendus['IdLivre'].tolist()
assert selection['IdLivre'].tolist() == livres.loc[livres['DansTop20']].sort_values('RangSelection')['IdLivre'].tolist()
assert selection['RangSelection'].tolist() == list(range(1, len(selection) + 1))
assert len(selection) == 20 and selection['IdLivre'].is_unique

# Les scénarios affichés dans Power BI doivent retrouver le catalogue français.
assert len(sensibilite) == 9
assert not sensibilite.duplicated(['NoteMinimum', 'NotesMinimum']).any()
base_francais = livres.loc[
    livres['Langue'].eq('Français') & ~livres['AuteurAbsent']
    & ~livres['EditeurAbsent'] & livres['Pages'].between(1, 5000)
].copy()
base_francais['Cle'] = (
    base_francais['Titre'].str.casefold().str.replace(r'[^\w\s]', ' ', regex=True)
    .str.replace(r'\s+', ' ', regex=True).str.strip()
    + ' | ' + base_francais['Auteurs'].str.casefold().str.replace(r'\s+', ' ', regex=True).str.strip()
)
for scenario in sensibilite.itertuples(index=False):
    groupe = base_francais.loc[
        base_francais['Note'].ge(scenario.NoteMinimum)
        & base_francais['NbNotes'].ge(scenario.NotesMinimum)
    ]
    assert len(groupe) == scenario.NbFiches
    assert groupe['Cle'].nunique() == scenario.NbTitresAuteurs

# Comparer chaque liste recalculée et ses mouvements à la référence de la même règle.
comparaison = pd.read_csv(dossier / 'comparaison_selections.csv', sep=';')
listes = pd.read_csv(dossier / 'listes_scenarios.csv', sep=';')
mouvements = pd.read_csv(dossier / 'mouvements_selections.csv', sep=';')
assert len(comparaison) == 6 and comparaison['Scenario'].is_unique
assert len(listes) == 120
for ligne in comparaison.itertuples(index=False):
    groupe = base_francais.loc[base_francais['Note'].ge(4) & base_francais['NbNotes'].ge(ligne.NotesMinimum)]
    candidats_groupes = groupe.sort_values(['NbNotes', 'IdLivre'], ascending=[False, True]).drop_duplicates('Cle')
    classes = candidats_groupes.sort_values(['Note', 'NbNotes', 'IdLivre'], ascending=[False, False, True])
    if ligne.Regle == 'Deux par auteur':
        auteurs = classes['Auteurs'].str.casefold().str.replace(r'\s+', ' ', regex=True).str.strip()
        classes = classes.loc[classes.groupby(auteurs).cumcount().lt(2)]
    attendu = classes.head(20)
    obtenu = listes.loc[listes['Scenario'].eq(ligne.Scenario)].sort_values('RangSelection')
    assert obtenu['IdLivre'].tolist() == attendu['IdLivre'].tolist()
    assert len(groupe) == ligne.NbCandidats and len(candidats_groupes) == ligne.NbRepresentants
    assert len(obtenu) == ligne.NbFiches == 20
    assert obtenu['Auteurs'].nunique() == ligne.NbAuteurs
    assert obtenu['Auteurs'].value_counts().max() == ligne.MaxParAuteur
    assert math.isclose(obtenu['Note'].mean(), ligne.NoteMoyenne, abs_tol=1e-10)
    assert obtenu['Note'].min() == ligne.NoteMinimum
    reference = listes.loc[listes['Regle'].eq(ligne.Regle) & listes['NotesMinimum'].eq(100)]
    ids, ids_ref = set(obtenu['IdLivre']), set(reference['IdLivre'])
    assert len(ids & ids_ref) == ligne.NbCommunsReference
    assert len(ids - ids_ref) == ligne.NbEntrees and len(ids_ref - ids) == ligne.NbSorties
    for mouvement, attendus in [('Entrée', ids - ids_ref), ('Sortie', ids_ref - ids)]:
        observes = mouvements.loc[mouvements['Scenario'].eq(ligne.Scenario) & mouvements['Mouvement'].eq(mouvement)]
        assert set(observes['IdLivre']) == attendus
    initiale = listes.loc[listes['Regle'].eq('Initiale') & listes['NotesMinimum'].eq(100)]
    assert len(ids & set(initiale['IdLivre'])) == ligne.CommunsInitiale100
assert selection['Auteurs'].value_counts().max() <= 2
assert livres.loc[~livres['DansTop20'], 'RangSelection'].isna().all()

# Le modèle doit lire les mêmes colonnes que les CSV et trier chaque tranche sans ambiguïté.
modele = json.loads((racine / 'powerbi/Goodreads.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
fichiers = {'Livres': 'livres_powerbi.csv', 'Langues': 'langues.csv',
            'AuditImport': 'controle_qualite.csv', 'Sensibilite': 'sensibilite.csv',
            'ComparaisonSelections': 'comparaison_selections.csv'}
for table in modele['tables']:
    colonnes_csv = pd.read_csv(dossier / fichiers[table['name']], sep=';', nrows=0).columns.tolist()
    assert [c['sourceColumn'] for c in table['columns']] == colonnes_csv
for tranche, ordre in [('TranchePages', 'OrdrePages'), ('TrancheNotes', 'OrdreNotes'), ('PeriodePublication', 'OrdrePeriode')]:
    assert livres[ordre].notna().all()
    assert livres.groupby(tranche)[ordre].nunique().eq(1).all()

# Ces résultats vérifient les données attendues sous filtres, sans exécuter le moteur DAX.
for nom, masque in [('Catalogue', pd.Series(True, index=livres.index)),
                    ('Français', livres['Langue'].eq('Français')),
                    ('Zéro note', livres['NbNotes'].eq(0)),
                    ('Compteur absent', livres['NbNotes'].isna())]:
    groupe = livres.loc[masque]
    print(nom, ':', len(groupe), 'fiches ;', int(groupe['Candidat'].sum()), 'candidats ; note moyenne', round(groupe['Note'].mean(), 2))

for chemin in sorted((racine / 'notebooks').glob('*.ipynb')):
    notebook = nbformat.read(chemin, as_version=4)
    nbformat.validate(notebook)
    for cellule in notebook.cells:
        if cellule.cell_type == 'code':
            assert cellule.execution_count is not None, chemin.name
            assert not any(s.output_type == 'error' for s in cellule.outputs), chemin.name

print('Contrôles des exports, des clés, des KPI et de la sélection : OK.', flush=True)
