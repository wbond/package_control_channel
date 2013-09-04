import json
import re
import os
from collections import OrderedDict
from urllib.request import urlopen
from urllib.error import HTTPError


st3_compatiable = [
    'ADBView',
    'AdvancedNewFile',
    'Andrew',
    'AngularJS',
    'AutoBackups',
    'Better CoffeeScript',
    'BracketHighlighter',
    'BufferScroll',
    'Case Conversion',
    'ChangeQuotes',
    'CheckBounce',
    'Clipboard Manager',
    'CodeFormatter',
    'ColorPicker',
    'CompleteSharp',
    'ConvertToUTF8',
    'CopyEdit',
    'CriticMarkup',
    'Cscope',
    'CSScomb',
    'CSSFontFamily',
    'CursorRuler',
    'DeleteBlankLines',
    'Djaneiro',
    'DocBlockr',
    'EditorConfig',
    'EditPreferences',
    'ElasticTabstops',
    'Emmet',
    'Ensime',
    'Expand Selection to Function (JavaScript)',
    'ExportHtml',
    'eZ Publish Syntax',
    'FavoriteFiles',
    'File History',
    'FileDiffs',
    'Filter Lines',
    'FindKeyConflicts',
    'Floobits',
    'FuzzyFileNav',
    'GenerateUUID',
    'Git',
    'GitGutter',
    'google-search',
    'GoSublime',
    'Hex to HSL Color Converter',
    'HexViewer',
    'Highlight',
    'HighlightWords',
    'Hipster Ipsum',
    'Http Requester',
    'IMESupport',
    'InactivePanes',
    'JavaPropertiesEditor',
    'JavaScript Refactor',
    'JsFormat',
    'JsRun',
    'Koan',
    'Laravel Blade Highlighter',
    'LaTeXing3',
    'LaTeXTools',
    'Less2Css',
    'LineEndings',
    'Local History',
    'MarkAndMove',
    'Markboard3',
    'Markdown Preview',
    'Marked.app Menu',
    'Mediawiker',
    'memTask',
    'Modific',
    'NaturalSelection',
    'Nettuts+ Fetch',
    'Nodejs',
    'ObjC2RubyMotion',
    'OmniMarkupPreviewer',
    'Open-Include',
    'orgmode',
    'Origami',
    'PackageResourceViewer',
    'Pandown',
    'PersistentRegexHighlight',
    'PgSQL',
    'PHP Companion',
    'Phpcs',
    'PHPUnit',
    'PlainTasks',
    'PlistJsonConverter',
    'Python PEP8 Autoformat',
    'Rails Latest Migration',
    'Rails Migrations List',
    'Random Text',
    'RegReplace',
    'Ruby Hash Converter',
    'RubyTest',
    'ScalaFormat',
    'Schemr',
    'ScopeHunter',
    'SelectUntil',
    'SideBarEnhancements',
    'SideBarGit',
    'SimpleSync',
    'Smart Delete',
    'Solarized Toggle',
    'Strapdown Markdown Preview',
    'StringUtilities',
    'sublime-github',
    'SublimeAStyleFormatter',
    'SublimeClang',
    'SublimeGDB',
    'SublimeGit',
    'SublimeInsertDatetime',
    'sublimelint',
    'SublimeLinter',
    'SublimePeek',
    'SublimeREPL',
    'Sublimerge',
    'SublimeSBT',
    'SublimeTmpl',
    'SublimeXiki',
    'Surround',
    'SyncedSideBar',
    'Table Editor',
    'Tag',
    'Theme - Flatland',
    'Theme - Nil',
    'Theme - Phoenix',
    'Theme - Soda',
    'Themr',
    'TOML',
    'Tradsim',
    'TrailingSpaces',
    'TWiki',
    'URLEncode',
    'View In Browser',
    'Vintageous',
    'Wind',
    'WordCount',
    'Worksheet',
    'Xdebug Client',
    'Xdebug'
]


# CONFIGURATION FOR MIGRATION PROCESS
old_repositories_json_path = './repositories.json'
client_auth = os.environ['PACKAGE_CONTROL_AUTH']
new_repository_url = './repository.json'

requests = 0
five_hundreds = 0

with open(old_repositories_json_path, encoding='utf-8') as of:
    old_data = json.load(of)

    master_list = []
    repositories_from_orgs = []
    repositories_without_orgs = []

    for repository in old_data['repositories']:
        user_match = re.match('https://github.com/([^/]+)$', repository)
        if user_match:
            api_url = 'https://api.github.com/users/%s/repos?per_page=100&%s' % (user_match.group(1), client_auth)
            json_string = urlopen(api_url).read()
            requests += 1
            data = json.loads(str(json_string, encoding='utf-8'))
            for repo in data:
                repositories_from_orgs.append(repo['html_url'])
        else:
            repositories_without_orgs.append(repository)

    repositories_to_process = repositories_without_orgs + repositories_from_orgs

    for repository in repositories_to_process:
        repo_match = re.match('https://(github.com)/([^/]+)/([^/]+)(?:/tree/([^/]+))?$', repository)

        if repo_match:
            old_name = None
            prev_names = None
            user = repo_match.group(2)
            repo = repo_match.group(3)
            name = repo_match.group(3)
            branch = 'master'
            if repo_match.group(4):
                branch = repo_match.group(4)

            if name in old_data['package_name_map']:
                old_name = name
                name = old_data['package_name_map'][name]

            # Skip duplicate sources for packages
            if name in master_list:
                continue

            if name in st3_compatiable:
                continue

            success = False
            while not success:
                try:
                    branch_url = 'https://api.github.com/repos/%s/%s/branches/%s?%s' % (user, repo, branch, client_auth)
                    requests += 1
                    json_string = urlopen(branch_url).read()
                    data = json.loads(str(json_string, encoding='utf-8'))
                    sha = data['commit']['sha']

                    tree_url = 'https://api.github.com/repos/%s/%s/git/trees/%s?%s' % (user, repo, sha, client_auth)
                    requests += 1
                    json_string = urlopen(tree_url).read()
                    data = json.loads(str(json_string, encoding='utf-8'))

                    success = True
                except (HTTPError):
                    five_hundreds += 1
                    print('Requests: %s, 500s: %s' % (requests, five_hundreds))
                    pass

            has_python = False
            for entry in data['tree']:
               if re.search('\.py$', entry['path']) is not None:
                   has_python = True
                   break

            if not has_python:
                print('No python: %s' % name)
            else:
                print('Yes python: %s' % name)

            master_list.append(name)

