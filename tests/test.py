#!/usr/bin/env python3

"""Tests for the validity of the channel and repository files.

You can run this script directly or with `python -m unittest` from this or the
root directory. For some reason `nosetests` does not pick up the generated tests
even though they are generated at load time.
"""

import os
import json
import unittest
from collections import OrderedDict
from functools import wraps

################################################################################

def _open(filepath, *args, **kwargs):
    """Wrapper function that can search one dir above if the desired file
    does not exist.
    """
    if not os.path.exists(filepath):
        filepath = os.path.join("..", filepath)

    return open(filepath, *args, **kwargs)


def generator_class(cls):
    """Class decorator for class that use generating methods.

    A class that is decorated with this function will be searched for methods
    starting with "generate_" (similar to "test_") and then run like a nosetest
    generator.
    Note: The generator function must be a classmethod!

    Generate tests using the following statement:
        yield function, (arg1, arg2, arg3)  # ...
    """
    for name in list(cls.__dict__.keys()):
        if not name.startswith("generate_") or not callable(getattr(cls, name)):
            continue

        # Create new methods for each `yield`
        for sub_call in getattr(cls, name)():
            method, params = sub_call

            @wraps(method)
            def wrapper(self, method=method, params=params):
                return method(self, *params)

            # Do not attempt to print lists/dicts with printed lenght of 1000 or
            # more, they are not interesting for us (probably the whole file)
            args = []
            for v in params:
                string = repr(v)
                if len(string) > 1000:
                    args.append('...')
                else:
                    args.append(repr(v))
            name = "%s(%s)" % (method.__name__.replace("_test", "test"),
                               ", ".join(args))
            setattr(cls, name, wrapper)

        # Remove the generator afterwards, it did its work
        delattr(cls, name)

    # print(dir(cls))
    return cls


def get_package_name(data):
    """Gets "name" from a package with a workaround when it's not defined.

    Use the last part of details url for the package's name otherwise since
    packages must one of these two keys anyway.
    """
    return data.get('name', data.get('details', '').rsplit('/', 1)[-1])


################################################################################

class ChannelTests(unittest.TestCase):
    maxDiff = None

    with _open('channel.json') as f:
        j = json.load(f)

    def test_channel_keys(self):
        keys = sorted(self.j.keys())
        self.assertEqual(keys, ['repositories', 'schema_version'])

        self.assertEqual(self.j['schema_version'], '2.0')
        self.assertIsInstance(self.j['repositories'], list)

        for repo in self.j['repositories']:
            self.assertIsInstance(repo, str)

    def test_channel_repo_order(self):
        repos = self.j['repositories']
        self.assertEqual(repos, sorted(repos, key=str.lower))


@generator_class
class RepositoryTests(unittest.TestCase):
    maxDiff = None

    with _open('repository.json') as f:
        j = json.load(f, object_pairs_hook=OrderedDict)

    key_types_map = {
        'name': str,
        'details': str,
        'description': str,
        'releases': list,
        'homepage': str,
        'author': str,
        'readme': str,
        'issues': str,
        'donate': str,
        'buy': str,
        'previous_names': list,
        'labels': list
    }

    def test_repository_keys(self):
        keys = sorted(self.j.keys())
        self.assertEqual(keys, ['includes', 'packages', 'schema_version'])

        self.assertEqual(self.j['schema_version'], '2.0')
        self.assertEqual(self.j['packages'], [])
        self.assertIsInstance(self.j['includes'], list)

        for include in self.j['includes']:
            self.assertIsInstance(include, str)

    @classmethod
    def generate_include_tests(cls):
        for include in cls.j['includes']:
            try:
                with _open(include) as f:
                    data = json.load(f, object_pairs_hook=OrderedDict)
            except Exception as e:
                print("adding failure")
                yield cls._test_error, ("Error while reading %r" % include, e)
                # print("Error while reading %r: %s" % (include, e))
                continue

            # `include` is for output during tests only
            yield cls._test_include_keys, (include, data)
            yield cls._test_include_package_order, (include, data)

            for package in data['packages']:
                yield cls._test_package, (include, package)

                package_name = get_package_name(data)

                if 'releases' in package:
                    for release in package['releases']:
                        yield cls._test_release, (package_name, release)

    def _test_include_keys(self, include, data):
        keys = sorted(data.keys())
        self.assertEqual(keys, ['packages', 'schema_version'])
        self.assertEqual(data['schema_version'], '2.0')
        self.assertIsInstance(data['packages'], list)

    def _test_include_package_order(self, include, data):
        letter = include[-6]  # Hacky but better than regex

        packages = [get_package_name(pdata) for pdata in data['packages']]

        # Check if in the correct file
        for package_name in packages:
            if letter == '9':
                self.assertTrue(package_name[0].isdigit())
            else:
                self.assertEqual(package_name[0].lower(), letter,
                                 "Package inserted in wrong file")

        # Check actual order
        self.assertEqual(packages, sorted(packages, key=str.lower))

    def _test_package(self, include, data):
        for key in data.keys():
            self.assertIn(key, self.key_types_map)
            self.assertIsInstance(data[key], self.key_types_map[key])

            if key in ('details', 'homepage', 'readme', 'issues', 'donate',
                       'buy'):
                self.assertRegex(data[key], '^https?://')

        if 'details' not in data:
            for key in ('name', 'homepage', 'author', 'releases'):
                self.assertIn(key, data, '%r is required if no "details" URL '
                                          'provided' % key)

    def _test_release(self, package_name, data):
        # Fail early
        self.assertIn('details', data,
                      'A release must have a "details" key if it is in the '
                      'main repository. For custom releases, a custom '
                      'repository.json file must be hosted elsewhere.')

        for key in data.keys():
            # Display this message despite it being tested with the next test
            # anyway
            self.assertNotIn(key, ('version', 'date', 'url'),
                             'The version, date and url keys should not be '
                             'used in the main repository since a pull request '
                             'would be necessary for every release')

            self.assertIn(key, ('details', 'sublime_text', 'platforms'))

            if key == 'details':
                self.assertRegex(data[key], '^https?://')

            if key == 'sublime_text':
                self.assertRegex(data[key], '^(\*|<=?\d{4}|>=?\d{4})$')

            if key == 'platforms':
                self.assertIsInstance(data[key], (str, list))
                if isinstance(data[key], str):
                    self.assertIn(data[key], ('*', 'osx', 'linux', 'windows'))
                else:
                    for plat in data[key]:
                        self.assertIn(plat, ('*', 'osx', 'linux', 'windows'))

    def _test_error(self, msg, e):
        self.fail("%s: %r" % (msg, e))


################################################################################

if __name__ == '__main__':
    unittest.main()
