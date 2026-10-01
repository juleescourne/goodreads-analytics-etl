"""Exécuter les trois notebooks dans l'ordre et conserver leurs résultats."""
from pathlib import Path
import time

import nbformat
from nbclient import NotebookClient

racine = Path(__file__).resolve().parent
notebooks = [
    '01_data_quality.ipynb',
    '02_analyse_globale.ipynb',
    '03_analyse_approfondie.ipynb',
]

for nom in notebooks:
    debut = time.time()
    chemin = racine / 'notebooks' / nom
    notebook = nbformat.read(chemin, as_version=4)
    print(f'Exécution de {nom}...', flush=True)
    NotebookClient(
        notebook, timeout=600, kernel_name='python3',
        resources={'metadata': {'path': str(racine)}}
    ).execute()
    nbformat.validate(notebook)
    nbformat.write(notebook, chemin)
    print(f'{nom} : OK ({time.time() - debut:.0f} secondes)', flush=True)

print('Notebooks exécutés. Exports disponibles dans data/processed.', flush=True)
