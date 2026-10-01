"""Contrôler les fichiers versionnés sans télécharger le catalogue complet."""
import ast
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

racine = Path(__file__).resolve().parents[1]
liste = subprocess.check_output(
    ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
    cwd=racine
).decode('utf-8').split('\0')
fichiers = sorted({racine / nom for nom in liste if nom and (racine / nom).is_file()})
erreurs = []
notebooks = 0

for chemin in fichiers:
    nom = chemin.relative_to(racine).as_posix()
    if chemin.stat().st_size >= 100 * 1024**2:
        erreurs.append(f'{nom} : fichier trop volumineux pour le dépôt')
    if nom.startswith(('data/raw/', 'data/processed/', 'archive_ancienne_version/')) and chemin.name != '.gitkeep':
        erreurs.append(f'{nom} : donnée locale à exclure de Git')
    if '/.pbi/' in nom or chemin.suffix in {'.pbix', '.pbit'}:
        erreurs.append(f'{nom} : cache ou binaire local à exclure de Git')
    if chemin.suffix not in {'.py', '.md', '.ipynb', '.json', '.bim', '.pbip', '.pbir', '.pbism'}:
        continue
    contenu = chemin.read_text(encoding='utf-8-sig')
    if '\ufffd' in contenu:
        erreurs.append(f'{nom} : caractère de remplacement dans le texte')
    if chemin.suffix == '.py':
        ast.parse(contenu, filename=nom)
    if chemin.suffix in {'.ipynb', '.json', '.bim', '.pbip', '.pbir', '.pbism'}:
        objet = json.loads(contenu)
    if chemin.suffix == '.ipynb':
        notebooks += 1
        if objet['nbformat'] != 4:
            erreurs.append(f'{nom} : format de notebook inattendu')
        for cellule in objet['cells']:
            if cellule['cell_type'] == 'code':
                ast.parse(''.join(cellule['source']), filename=nom)
                if cellule.get('execution_count') is None:
                    erreurs.append(f'{nom} : cellule de code non exécutée')
                if any(s.get('output_type') == 'error' for s in cellule.get('outputs', [])):
                    erreurs.append(f'{nom} : erreur enregistrée dans une sortie')
        contenu = '\n'.join(''.join(c['source']) for c in objet['cells'] if c['cell_type'] == 'markdown')
    if chemin.suffix in {'.md', '.ipynb'}:
        for cible in re.findall(r'\]\(([^)]+)\)', contenu):
            cible = unquote(cible.split('#')[0])
            if cible and not cible.startswith(('https:', 'http:', 'mailto:')):
                if not (chemin.parent / cible).exists():
                    erreurs.append(f'{nom} : lien local cassé vers {cible}')

if notebooks != 3:
    erreurs.append(f'Trois notebooks attendus, {notebooks} trouvés')

# Vérifier que les visuels utilisent des champs qui existent dans le modèle.
modele = json.loads((racine / 'powerbi/Goodreads.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
colonnes = {t['name']: {c['name'] for c in t['columns']} for t in modele['tables']}
mesures = {t['name']: {m['name'] for m in t.get('measures', [])} for t in modele['tables']}

def verifier_champs(objet, nom):
    if isinstance(objet, dict):
        for type_champ, inventaire in [('Column', colonnes), ('Measure', mesures)]:
            if type_champ in objet:
                champ = objet[type_champ]
                table = champ.get('Expression', {}).get('SourceRef', {}).get('Entity')
                if table and champ['Property'] not in inventaire.get(table, set()):
                    erreurs.append(f"{nom} : champ absent {table}.{champ['Property']}")
        for valeur in objet.values():
            verifier_champs(valeur, nom)
    elif isinstance(objet, list):
        for valeur in objet:
            verifier_champs(valeur, nom)

for chemin in (racine / 'powerbi/Goodreads.Report/definition').rglob('*.json'):
    verifier_champs(json.loads(chemin.read_text(encoding='utf-8')), chemin.name)

if erreurs:
    raise SystemExit('\n'.join(erreurs))
print(f'Livrables : OK ({len(fichiers)} fichiers, 3 notebooks, liens locaux et champs Power BI vérifiés).')
print('Ce contrôle ne réexécute pas les analyses et ne vérifie pas le rendu dans Power BI Desktop.')
