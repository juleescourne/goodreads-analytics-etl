"""Contract between the reproducible demo data and the portfolio explorer."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_demo_data import build_catalogue


class DemoCatalogueTests(unittest.TestCase):
    def test_reproducible_published_payload(self):
        catalogue = build_catalogue()
        self.assertEqual(catalogue, build_catalogue())
        self.assertEqual(catalogue, json.loads((ROOT / 'demo/catalogue.json').read_text()))

    def test_quality_accounting(self):
        report = build_catalogue()['quality']
        self.assertEqual(report, dict(input=801, duplicates=1, invalidRating=1,
                                      invalidDate=1, unknownLanguage=1, missingPages=1,
                                      output=798))
        self.assertEqual(report['input'], report['output'] + report['duplicates']
                         + report['invalidRating'] + report['invalidDate'])

    def test_valid_grain_and_denominators(self):
        books = build_catalogue()['books']
        self.assertEqual(len(books), len({book['id'] for book in books}))
        self.assertTrue(all(0 <= book['rating'] <= 5 for book in books))
        self.assertTrue(all(0 <= book['reviews'] <= book['votes'] for book in books))
        self.assertTrue(any(book['votes'] == 0 for book in books))
        self.assertNotIn('en-US', {book['language'] for book in books})
