"""Relier le modèle Power BI aux CSV du projet courant, sans chemin personnel fixé."""
import argparse
import csv
import json
import os
from pathlib import Path, PureWindowsPath
import tempfile

FICHIERS = {
    'Livres': 'livres_powerbi.csv',
    'Langues': 'langues.csv',
    'AuditImport': 'controle_qualite.csv',
    'Sensibilite': 'sensibilite.csv',
    'ComparaisonSelections': 'comparaison_selections.csv',
}


def chemin_powerbi(dossier):
    """Convertir aussi un chemin WSL /mnt/d/... vers son équivalent Windows."""
    dossier = Path(dossier).resolve()
    morceaux = dossier.parts
    if len(morceaux) >= 3 and morceaux[:2] == ('/', 'mnt') and len(morceaux[2]) == 1:
        return str(PureWindowsPath(morceaux[2].upper() + ':/', *morceaux[3:]))
    return str(dossier)


def configurer(racine=None):
    racine = Path(racine) if racine is not None else Path(__file__).resolve().parents[1]
    dossier = (racine / 'data/processed').resolve()
    fichier_modele = racine / 'powerbi/Goodreads.SemanticModel/model.bim'
    manquants = [nom for nom in FICHIERS.values() if not (dossier / nom).is_file()]
    if manquants:
        raise FileNotFoundError(
            'Exports manquants dans ' + str(dossier) + ' : ' + ', '.join(manquants)
            + '. Exécutez les trois notebooks avec python main.py.'
        )
    modele = json.loads(fichier_modele.read_text(encoding='utf-8-sig'))
    # Éviter de configurer un rapport à partir de fichiers vides ou incompatibles.
    for table in modele['model']['tables']:
        nom = FICHIERS[table['name']]
        with (dossier / nom).open(encoding='utf-8-sig', newline='') as fichier:
            lecteur = csv.reader(fichier, delimiter=';')
            entetes = next(lecteur, [])
            colonnes = [colonne['sourceColumn'] for colonne in table['columns']]
            if entetes != colonnes or next(lecteur, None) is None:
                raise ValueError('Export vide ou colonnes incompatibles : ' + nom)
    parametres = [p for p in modele['model']['expressions'] if p['name'] == 'DossierDonnees']
    if len(parametres) != 1:
        raise ValueError('Le modèle doit contenir un seul paramètre DossierDonnees.')
    chemin = chemin_powerbi(dossier)
    expression = '"' + chemin.replace('"', '""') + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    if parametres[0]['expression'] != expression:
        parametres[0]['expression'] = expression
        # Écriture atomique : ne pas laisser un modèle partiel en cas d'interruption.
        contenu = json.dumps(modele, ensure_ascii=False, indent=2) + '\n'
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=fichier_modele.parent, delete=False) as fichier:
            temporaire = Path(fichier.name)
            fichier.write(contenu)
        try:
            temporaire.replace(fichier_modele)
        finally:
            temporaire.unlink(missing_ok=True)
    return chemin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ouvrir', action='store_true', help='Ouvrir le PBIP après configuration, sous Windows')
    args = parser.parse_args()
    if args.ouvrir and os.name != 'nt':
        parser.error("L'ouverture de Power BI Desktop nécessite Windows.")
    try:
        chemin = configurer()
    except (OSError, ValueError, KeyError) as erreur:
        parser.exit(1, str(erreur) + '\n')
    print('Les cinq exports sont présents. DossierDonnees = ' + chemin, flush=True)
    if args.ouvrir:
        projet = Path(__file__).resolve().parents[1] / 'powerbi/Goodreads.pbip'
        os.startfile(str(projet))


if __name__ == '__main__':
    main()
