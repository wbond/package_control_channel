#!/usr/bin/env python3

"""Tests for the validity of the channel file

You can run this file directly or with `notetests` (or `python -m unittest`)
from the root directory.
"""

import os
import json
import unittest
from collections import OrderedDict
from nose.tools import assert_equal, assert_in, assert_not_in, assert_regexp_matches

# Generator tests can't be part of a class, so for consistency
# they are all functions

def test_channel():
    with open("channel.json") as fp:
        data = json.load(fp)
    keys = sorted(data.keys())
    assert_equal(keys, ['repositories', 'schema_version'])

    assert_equal(data['schema_version'], '2.0')
    assert_equal(type(data['repositories']), list)

    for repository in data['repositories']:
        assert_equal(type(repository), str)


def test_repository():
    with open('repository.json') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    keys = sorted(data.keys())
    assert_equal(keys, ['includes', 'packages', 'schema_version'])

    assert_equal(data['schema_version'], '2.0')
    assert_equal(data['packages'], [])
    assert_equal(type(data['includes']), list)

    for include in data['includes']:
        assert_equal(type(include), str)


def test_repository_includes():
    with open('repository.json') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    for include in data['includes']:
        yield check_include, include

        with open(include) as f:
            include_data = json.load(f, object_pairs_hook=OrderedDict)
        for package in include_data['packages']:
            yield check_package, package
            if 'releases' in package:
                for release in package['releases']:
                    yield check_release, package, release


def check_include(filename):
    with open(filename) as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    keys = sorted(data.keys())
    assert_equal(keys, ['packages', 'schema_version'])
    assert_equal(data['schema_version'], '2.0')
    assert_equal(type(data['packages']), list)


def check_package(data):
    for key in data.keys():
        assert_in(key, ['name', 'details', 'releases', 'homepage', 'author',
            'readme', 'issues', 'donate', 'buy', 'previous_names', 'labels'])
        assert_equal(type(data[key]), map_key_type(key))
        if key in ['details', 'homepage', 'readme', 'issues', 'donate', 'buy']:
            assert_regexp_matches(data[key], '^https?://')

    if 'details' not in data:
        assert_in('name', data, 'The key "name" is required if no "details" URL provided')
        assert_in('homepage', data, 'The key "homepage" is required if no "details" URL provided')
        assert_in('author', data, 'The key "author" is required if no "details" URL provided')
        assert_in('releases', data, 'The key "releases" is required if no "details" URL provided')


def check_release(package, data):
    for key in data.keys():
        assert_not_in(key, ['version', 'date', 'url'], 'The version, date and ' + \
            'url keys should not be used in the main repository since a pull ' + \
            'request would be necessary for every release')

        assert_in(key, ['details', 'sublime_text', 'platforms'])

        if key in ['details', 'url']:
            assert_regexp_matches(data[key], '^https?://')

        if key == 'sublime_text':
            assert_regexp_matches(data[key], '^(\*|<=?\d{4}|>=?\d{4})$')

        if key == 'platforms':
            assert_in(type(data[key]), [str, list])
            if type(data[key]) == str:
                assert_in(data[key], ['*', 'osx', 'linux', 'windows'])
            else:
                for platform in data[key]:
                    assert_in(platform, ['*', 'osx', 'linux', 'windows'])

    assert_in('details', data, 'A release must have a "details" key if it is in ' + \
        'the main repository. For custom releases, a custom repository.json ' + \
        'file must be hosted elsewhere.')


def map_key_type(key):
    return {
        'name': str,
        'details': str,
        'releases': list,
        'homepage': str,
        'author': str,
        'readme': str,
        'issues': str,
        'donate': str,
        'buy': str,
        'previous_names': list,
        'labels': list
    }.get(key)


if __name__ == '__main__':
    # Manually go up one directory if this file is run explicitly
    if not os.path.exists(repo_file):
        repo_file = os.path.join("..", repo_file)

    unittest.main()
