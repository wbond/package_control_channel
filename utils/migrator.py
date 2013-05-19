import json
import re
from collections import OrderedDict
from urllib.request import urlopen


# CONFIGURATION FOR MIGRATION PROCESS
old_repositories_json_path = './repositories.json'
new_channel_path = './channel.json'
new_repository_path = './repository.json'

new_repository_url = './repository.json'
new_repository_subfolder_path = './repository/'


with open(old_repositories_json_path, encoding='utf-8') as of:
    old_data = json.load(of)
    previous_names = OrderedDict()
    for key, value in old_data['renamed_packages'].items():
        if value not in previous_names:
            previous_names[value] = []
        previous_names[value].append(key)

    names = OrderedDict()
    master_list = OrderedDict()
    repositories = [new_repository_url]
    repositories_from_orgs = []

    repositories_without_orgs = []
    for repository in old_data['repositories']:
        user_match = re.match('https://github.com/([^/]+)$', repository)
        if user_match:
            api_url = 'https://api.github.com/users/%s/repos?per_page=100' % user_match.group(1)
            json_string = urlopen(api_url).read()
            data = json.loads(str(json_string, encoding='utf-8'))
            for repo in data:
                repositories_from_orgs.append(repo['html_url'])
        else:
            repositories_without_orgs.append(repository)

    repositories_to_process = repositories_without_orgs + repositories_from_orgs

    for repository in repositories_to_process:
        repo_match = re.match('https://(github.com|bitbucket.org)/([^/]+)/([^/]+)(?:/tree/([^/]+))?$', repository)

        if repo_match:
            old_name = None
            prev_names = None
            name = repo_match.group(3)
            branch = 'master' if repo_match.group(1) == 'github.com' else 'default'
            if repo_match.group(4):
                branch = repo_match.group(4)

            # BitBucket repos that don't use the branch named "default"
            if name in ['quick-rails', 'quickref', 'smartmovetotheeol', 'sublime-http-response-headers-snippets', 'sublimesourcetree', 'zap-gremlins', 'andrew']:
                branch = 'master'

            if name in old_data['package_name_map']:
                old_name = name
                name = old_data['package_name_map'][name]

            # Skip duplicate sources for packages
            if name in master_list:
                continue

            if name in previous_names:
                prev_names = previous_names[name]

            letter = name[0].lower()
            if letter in [str(num) for num in range(0, 9)]:
                letter = '0-9'

            if letter not in names:
                names[letter] = []

            names[letter].append(name)
            entry = OrderedDict()
            if old_name:
                entry['name'] = name

            entry['details'] = repository

            if repo_match.group(1).lower() == 'github.com':
                release_url = 'https://github.com/%s/%s/tree/%s' % (repo_match.group(2), repo_match.group(3), branch)
            else:
                release_url = 'https://bitbucket.org/%s/%s/src/%s' % (repo_match.group(2), repo_match.group(3), branch)
            entry['releases'] = [
                OrderedDict([
                    ('sublime_text', '<3000'),
                    ('details', release_url)
                ])
            ]

            if prev_names:
                entry['previous_names'] = prev_names
            master_list[name] = entry

        else:
            repository = repository.replace('http://sublime.wbond.net/', 'https://sublime.wbond.net/')
            repositories.append(repository)


includes = []

for letter in names:
    include_path = '%s%s.json' % (new_repository_subfolder_path, letter)
    includes.append(include_path)
    sorted_names = sorted(names[letter], key=str.lower)
    sorted_packages = []
    for name in sorted_names:
        sorted_packages.append(master_list[name])
    with open(include_path, 'w', encoding='utf-8') as f:
        data = OrderedDict([
            ('schema_version', '2.0'),
            ('packages', [])
        ])
        data['packages'] = sorted_packages
        json.dump(data, f, indent="\t")

with open(new_channel_path, 'w', encoding='utf-8') as f:
    data = OrderedDict()
    data['schema_version'] = '2.0'
    data['repositories'] = repositories
    json.dump(data, f, indent="\t")

with open(new_repository_path, 'w', encoding='utf-8') as f:
    data = OrderedDict()
    data['schema_version'] = '2.0'
    data['packages'] = []
    data['includes'] = sorted(includes)
    json.dump(data, f, indent="\t")
