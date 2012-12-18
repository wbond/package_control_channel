import json

def test_json_is_valid():
	fp = open("repositories.json")
	json.load(fp)
