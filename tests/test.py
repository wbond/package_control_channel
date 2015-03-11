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

from functools import wraps

if sys.version_info >= (3,):
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from urllib.parse import urljoin
    generator_method_type = 'method'
    str_cls = str
else:
    from . import unittest_compat  # NOQA (monkeypatches the unittest module)
    from urlparse import urljoin
    from urllib2 import HTTPError, urlopen
    generator_method_type = 'instancemethod'
    str_cls = unicode  # NOQA (obviously undefined in Py3)


if hasattr(sys, 'argv'):
    arglist = ['--test-repositories']
    # Exctract used arguments form the commandline an strip them for
    # unittest.main
    userargs = [arg for arg in sys.argv if arg in arglist]
    for arg in userargs:
        if arg in sys.argv:
            sys.argv.remove(arg)
else:
    userargs = []


################################################################################
# Utilities


def _open(filepath, *args, **kwargs):
    """Wrapper function to search one dir above if a file does not exist."""
    if not os.path.exists(filepath):
        filepath = os.path.join("..", filepath)

    return open(filepath, 'rb', *args, **kwargs)


def generate_test_methods(cls, stream):
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

        if not generator.__class__.__name__ == generator_method_type:
            raise TypeError("Generator methods must be classmethods")

        # Create new methods for each `yield`
        for sub_call in generator(stream):
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
    """Get "name" from a package with a workaround when it's not defined.

    Use the last part of details url for the package's name otherwise since
    packages must define one of these two keys anyway.
    """
    return data.get('name') or data.get('details').strip("/").rsplit("/", 1)[-1]


################################################################################
# Tests


class TestContainer(object):

    """Contains tests that the generators can easily access (when subclassing).

    Does not contain tests itself, must be used as mixin with unittest.TestCase.
    """

    package_key_types_map = {
        'name': str_cls,
        'details': str_cls,
        'description': str_cls,
        'releases': list,
        'homepage': str_cls,
        'author': (str_cls, list),
        'readme': str_cls,
        'issues': str_cls,
        'donate': (str_cls, type(None)),
        'buy': str_cls,
        'previous_names': list,
        'labels': list
    }

    dependency_key_types_map = {
        'name': str_cls,
        'description': str_cls,
        'releases': list,
        'issues': str_cls,
        'load_order': str_cls,
        'author': str_cls
    }

    rel_b_reg = r'''^ (https:// github\.com/ [^/]+/ [^/]+
                      |https:// bitbucket\.org/ [^/]+/ [^/]+
                      ) $'''
    # Strip multilines for better debug info on failures
    rel_b_reg = ' '.join(map(str.strip, rel_b_reg.split()))
    release_base_regex = re.compile(rel_b_reg, re.X)

    pac_d_reg = r'''^ (https:// github\.com/ [^/]+/ [^/]+ (/tree/ .+ (?<!/)
                                                          |/)? (?<!\.git)
                      |https:// bitbucket\.org/ [^/]+/ [^/]+ (/src/ .+ (?<!/)
                                                             |\#tags
                                                             |/)?
                      ) $'''
    pac_d_reg = ' '.join(map(str.strip, pac_d_reg.split()))
    package_details_regex = re.compile(pac_d_reg, re.X)

    def _test_repository_keys(self, include, data):
        self.assertTrue(2 <= len(data) <= 4, "Unexpected number of keys")
        self.assertIn('schema_version', data)
        self.assertEqual(data['schema_version'], '3.0.0')

        listkeys = [k for k in ('packages', 'dependencies', 'includes')
                    if k in data]
        self.assertGreater(len(listkeys), 0)
        for k in listkeys:
            self.assertIsInstance(data[k], list)

    def _test_dependency_order(self, include, data):
        m = re.search(r"(?:^|/)(0-9|[a-z]|dependencies)\.json$", include)
        if not m:
            self.fail("Include filename does not match")

        dependencies = []
        for pdata in data['dependencies']:
            pname = get_package_name(pdata)
            if pname in dependencies:
                self.fail("Dependency names must be unique: " + pname)
            else:
                dependencies.append(pname)

        # Check package order
        self.assertEqual(dependencies, sorted(dependencies, key=str_cls.lower),
                         "Dependencies must be sorted alphabetically")

    def _test_repository_package_order(self, include, data):
        m = re.search(r"(?:^|/)(0-9|[a-z]|dependencies)\.json$", include)
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
                self.assertTrue(package_name[0].isdigit(),
                                "Package inserted in wrong file")
            else:
                self.assertEqual(package_name[0].lower(), letter,
                                 "Package inserted in wrong file")

        # Check package order
        self.assertEqual(packages, sorted(packages, key=str_cls.lower),
                         "Packages must be sorted alphabetically (by name)")

    def _test_repository_indents(self, include, contents):
        for i, line in enumerate(contents.splitlines()):
            self.assertRegex(line, r"^\t*\S",
                             "Indent must be tabs in line %d" % (i + 1))

    def _test_package(self, include, data):
        for k, v in data.items():
            self.assertIn(k, self.package_key_types_map)
            self.assertIsInstance(v, self.package_key_types_map[k], k)

            if k == 'donate' and v is None:
                # Allow "removing" the donate url that is added by "details"
                continue
            elif k in ('homepage', 'readme', 'issues', 'donate', 'buy'):
                self.assertRegex(v, '^https?://')

            elif k == 'details':
                self.assertRegex(v, self.package_details_regex,
                                 'The details url is badly formatted or '
                                 'invalid')

        # Test for invalid characters (on file systems)
        name = get_package_name(data)
        # Invalid on Windows (and sometimes problematic on UNIX)
        self.assertNotRegex(name, r'[/?<>\\:*|"\x00-\x19]',
                            'Package names must be valid folder names on all '
                            'operating systems')
        # Invalid on OS X (or more precisely: hidden)
        self.assertFalse(name.startswith('.'), 'Package names may not start '
                                               'with a dot')

        if 'details' not in data:
            for key in ('name', 'homepage', 'author', 'releases'):
                self.assertIn(key, data, '%r is required if no "details" URL '
                                         'provided' % key)

    def _test_dependency(self, include, data):
        for k, v in data.items():
            self.assertIn(k, self.dependency_key_types_map)
            self.assertIsInstance(v, self.dependency_key_types_map[k], k)

            if k == 'issues':
                self.assertRegex(v, '^https?://')

            # Test for invalid characters (on file systems)
            elif k == 'name':
                # Invalid on Windows (and sometimes problematic on UNIX)
                self.assertNotRegex(v, r'[/?<>\\:*|"\x00-\x19]')
                self.assertFalse(v.startswith('.'))

            elif k == 'load_order':
                self.assertRegex(v, '^\d\d$', '"load_order" must be a two '
                                              'digit string')

    def _test_release(self, package_name, data, main_repo=True):
        # Fail early
        if main_repo:
            self.assertTrue(('tags' in data or 'branch' in data),
                            'A release must have a "tags" key or "branch" key '
                            'if it is in the main repository. For custom '
                            'releases, a custom repository.json file must be '
                            'hosted elsewhere.')
            for req in ('url', 'version', 'date'):
                self.assertNotIn(req, data,
                                 'The version, date and url keys should not be '
                                 'used in the main repository since a pull '
                                 'request would be necessary for every release')

        elif 'tags' not in data and 'branch' not in data:
            self.assertTrue(all(k in data for k in ('url', 'version', 'date')),
                            'A release must provide "url", "version" and '
                            '"date" keys if it does not specify "tags" or'
                            '"branch"')

        else:
            for req in ('url', 'version', 'date'):
                self.assertNotIn(req, data,
                                 'The key "%s" is redundant when "tags" or '
                                 '"branch" is specified' % req)

        self.assertIn('sublime_text', data,
                      'A sublime text version selector is required')

        self.assertFalse(('tags' in data and 'branch' in data),
                         'A release must have a only one of the "tags" or '
                         '"branch" keys.')

        for k, v in data.items():
            self.assertIn(k, ('base', 'tags', 'branch', 'sublime_text',
                              'platforms', 'version', 'date', 'url'))

            if k == 'date':
                self.assertRegex(v, r"^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d$")

            if k == 'url':
                self.assertRegex(v, r'^https?://')

            if k == 'base':
                self.assertRegex(v, self.release_base_regex,
                                 'The base url is badly formatted or '
                                 'invalid')

            if k == 'tags':
                self.assertIn(type(v), (str_cls, bool))

            if k == 'branch':
                self.assertEqual(type(v), str_cls)

            if k == 'sublime_text':
                self.assertRegex(v, '^(\*|<=?\d{4}|>=?\d{4})$',
                                 'sublime_text must be `*` or of the form '
                                 '<relation><version> '
                                 'where <relation> is one of {<, <=, >, >=} '
                                 'and <version> is a 4 digit number')

            if k == 'platforms':
                self.assertIsInstance(v, (str_cls, list))
                if isinstance(v, str_cls):
                    v = [v]
                for plat in v:
                    self.assertRegex(plat,
                                     r"^\*|(osx|linux|windows)(-x(32|64))?$")

    def _test_dependency_release(self, package_name, data, main_repo=True):
        if main_repo:
            self.assertTrue(('tags' in data
                             or 'branch' in data
                             or ('sha256' in data and 'version' in data
                                 and 'url' in data
                                 and data['url'][0:7] == 'http://')),
                            'A release must have a "tags" key or "branch" key '
                            'if it is in the main repository. For custom '
                            'releases, a custom repository.json file must be '
                            'hosted elsewhere. The only exception to this rule '
                            'is for packages that can not be served over HTTPS '
                            'since they help bootstrap proper secure HTTP '
                            'support for Sublime Text.')
            if 'sha256' not in data:
                for req in ('url', 'version'):
                    self.assertNotIn(req, data,
                                     'The version and url keys should not be '
                                     'used in the main repository since a pull '
                                     'request would be necessary for every '
                                     'release.')

        elif 'tags' not in data and 'branch' not in data:
            for req in ('url', 'version'):
                self.assertIn(req, data,
                              'A release must provide "url" and "version" '
                              'keys if it does not specify "tags" or "branch"')

        else:
            if 'tags' in data and 'branch' in data:
                self.fail('Only one of the keys "tags" and "branch" should '
                          'be used')

            for req in ('url', 'version'):
                self.assertNotIn(req, data,
                                 'The key "%s" is redundant when "tags" or '
                                 '"branch" is specified' % req)

        self.assertIn('sublime_text', data,
                      'A sublime text version selector is required')

        for k, v in data.items():
            self.assertIn(k, ('base', 'tags', 'branch', 'sublime_text',
                              'platforms', 'version', 'url', 'sha256'))

            if k == 'url' and 'sha256' not in data:
                self.assertRegex(v, r'^https://')
            elif k == 'url':
                self.assertRegex(v, r'^http://')

            if k == 'base':
                self.assertRegex(v, self.release_base_regex,
                                 'The base url is badly formatted or '
                                 'invalid')

            if k == 'tags':
                self.assertIn(type(v), (str_cls, bool))

            if k == 'branch':
                self.assertEqual(type(v), str_cls)

            if k == 'sha256':
                self.assertEqual(type(v), str_cls)

            if k == 'sublime_text':
                self.assertRegex(v, '^(\*|<=?\d{4}|>=?\d{4})$',
                                 'sublime_text must be `*` or of the form '
                                 '<relation><version> '
                                 'where <relation> is one of {<, <=, >, >=} '
                                 'and <version> is a 4 digit number')

            if k == 'platforms':
                self.assertIsInstance(v, (str_cls, list))
                if isinstance(v, str_cls):
                    v = [v]
                for plat in v:
                    self.assertRegex(plat,
                                     r"^\*|(osx|linux|windows)(-x(32|64))?$")

    def _test_error(self, msg, e=None):
        """
        A generic error-returning function used by the meta-programming features
        of this class.

        :param msg:
            The error message to return

        :param e:
            An optional exception to include with the error message
        """

        if e:
            if isinstance(e, HTTPError):
                self.fail("%s: %s" % (msg, e))
            else:
                self.fail("%s: %r" % (msg, e))
        else:
            self.fail(msg)

    @classmethod
    def _include_tests(cls, path, stream):
        """
        Return a tuple of (method, args) to add to a unittest TestCase class.
        A meta-programming function to expand the definition of class at run
        time, based on the contents of a file or URL.

        :param cls:
            The class to add the methods to

        :param path:
            The URL or file path to fetch the repository info from

        :param stream:
            A file-like object used for diagnostic output that provides .write()
            and .flush()
        """
        # TODO multi-threading
        stream.write("%s ... " % path)
        stream.flush()

        success = False
        try:
            if re.match('https?://', path, re.I) is not None:
                # Download the repository
                try:
                    with urlopen(path) as f:
                        source = f.read().decode("utf-8", 'replace')
                except Exception as e:
                    yield cls._fail("Downloading %s failed" % path, e)
                    return
            else:
                try:
                    with _open(path) as f:
                        source = f.read().decode('utf-8', 'replace')
                except Exception as e:
                    yield cls._fail("Opening %s failed" % path, e)
                    return

            if not source:
                yield cls._fail("%s is empty" % path)
                return

            # Parse the repository
            try:
                data = json.loads(source)
            except Exception as e:
                yield cls._fail("Could not parse %s" % path, e)
                return

            # Check for the schema version first (and generator failures it's
            # badly formatted)
            if 'schema_version' not in data:
                yield cls._fail("No schema_version found in %s" % path)
                return
            schema = data['schema_version']
            if schema != '3.0.0' and float(schema) not in (1.0, 1.1, 1.2, 2.0):
                yield cls._fail("Unrecognized schema version %s in %s"
                                % (schema, path))
                return

            success = True

            # Do not generate 1000 failing tests for not yet updated repos
            if schema != '3.0.0':
                stream.write("skipping (schema version %s)"
                             % data['schema_version'])
                return
            else:
                stream.write("done")
        finally:
            if not success:
                stream.write("failed")
            stream.write("\n")

        # `path` is for output during tests only
        yield cls._test_repository_keys, (path, data)

        if 'packages' in data:
            for package in data['packages']:
                yield cls._test_package, (path, package)

                package_name = get_package_name(package)

                if 'releases' in package:
                    for release in package['releases']:
                        (yield cls._test_release,
                            ("%s (%s)" % (package_name, path),
                             release, False))
        if 'includes' in data:
            for include in data['includes']:
                i_url = urljoin(path, include)
                for test in cls._include_tests(i_url, stream):
                    yield test

    @classmethod
    def _fail(cls, *args):
        """
        Generates a (method, args) tuple that returns an error when called.
        Allows for defering an error until the tests are actually run.
        """

        return cls._test_error, args

    @classmethod
    def _write(cls, stream, string):
        """
        Writes dianostic output to a file-like object.

        :param stream:
            Must have the methods .write() and .flush()

        :param string:
            The string to write - a newline will NOT be appended
        """

        stream.write(string)
        stream.flush()


class DefaultChannelTests(TestContainer, unittest.TestCase):
    maxDiff = None

    with _open('channel.json') as f:
        source = f.read().decode('utf-8', 'replace')
        j = json.loads(source)

    def test_channel_keys(self):
        keys = sorted(self.j.keys())
        self.assertEqual(keys, ['repositories', 'schema_version'])

        self.assertEqual(self.j['schema_version'], '3.0.0')
        self.assertIsInstance(self.j['repositories'], list)

        for repo in self.j['repositories']:
            self.assertIsInstance(repo, str_cls)

    def test_channel_repo_order(self):
        repos = self.j['repositories']
        self.assertEqual(repos, sorted(repos, key=str_cls.lower),
                         "Repositories must be sorted alphabetically")

    @classmethod
    def generate_repository_tests(cls, stream):
        if "--test-repositories" not in userargs:
            # Only generate tests for all repositories (those hosted online)
            # when run with "--test-repositories" parameter.
            return

        stream.write("Fetching remote repositories:\n")

        for repository in cls.j['repositories']:
            if repository.startswith('.'):
                continue
            if not repository.startswith("http"):
                cls._fail("Unexpected repository url: %s" % repository)

            for test in cls._include_tests(repository, stream):
                yield test

        stream.write('\n')
        stream.flush()


class DefaultRepositoryTests(TestContainer, unittest.TestCase):
    maxDiff = None

    with _open('repository.json') as f:
        source = f.read().decode('utf-8', 'replace')
        j = json.loads(source)

    def test_repository_keys(self):
        keys = sorted(self.j.keys())
        self.assertEqual(keys, ['dependencies', 'includes', 'packages',
                                'schema_version'])

        self.assertEqual(self.j['schema_version'], '3.0.0')
        self.assertEqual(self.j['packages'], [])
        self.assertEqual(self.j['dependencies'], [])
        self.assertIsInstance(self.j['includes'], list)

        for include in self.j['includes']:
            self.assertIsInstance(include, str_cls)

    @classmethod
    def generate_include_tests(cls, stream):
        for include in cls.j['includes']:
            try:
                with _open(include) as f:
                    contents = f.read().decode('utf-8', 'replace')
                data = json.loads(contents)
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

            if 'dependencies' in data:
                yield cls._test_dependency_order, (include, data)

                for dependency in data['dependencies']:
                    yield cls._test_dependency, (include, dependency)

                    dependency_name = get_package_name(dependency)

                    if 'releases' in dependency:
                        for release in dependency['releases']:
                            (yield cls._test_dependency_release,
                                ("%s (%s)" % (dependency_name, include),
                                 release))


def generate_default_test_methods(stream=None):
    if not stream:
        stream = sys.stdout
    generate_test_methods(DefaultRepositoryTests, stream)
    generate_test_methods(DefaultChannelTests, stream)


################################################################################
# Main


# When included to a Sublime package, sys.argv will not be set. We need to
# generate the test methods differently in that context, so we only generate
# them if sys.argv exists.
if hasattr(sys, 'argv'):
    generate_default_test_methods()

if __name__ == '__main__':
    unittest.main()
