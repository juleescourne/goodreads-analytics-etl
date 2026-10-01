"""Télécharger les fichiers de livres Kaggle utilisés dans l'analyse."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import io
import json
import zipfile

racine = Path(__file__).resolve().parents[1]
manifest = json.loads((racine / 'data/sources.json').read_text(encoding='utf-8'))
dossier = racine / 'data/raw/kaggle_v18'
dossier.mkdir(parents=True, exist_ok=True)

for fichier in manifest['files']:
    chemin = dossier / fichier['name']
    if chemin.exists():
        contenu = chemin.read_bytes()
    else:
        print('Téléchargement :', fichier['name'], flush=True)
        requete = Request(fichier['url'], headers={'User-Agent': 'GoodreadsPortfolio/1.0'})
        with urlopen(requete, timeout=180) as reponse:
            contenu = reponse.read()
        # Selon la réponse Kaggle, le fichier peut être compressé seul dans un ZIP.
        if contenu[:2] == b'PK':
            with zipfile.ZipFile(io.BytesIO(contenu)) as archive:
                contenu = archive.read(fichier['name'])

    if hashlib.sha256(contenu).hexdigest() != fichier['sha256']:
        raise ValueError(f"Version inattendue pour {fichier['name']}. Aucun fichier existant n'a été remplacé.")
    if not chemin.exists():
        chemin.write_bytes(contenu)
    print(fichier['name'], ': empreinte vérifiée', flush=True)

print('Les 23 fichiers de livres sont prêts.', flush=True)
