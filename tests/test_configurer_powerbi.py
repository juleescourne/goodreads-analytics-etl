import csv
import json
from pathlib import Path
import tempfile
import unittest
from scripts.configurer_powerbi import configurer, chemin_powerbi, FICHIERS


class ConfigurationPowerBITest(unittest.TestCase):
    def projet(self, racine):
        donnees = racine / 'data/processed'
        modele = racine / 'powerbi/Goodreads.SemanticModel/model.bim'
        donnees.mkdir(parents=True)
        modele.parent.mkdir(parents=True)
        contenu = {'model': {
            'expressions': [{'name': 'DossierDonnees', 'expression': '"ancien"'}],
            'tables': [{'name': nom, 'columns': [{'sourceColumn': 'Valeur'}]}
                       for nom in FICHIERS],
        }}
        modele.write_text(json.dumps(contenu), encoding='utf-8')
        for nom in FICHIERS.values():
            with (donnees / nom).open('w', encoding='utf-8-sig', newline='') as fichier:
                csv.writer(fichier, delimiter=';').writerows([['Valeur'], ['1']])
        return modele

    def test_utilise_le_projet_et_non_le_repertoire_du_terminal(self):
        with tempfile.TemporaryDirectory() as temporaire:
            racine = Path(temporaire) / 'projet avec espaces'
            modele = self.projet(racine)
            chemin = configurer(racine)
            self.assertEqual(chemin, chemin_powerbi(racine / 'data/processed'))
            self.assertIn(chemin, json.loads(modele.read_text())['model']['expressions'][0]['expression'])
            contenu = modele.read_bytes()
            configurer(racine)
            self.assertEqual(modele.read_bytes(), contenu)

    def test_reconfigure_apres_deplacement_du_projet(self):
        with tempfile.TemporaryDirectory() as temporaire:
            premier = Path(temporaire) / 'ancien'
            self.projet(premier)
            avant = configurer(premier)
            nouveau = premier.rename(Path(temporaire) / 'nouveau')
            apres = configurer(nouveau)
            self.assertNotEqual(avant, apres)
            expression = json.loads((nouveau / 'powerbi/Goodreads.SemanticModel/model.bim').read_text())['model']['expressions'][0]['expression']
            self.assertNotIn(avant, expression)
            self.assertIn(apres, expression)

    def test_csv_manquant_ne_modifie_pas_le_modele(self):
        with tempfile.TemporaryDirectory() as temporaire:
            racine = Path(temporaire)
            modele = self.projet(racine)
            avant = modele.read_bytes()
            (racine / 'data/processed/comparaison_selections.csv').unlink()
            with self.assertRaisesRegex(FileNotFoundError, 'comparaison_selections.csv'):
                configurer(racine)
            self.assertEqual(modele.read_bytes(), avant)

    def test_colonnes_incompatibles_ne_modifient_pas_le_modele(self):
        with tempfile.TemporaryDirectory() as temporaire:
            racine = Path(temporaire)
            modele = self.projet(racine)
            avant = modele.read_bytes()
            (racine / 'data/processed/langues.csv').write_text('MauvaiseColonne\n1\n')
            with self.assertRaisesRegex(ValueError, 'langues.csv'):
                configurer(racine)
            self.assertEqual(modele.read_bytes(), avant)

    @unittest.skipIf(__import__('os').name == 'nt', 'Conversion utile uniquement depuis WSL')
    def test_conversion_du_chemin_wsl(self):
        self.assertEqual(chemin_powerbi('/mnt/d/formation/projet/data/processed'),
                         'D:\\formation\\projet\\data\\processed')


if __name__ == '__main__':
    unittest.main()
