import unittest
import pandas as pd
from scripts.regles_catalogue import lire_compteur, isoler_versions, normaliser_langues, selectionner


def catalogue():
    return pd.DataFrame([
        {'IdLivre': i, 'Titre': f'Titre {i}', 'Auteurs': auteur, 'Note': note,
         'NbNotes': notes, 'Langue': 'Français', 'AuteurAbsent': False,
         'EditeurAbsent': False, 'Pages': 200}
        for i, auteur, note, notes in [
            (1, 'A', 4.8, 150), (2, 'A', 4.7, 600), (3, 'A', 4.6, 800),
            (4, 'B', 4.5, 200), (5, 'C', 4.4, 1200), (6, 'D', 4.3, 500)]])


class NettoyageTest(unittest.TestCase):
    def test_compteur_invalide_ne_devient_pas_zero(self):
        resultat = lire_compteur(pd.Series(['total:0', 'total:12', 'total:-2', None, '5:12']), 'total')
        self.assertEqual(resultat.iloc[:2].tolist(), [0, 12])
        self.assertTrue(resultat.iloc[2:].isna().all())

    def test_toutes_les_versions_contradictoires_sont_isolees(self):
        table = pd.DataFrame({'Id': [1, 1, 2, 2, 3], 'Name': ['A', 'A', 'B', 'C', 'D']})
        retenues, quarantaine, repetitions = isoler_versions(table, ['Id', 'Name'])
        self.assertEqual(repetitions, 1)
        self.assertEqual(retenues['Id'].tolist(), [1, 3])
        self.assertEqual(quarantaine['Id'].tolist(), [2, 2])
        self.assertEqual(len(table), repetitions + len(retenues) + len(quarantaine))

    def test_identifiant_et_titre_invalides(self):
        table = pd.DataFrame({'Id': [None, -1, 1.5, 4, 5], 'Name': ['A', 'B', 'C', ' ', 'E']})
        retenues, quarantaine, _ = isoler_versions(table, ['Id', 'Name'])
        self.assertEqual(retenues['Id'].tolist(), [5])
        self.assertEqual(len(quarantaine), 4)

    def test_langue_absente_et_variantes(self):
        resultat = normaliser_langues(pd.Series([' FR ', 'fra', 'en-US', None, ' ', 'jpn']))
        self.assertEqual(resultat.tolist(), ['fre', 'fre', 'eng', 'non_renseigne', 'non_renseigne', 'jpn'])


class SelectionTest(unittest.TestCase):
    def test_plafond_remplace_les_titres_sans_reduire_la_liste(self):
        source = catalogue()
        original = source.copy(deep=True)
        _, _, liste = selectionner(source, maximum_par_auteur=2, taille=4)
        self.assertEqual(liste['IdLivre'].tolist(), [1, 2, 4, 5])
        self.assertEqual(liste['RangSelection'].tolist(), [1, 2, 3, 4])
        pd.testing.assert_frame_equal(source, original)

    def test_seuil_recalcule_la_liste_et_ses_remplacants(self):
        _, _, liste = selectionner(catalogue(), minimum_notes=500, taille=4)
        self.assertEqual(liste['IdLivre'].tolist(), [2, 3, 5, 6])

    def test_egalite_de_note_et_volume_departagee_par_id(self):
        source = catalogue().iloc[:2].copy()
        source['Note'], source['NbNotes'] = 4.5, 100
        _, _, liste = selectionner(source.iloc[::-1])
        self.assertEqual(liste['IdLivre'].tolist(), [1, 2])

    def test_edition_representante_plus_notee_sans_sommer_les_compteurs(self):
        source = catalogue().iloc[:2].copy()
        source['Titre'] = ['Le livre!', 'le livre']
        _, representants, liste = selectionner(source)
        self.assertEqual(len(representants), 1)
        self.assertEqual(liste['IdLivre'].tolist(), [2])
        self.assertEqual(liste['NbNotes'].tolist(), [600])

    def test_plafond_normalise_le_libelle_auteur(self):
        source = catalogue()
        source.loc[:2, 'Auteurs'] = [' A ', 'a', 'A']
        _, _, liste = selectionner(source, maximum_par_auteur=2)
        self.assertEqual(liste['IdLivre'].tolist(), [1, 2, 4, 5, 6])

    def test_metadonnees_et_langue_excluent_sans_relacher_les_criteres(self):
        source = catalogue()
        source.loc[0, 'Langue'] = 'Non renseignée'
        source.loc[1, 'AuteurAbsent'] = True
        source.loc[2, 'EditeurAbsent'] = True
        source.loc[3, 'Pages'] = 0
        source.loc[4, 'Pages'] = 5001
        source.loc[5, 'Note'] = float('nan')
        candidats, _, liste = selectionner(source)
        self.assertTrue(candidats.empty)
        self.assertTrue(liste.empty)


if __name__ == '__main__':
    unittest.main()
