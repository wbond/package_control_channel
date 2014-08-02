#!/usr/bin/env python3

"""Tests for the validity of the channel and repository files.

You can run this script directly or with `python -m unittest` from this or the
root directory. For some reason `nosetests` does not pick up the generated tests
even though they are generated at load time.

Arguments:
    --test-repositories
        Also generates tests for all repositories in `channel.json` (the http
        ones).
"""

import os
import re
import json
import sys
import unittest

from collections import OrderedDict
from functools import wraps
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import urljoin

arglist = ['--test-repositories']
# Exctract used arguments form the commandline an strip them for unittest.main
userargs = [arg for arg in sys.argv if arg in arglist]
for arg in userargs:
    if arg in sys.argv:
        sys.argv.remove(arg)


################################################################################
# Utilities


def _open(filepath, *args, **kwargs):
    """Wrapper function that can search one dir above if the desired file
    does not exist.
    """
    if not os.path.exists(filepath):
        filepath = os.path.join("..", filepath)

    return open(filepath, *args, **kwargs)


def generator_class(cls):
    """Class decorator for classes that use test generating methods.

    A class that is decorated with this function will be searched for methods
    starting with "generate_" (similar to "test_") and then run like a nosetest
    generator.
    Note: The generator function must be a classmethod!

    Generate tests using the following statement:
        yield method, (arg1, arg2, arg3)  # ...
    """
    for name in list(cls.__dict__.keys()):
        generator = getattr(cls, name)
        if not name.startswith("generate_") or not callable(generator):
            continue

        if not generator.__class__.__name__ == 'method':
            raise TypeError("Generator methods must be classmethods")

        # Create new methods for each `yield`
        for sub_call in generator():
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

            mname = method.__name__
            if mname.startswith("_test"):
                mname = mname[1:]
            elif not mname.startswith("test_"):
                mname = "test_" + mname

            # Include parameters in attribute name
            name = "%s(%s)" % (mname, ", ".join(args))
            setattr(cls, name, wrapper)

        # Remove the generator afterwards, it did its work
        delattr(cls, name)

    return cls


def get_package_name(data):
    """Gets "name" from a package with a workaround when it's not defined.

    Use the last part of details url for the package's name otherwise since
    packages must define one of these two keys anyway.
    """
    return data.get('name') or data.get('details').rsplit('/', 1)[-1]


################################################################################
# Tests


class TestContainer(object):
    """Contains tests that the generators can easily access (when subclassing).

    Does not contain tests itself, must be used as mixin with unittest.TestCase.
    """

    package_key_types_map = {
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

    d_reg = r'''^ (https:// github\.com/ [^/]+/ [^/]+ (/tree/ .+ (?<!/)
                                                      |/tags
                                                      |/)?
                  |https:// bitbucket\.org/ [^/]+/ [^/]+ (/src/ .+ (?<!/)
                                                         |\#tags
                                                         |/)?
                  ) $'''
    # Strip multilines for better debug info on failures
    details_regex = re.compile(' '.join(d_reg.split()), re.X)

    def _test_repository_keys(self, include, data):
        self.assertTrue(2 <= len(data) <= 3, "Unexpected number of keys")
        self.assertIn('schema_version', data)
        self.assertEqual(data['schema_version'], '2.0')

        listkeys = [k for k in ('packages', 'includes') if k in data]
        self.assertGreater(len(listkeys), 0)
        for k in listkeys:
            self.assertIsInstance(data[k], list)

    def _test_repository_package_order(self, include, data):
        m = re.search(r"(?:^|/)(0-9|[a-z])\.json$", include)
        if not m:
            self.fail("Include filename does not match")

        # letter = include[-6]
        letter = m.group(1)
        packages = []
        for pdata in data['packages']:
            pname = get_package_name(pdata)
            if pname in packages:
                self.fail("Package names must be unique: " + pname)
            else:
                packages.append(pname)

            # TODO?: Test for *all* "previous_names"

        # Check if in the correct file
        for package_name in packages:
            if letter == '0-9':
                self.assertTrue(package_name[0].isdigit())
            else:
                self.assertEqual(package_name[0].lower(), letter,
                                 "Package inserted in wrong file")

        # Check package order
        self.assertEqual(packages, sorted(packages, key=str.lower),
                         "Packages must be sorted alphabetically (by name)")

    def _test_repository_indents(self, include, contents):
        for i, line in enumerate(contents.splitlines()):
            self.assertRegex(line, r"^\t*\S",
                             "Indent must be tabs in line %d" % (i + 1))

    def _test_package(self, include, data):
        for k, v in data.items():
            self.assertIn(k, self.package_key_types_map)
            self.assertIsInstance(v, self.package_key_types_map[k], k)

            if k in ('homepage', 'readme', 'issues', 'donate', 'buy'):
                self.assertRegex(v, '^https?://')

            if k == 'details':
                self.assertRegex(v, self.details_regex,
                                 'The details url is badly formatted or '
                                 'invalid')

            # Test for invalid characters (on file systems)
            if k == 'name':
                # Invalid on Windows (and sometimes problematic on UNIX)
                self.assertNotRegex(v, r'[/?<>\\:*|"\x00-\x19]')
                # Invalid on OS X (or more precisely: hidden)
                self.assertFalse(v.startswith('.'))

        if 'details' not in data:
            for key in ('name', 'homepage', 'author', 'releases'):
                self.assertIn(key, data, '%r is required if no "details" URL '
                                         'provided' % key)

    def _test_release(self, package_name, data, main_repo=True):
        # Fail early
        if main_repo:
            self.assertIn('details', data,
                          'A release must have a "details" key if it is in the '
                          'main repository. For custom releases, a custom '
                          'repository.json file must be hosted elsewhere.')
            for req in ('url', 'version', 'date'):
                self.assertNotIn(req, data,
                                 'The version, date and url keys should not be '
                                 'used in the main repository since a pull '
                                 'request would be necessary for every release')

        elif not 'details' in data:
            for req in ('url', 'version', 'date'):
                self.assertIn(req, data,
                              'A release must provide "url", "version" and '
                              '"date" keys if it does not specify "details"')

        else:
            for req in ('url', 'version', 'date'):
                self.assertNotIn(req, data,
                                 'The key "%s" is redundant when "details" is '
                                 'specified' % req)

        self.assertIn('sublime_text', data,
                      'A sublime text version selector is required')

        for k, v in data.items():
            self.assertIn(k, ('details', 'sublime_text', 'platforms',
                              'version', 'date', 'url'))

            if k == 'date':
                self.assertRegex(v, r"^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d$")

            if k == 'url':
                self.assertRegex(v, r'^https?://')

            if k == 'details':
                self.assertRegex(v, self.details_regex,
                                 'The details url is badly formatted or '
                                 'invalid')

            if k == 'sublime_text':
                self.assertRegex(v, '^(\*|<=?\d{4}|>=?\d{4})$',
                                 'sublime_text must be `*` or of the form '
                                 '<relation><version> '
                                 'where <relation> is one of {<, <=, >, >=} '
                                 'and <version> is a 4 digit number')

            if k == 'platforms':
                self.assertIsInstance(v, (str, list))
                if isinstance(v, str):
                    v = [v]
                for plat in v:
                    self.assertRegex(plat,
                                     r"^\*|(osx|linux|windows)(-x(32|64))?$")

    def _test_error(self, msg, e=None):
        if e:
            if isinstance(e, HTTPError):
                self.fail("%s: %s" % (msg, e))
            else:
                self.fail("%s: %r" % (msg, e))
        else:
            self.fail(msg)

    @classmethod
    def _fail(cls, *args):
        return cls._test_error, args


@generator_class
class ChannelTests(TestContainer, unittest.TestCase):
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
        self.assertEqual(repos, sorted(repos, key=str.lower),
                         "Repositories must be sorted alphabetically")

    @classmethod
    def generate_repository_tests(cls):
        if not "--test-repositories" in userargs:
            # Only generate tests for all repositories (those hosted online)
            # when run with "--test-repositories" parameter.
            return

        for repository in cls.j['repositories']:
            if repository.startswith('.'):
                continue
            if not repository.startswith("http"):
                cls._fail("Unexcpected repository url: %s" % repository)

            yield from cls._include_tests(repository)

    @classmethod
    def _include_tests(cls, url):
        print("fetching %s" % url)

        # Download the repository
        try:
            with urlopen(url) as f:
                source = f.read().decode("utf-8")
        except Exception as e:
            yield cls._fail("Downloading %s failed" % url, e)
            return

        if not source:
            yield cls._fail("%s is empty" % url)
            return

        # Parse the repository
        try:
            data = json.loads(source)
        except Exception as e:
            yield cls._fail("Could not parse %s" % url, e)
            return

        # Check for the schema version first (and generator failures it's
        # badly formatted)
        if 'schema_version' not in data:
            yield cls._fail("No schema_version found in %s" % url)
            return
        schema = float(data['schema_version'])
        if schema not in (1.0, 1.1, 1.2, 2.0):
            yield cls._fail("Unrecognized schema version %s in %s"
                            % (schema, url))
            return
        # Do not generate 1000 failing tests for not yet updated repos
        if schema != 2.0:
            print("schema version %s, skipping" % data['schema_version'])
            return

        # `url` is for output during tests only
        yield cls._test_repository_keys, (url, data)

        if 'packages' in data:
            for package in data['packages']:
                yield cls._test_package, (url, package)

                package_name = get_package_name(package)

                if 'releases' in package:
                    for release in package['releases']:
                        (yield cls._test_release,
                            ("%s (%s)" % (package_name, url),
                             release, False))
        if 'includes' in data:
            for include in data['includes']:
                i_url = urljoin(url, include)
                yield from cls._include_tests(i_url)


@generator_class
class RepositoryTests(TestContainer, unittest.TestCase):
    maxDiff = None

    with _open('repository.json') as f:
        j = json.load(f, object_pairs_hook=OrderedDict)

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
                    contents = f.read()
                data = json.loads(contents, object_pairs_hook=OrderedDict)
            except Exception as e:
                yield cls._test_error, ("Error while reading %r" % include, e)
                continue

            # `include` is for output during tests only
            yield cls._test_repository_indents, (include, contents)
            yield cls._test_repository_keys, (include, data)
            yield cls._test_repository_package_order, (include, data)

            for package in data['packages']:
                yield cls._test_package, (include, package)

                package_name = get_package_name(package)

                if 'releases' in package:
                    for release in package['releases']:
                        (yield cls._test_release,
                            ("%s (%s)" % (package_name, include), release))


################################################################################
# Main


if __name__ == '__main__':
    unittest.main()
