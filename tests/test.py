import json
import unittest
from collections import OrderedDict

# Only run these using `notetests` (or `python -m unittest`) from the root directory


# No need to check for this because all the other tests would fail anyway
# class TestValidity(unittest.TestCase):
#     def test_json_is_valid(self):
#         fp = open("repositories.json")
#         json.load(fp)


class TestOrder(unittest.TestCase):
    # Do not limit the list comparison to 600 chars (for more detailed debugging)
    maxDiff = None

    def setUp(self):
        self.j = json.load(open("repositories.json"), object_pairs_hook=OrderedDict)

    def test_repositories_in_order(self):
        repos = self.j['repositories']
        # Remove "https://github.com/SublimeText" at the top because it is purposely not in order
        del repos[0]
        self.assertEqual(repos, sorted(repos, key=str.lower))

    def test_package_names_in_order(self):
        map_packages = list(self.j['package_name_map'].keys())
        self.assertEqual(map_packages, sorted(map_packages, key=str.lower))

    def test_renamed_packages_in_order(self):
        ren_packages = list(self.j['renamed_packages'].keys())
        self.assertEqual(ren_packages, sorted(ren_packages, key=str.lower))
