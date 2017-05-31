# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import imp
import re
import os
import sys
import subprocess
import unittest
import tempfile
import shutil
import zipfile
import pip
import json
import pathlib
import traceback


pip_version = tuple(int(p) for p in pip.__version__.split('.'))
if pip_version < (8,):
    print('pip must be version 8.0 or newer', file=sys.stderr)
    exit(1)

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print('Installing deps')
pip.main(['install', '-q', '--user', '--upgrade', 'st-package-reviewer'])
pip.main(['install', '-q', '--user', '--upgrade', 'requests'])
print()


import st_package_reviewer.runner
import st_package_reviewer.check.file
import requests


def run(command, cwd=None):
    if cwd is None:
        cwd = repo_dir
    if not isinstance(command, list):
        raise TypeError('command must be a list')
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    stdout, stderr = proc.communicate()
    stdout = stdout.decode('utf-8').strip()
    stderr = stderr.decode('utf-8').strip()
    returncode = proc.wait()
    if returncode != 0:
        raise OSError((stdout + '\n' + stderr).strip())
    return stdout


print('Running channel tests')
test_mod_info = imp.find_module('test', [os.path.dirname(os.path.abspath(__file__))])
test_mod = imp.load_module('package_control_channel.tests.test', *test_mod_info)
test_mod.generate_default_test_methods()
suite = unittest.TestLoader().loadTestsFromModule(test_mod)
channel_results = unittest.TextTestRunner(stream=sys.stdout, verbosity=0).run(suite)
if not channel_results.wasSuccessful():
    exit(2)

print()

filenames = []

files_changed = run(['git', 'diff', '--name-status', 'HEAD~1'])
for line in files_changed.splitlines():
    parts = re.split(r'\s+', line, 1)
    if len(parts) != 2:
        raise ValueError('git diff-tree output included a line without status and filename\n\n%s' % files_changed)
    status, filename = parts
    if not filename.endswith('.json'):
        print('Skipping %s since it is not a json file')
        continue
    if not re.match(r'repository/(\w|0-9)\.json$', filename) and filename != 'channel.json':
        print('Skipping %s since is not a json file that specifies packages or repositories')
    if status != 'M':
        raise ValueError('Unsure how to test a change that adds or removes a file, aborting')
    filenames.append(filename)

def package_name(data):
    if 'name' in data:
        return data['name']
    else:
        return os.path.basename(data['details'])


modified_pkgs = set()
added_pkgs = set()
removed_pkgs = set()

added_pkg_data = {}

added_repositories = set()
removed_repositories = set()

for filename in filenames:
    old_version = run(['git', 'show', 'HEAD~1:%s' % filename])
    new_version = run(['git', 'show', 'HEAD:%s' % filename])
    old_json = json.loads(old_version)
    new_json = json.loads(new_version)
    if filename == 'channel.json':
        removed_repositories = set(old_json['repositories']) - set(new_json['repositories'])
        added_repositories = set(new_json['repositories']) - set(old_json['repositories'])

    else:
        old_packages = [json.dumps(p) for p in old_json['packages']]
        new_packages = [json.dumps(p) for p in new_json['packages']]
        deleted = set(old_packages) - set(new_packages)
        added = set(new_packages) - set(old_packages)
        deleted_indexes = [old_packages.index(op) for op in deleted]
        added_indexes = [new_packages.index(np) for np in added]
        if len(deleted_indexes) == len(added_indexes):
            for index in added_indexes:
                modified_pkgs.add(package_name(new_json['packages'][index]))
        elif len(deleted_indexes) == 0:
            for index in added_indexes:
                pkg_name = package_name(new_json['packages'][index])
                added_pkgs.add(pkg_name)
                added_pkg_data[pkg_name] = new_json['packages'][index]
        else:
            for index in deleted_indexes:
                removed_pkgs.add(package_name(old_json['packages'][index]))

if removed_repositories:
    print('Repositories removed:')
    for url in sorted(removed_repositories):
        print('  - %s' % url)

if added_repositories:
    print('Repositories added:')
    for url in sorted(added_repositories):
        print('  - %s' % url)

if added_repositories:
    for repo in added_repositories:
        print()
        if not repo.startswith('http://') and not repo.startswith('https://'):
            print('Skipping repository since it is local: %s' % repo)
            continue
        print('Fetching repository: %s' % repo)
        raw_data = requests.get(repo).content
        try:
            raw_data = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            errors = True
            print('  ERROR: Error decoding JSON as UTF-8')
            continue
        try:
            repo_json = json.loads(raw_data)
        except ValueError:
            errors = True
            print('  ERROR: Error parsing JSON')
            continue

        missing_key = False
        for key in ['schema_version', 'packages']:
            if key not in repo_json:
                missing_key = True
                errors = True
                print('  ERROR: Top-level key "%s" is missing' % key)
                continue
        if missing_key:
            continue

        if repo_json['schema_version'] != '3.0.0':
            errors = True
            print('  ERROR: "schema_version" must be 3.0.0')
            continue

        num_pkgs = 0
        for pkg_info in repo_json['packages']:
            pkg_name = package_name(pkg_info)
            added_pkgs.add(pkg_name)
            added_pkg_data[pkg_name] = pkg_info
            num_pkgs += 1
        print('  Found %d package%s' % (num_pkgs, 's' if num_pkgs != 1 else ''))
    print()

if removed_pkgs:
    print('Packages removed:')
    for name in sorted(removed_pkgs):
        print('  - %s' % name)

if modified_pkgs:
    print('Packages modified:')
    for name in sorted(modified_pkgs):
        print('  - %s' % name)

if added_pkgs:
    print('Packages added:')
    for name in sorted(added_pkgs):
        print('  - %s' % name)

if not added_pkgs:
    exit(0)


def st_build_match(version_range, ver):
    min_version = float("-inf")
    max_version = float("inf")

    if version_range == '*':
        return True

    gt_match = re.match('>(\d+)$', version_range)
    ge_match = re.match('>=(\d+)$', version_range)
    lt_match = re.match('<(\d+)$', version_range)
    le_match = re.match('<=(\d+)$', version_range)
    range_match = re.match('(\d+) - (\d+)$', version_range)

    if gt_match:
        min_version = int(gt_match.group(1)) + 1
    elif ge_match:
        min_version = int(ge_match.group(1))
    elif lt_match:
        max_version = int(lt_match.group(1)) - 1
    elif le_match:
        max_version = int(le_match.group(1))
    elif range_match:
        min_version = int(range_match.group(1))
        max_version = int(range_match.group(2))
    else:
        return None

    if min_version > ver:
        return False
    if max_version < ver:
        return False

    return True


try:

    mod_path = None
    tmpdir = tempfile.mkdtemp()
    if not tmpdir:
        print('Could not create tempdir', file=sys.stderr)
        exit(3)

    errors = False
    warnings = False
    for name in sorted(added_pkgs):
        print()
        print('Fetching package info for: %s' % name)
        data = added_pkg_data[name]
        if 'details' in data:

            headers = {
                'user-agent': 'Package Control Channel CI Script',
                'content-type': 'application/json',
            }
            response = requests.post(
                'https://packagecontrol.io/fetch.json',
                headers=headers,
                json=data
            )
            response_json = response.json()
            if response_json.get('result') != 'success':
                print('  ERROR: %s' % response_json.get('message', 'Unknown error'))
                continue

            info = response_json['info']

            if not info['releases']:
                errors = True
                print('  ERROR: No releases found, check to ensure you have created a valid semver tag')
                print('    https://packagecontrol.io/docs/submitting_a_package#Step_4')
            else:
                for release_source in data['releases']:
                    if 'branch' in release_source:
                        errors = True
                        print('  ERROR: Branch-based releases are not supported for new packages, please use "tags": true')
                        print('    https://packagecontrol.io/docs/submitting_a_package#Step_4')
            if info['readme'] is None:
                warnings = True
                print('  WARNING: Please create a readme for your package')

            if not info['releases']:
                continue

            url = info['releases'][0]['url']

            tmp_package_path = os.path.join(tmpdir, '%s.sublime-package' % name)
            tmp_package_dir = os.path.join(tmpdir, name)
            os.mkdir(tmp_package_dir)
            with open(tmp_package_path, 'wb') as package_file:
                package_file.write(requests.get(url).content)

            with zipfile.ZipFile(tmp_package_path, 'r') as package_zip:

                # Scan through the root level of the zip file to gather some info
                root_level_paths = []
                last_path = None
                for path in package_zip.namelist():
                    if not isinstance(path, str):
                        path = path.decode('utf-8', 'strict')

                    last_path = path

                    if path.find('/') in [len(path) - 1, -1]:
                        root_level_paths.append(path)

                if last_path and len(root_level_paths) == 0:
                    root_level_paths.append(last_path[0:last_path.find('/') + 1])

                # If there is only a single directory at the top leve, the file
                # is most likely a zip from BitBucket or GitHub and we need
                # to skip the top-level dir when extracting
                skip_root_dir = len(root_level_paths) == 1 and \
                    root_level_paths[0].endswith('/')

                for path in package_zip.namelist():
                    dest = path
                    if not isinstance(dest, str):
                        dest = dest.decode('utf-8', 'strict')

                    # If there was only a single directory in the package, we remove
                    # that folder name from the paths as we extract entries
                    if skip_root_dir:
                        dest = dest[len(root_level_paths[0]):]

                    dest = dest.replace('\\', '/')
                    dest = os.path.join(tmp_package_dir, dest)

                    if path.endswith('/'):
                        if not os.path.exists(dest):
                            os.makedirs(dest)
                    else:
                        dest_dir = os.path.dirname(dest)
                        if not os.path.exists(dest_dir):
                            os.makedirs(dest_dir)
                        with open(dest, 'wb') as f:
                            f.write(package_zip.read(path))

                print('  Running st_package_reviewer')
                runner = st_package_reviewer.runner.CheckRunner(st_package_reviewer.check.file.get_checkers())
                runner.run(pathlib.Path(tmp_package_dir))

                if runner.failures:
                    print("    {} failures:".format(len(runner.failures)))
                else:
                    print("    No failures")
                for failure in runner.failures:
                    print("     - {}".format(failure.message))
                    for elem in failure.details:
                        print("       {}".format(elem))
                    if failure.exc_info:
                        traceback.print_exception(*failure.exc_info)

                filtered_warnings = []
                for warning in runner.warnings:
                    if 'added in build 3092' in warning.message:
                        st_selector = info['releases'][0]['sublime_text']
                        if st_build_match(st_selector, 3091) or st_build_match(st_selector, 2221):
                            filtered_warnings.append(warning)
                    else:
                        filtered_warnings.append(warning)

                if filtered_warnings:
                    print("    {} warnings:".format(len(filtered_warnings)))
                else:
                    print("    No warnings")

                for warning in filtered_warnings:
                    print("     - {}".format(warning.message))
                    for elem in warning.details:
                        print("       {}".format(elem))
                    if warning.exc_info:
                        traceback.print_exception(*warning.exc_info)

        else:
            print('Non-VCS package found in primary channel', file=sys.stderr)
            exit(4)

    if errors:
        exit(5)

finally:
    if mod_path and os.path.exists(mod_path):
        shutil.rmtree(mod_path)
    if tmpdir and os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
