import json
from collections import OrderedDict

def test_json_is_valid():
	fp = open("repositories.json")
	json.load(fp)

def test_repositories_in_order():
	j = json.load(open("repositories.json"))
	repos = j['repositories'][3:]
	assert repos == sorted(repos, key=unicode.lower)

def test_package_names_in_order():
	j = json.load(open("repositories.json"), object_pairs_hook=OrderedDict)
	packages = j['package_name_map'].keys()
	assert packages == sorted(packages, key=unicode.lower)

def test_renamed_packages_in_order():
	j = json.load(open("repositories.json"), object_pairs_hook=OrderedDict)
	packages = j['renamed_packages'].keys()
	assert packages == sorted(packages, key=unicode.lower)
