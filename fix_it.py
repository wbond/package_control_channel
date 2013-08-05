#!/usr/bin/env python3

"""Tests for the validity of the channel file

Run this file when tests are failing. Does not handle invalid JSON.
"""

import json
import re
import math
from collections import OrderedDict

repo_file = "repositories.json"


def reorder_repositories(j):
    repos = j['repositories']
    # Disregard "https://github.com/SublimeText" at the top because it is
    # purposely not in order
    first_elmt = repos.pop(0)
    j['repositories'] = [first_elmt] + sorted(repos, key=str.lower)


def reorder_package_names(j):
    map_package_names = list(j['package_name_map'].keys())
    j['package_name_map'] = OrderedDict([(k, j['package_name_map'][k])
                                         for k in sorted(map_package_names, key=str.lower)])


def reorder_renamed_packages(j):
    ren_package_names = list(j['renamed_packages'].keys())
    j['renamed_packages'] = OrderedDict([(k, j['renamed_packages'][k])
                                         for k in sorted(ren_package_names, key=str.lower)])


def remove_redundant_name_maps(j):
    for k, v in j['package_name_map'].items():
        if k == v:
            del j['package_name_map'][k]


def remove_redundant_rename_maps(j):
    for k, v in j['renamed_packages'].items():
        if k == v:
            del j['renamed_packages'][k]


def main():
    # Read from file
    with open(repo_file) as f:
        j = json.load(f, object_pairs_hook=OrderedDict)

    # Validate the data
    reorder_repositories(j)
    reorder_package_names(j)
    reorder_renamed_packages(j)
    remove_redundant_name_maps(j)
    remove_redundant_rename_maps(j)

    # Pretty print
    res = json.dumps(j, ensure_ascii=False, indent="\t", separators=(',', ': '))
    # Convert to tab indents
    # res = re.sub(r"(?m)^( {4,})", lambda r: "\t" * math.floor(len(r.group(1)) / 4), res)

    # Write to file
    with open(repo_file, 'w') as f:
        f.write(res)


if __name__ == '__main__':
    main()
