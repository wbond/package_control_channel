import json
import re
import os
from collections import OrderedDict
from urllib.request import urlopen


# CONFIGURATION FOR MIGRATION PROCESS
old_repositories_json_path = './repositories.json'
new_channel_path = './channel.json'
new_repository_path = './repository.json'

new_repository_url = './repository.json'
new_repository_subfolder_path = './repository/'

client_auth = os.environ['PACKAGE_CONTROL_AUTH']


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
            api_url = 'https://api.github.com/users/%s/repos?per_page=100&%s' % (user_match.group(1), client_auth)
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
            if name in ['html-crush-switch', 'whocalled', 'jsonlint',
                    'symfonytools-for-sublimetext-2', 'html-compress-and-replace',
                    'sublime-aml', 'quick-rails', 'quickref', 'smartmovetotheeol',
                    'sublime-http-response-headers-snippets', 'sublimesourcetree',
                    'zap-gremlins', 'andrew', 'bootstrap-jade']:
                branch = 'master'

            if name in old_data['package_name_map']:
                old_name = name
                name = old_data['package_name_map'][name]

            # Fixes for bitbucket repos that are using a package_name_map
            if name == 'pythonpep8autoformat':
                old_name = name
                name = 'Python PEP8 Autoformat'
            if name == 'sublimesourcetree':
                old_name = name
                name = 'SourceTree'
            if name == 'sublime-http-response-headers-snippets':
                old_name = name
                name = 'HTTP Response Headers Snippets'
            if name == 'symfonytools-for-sublimetext-2':
                old_name = name
                name = 'SymfonyTools'
            if name == 'statusbarextension':
                old_name = name
                name = 'Status Bar Extension'

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

            # According to the wiki, these are compatible with
            # ST3 without any extra work
            st3_compatiable = [
                'ADBView',
                'AdvancedNewFile',
                'Andrew',
                'AngularJS',
                'AutoBackups',
                'Better CoffeeScript',
                'Case Conversion',
                'CheckBounce',
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
                'Expand Selection to Function (JavaScript)',
                'eZ Publish Syntax',
                'File History',
                'Filter Lines',
                'FindKeyConflicts',
                'Floobits',
                'GenerateUUID',
                'GitGutter',
                'google-search',
                'GoSublime',
                'Hex to HSL Color Converter',
                'HighlightWords',
                'Hipster Ipsum',
                'IMESupport',
                'InactivePanes',
                'JavaPropertiesEditor',
                'JavaScript Refactor',
                'JsFormat',
                'JsRun',
                'Laravel Blade Highlighter',
                'LaTeXTools',
                'Less2Css',
                'Local History',
                'MarkAndMove',
                'Marked.app Menu',
                'Mediawiker',
                'memTask',
                'Modific',
                'NaturalSelection',
                'Nettuts+ Fetch',
                'ObjC2RubyMotion',
                'OmniMarkupPreviewer',
                'Open-Include',
                'orgmode',
                'Origami',
                'PackageResourceViewer',
                'Pandown',
                'PersistentRegexHighlight',
                'PgSQL',
                'Phpcs',
                'PHPUnit',
                'PlainTasks',
                'Python PEP8 Autoformat',
                'Rails Latest Migration',
                'Rails Migrations List',
                'Random Text',
                'Ruby Hash Converter',
                'RubyTest',
                'ScalaFormat',
                'Schemr',
                'SelectUntil',
                'SimpleSync',
                'Smart Delete',
                'Solarized Toggle',
                'sublime-github',
                'SublimeAStyleFormatter',
                'SublimeClang',
                'SublimeGDB',
                'SublimeGit',
                'SublimeInsertDatetime',
                'SublimeREPL',
                'SublimeSBT',
                'SublimeTmpl',
                'Surround',
                'SyncedSideBar',
                'Table Editor',
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
                'Wind',
                'Worksheet',
                'Xdebug',
                'Xdebug Client',
                'Transience',
                'RemoteOpen',
                'Path Tools',
                'WakaTime',
                'AutoSoftWrap',
                'fido',
                'Preference Helper',
                'HTML-CSS-JS Prettify',
                'JSHint Gutter',
                'Vintage Escape',
                'Ruby Pipe Text Processing',
                'Crypto',
                'Preset Command',
                'Sublime​Log',
                'PHP Code Coverage',
                'Status Bar Extension',
                'To Hastebin',
                'Alphpetize',
                'BeautifyRuby',
                'BoundKeys',
                'Evaluate',
                'FindSelected',
                'JSONLint',
                'Pretty JSON',
                'Restructured Text (RST) Snippets',
                'PySide',
                'Diagram',
                'Japanize',
                'SimpleClone',
                'rsub',
                'Pman',
                'Gist'
            ]

            # These packages have a separate branch for ST3
            st3_with_branch = {
                'BracketHighlighter': 'BH2ST3',
                'BufferScroll': 'st3',
                'ChangeQuotes': 'st3',
                'Ensime': 'ST3',
                'ExportHtml': 'ST3',
                'FavoriteFiles': 'ST3',
                'FileDiffs': 'st3',
                'FuzzyFileNav': 'ST3',
                'Git': 'python3',
                'HexViewer': 'ST3',
                'LineEndings': 'st3',
                'Markdown Preview': 'ST3',
                'Nodejs': 'sublime-text-3',
                'PlistJsonConverter': 'ST3',
                'RegReplace': 'ST3',
                'ScopeHunter': 'ST3',
                'SideBarEnhancements': 'st3',
                'SideBarGit': 'st3',
                'Clipboard Manager': 'st3',
                'SublimeLinter': 'sublime-text-3',
                'Highlight': 'python3',
                'Http Requester': 'st3',
                'SublimePeek': 'ST3',
                'StringUtilities': 'ST3',
                'sublimelint': 'st3',
                'SublimeXiki': 'st3',
                'Tag': 'st3',
                'WordCount': 'st3',
                'Code Runner': 'SublimeText3',
                'Sublimerge': 'sublime-text-3'
            }

            no_python = [
                '3024 Color Scheme',
                '4GL',
                'ABC Notation',
                'ActionScript 3',
                'Additional PHP Snippets',
                'Alternate VIM Navigation',
                'AmpScript Highlighter',
                'AMPScript',
                'AndyPHP',
                'AngelScript',
                'AngularJS (CoffeeScript)',
                'AngularJS Snippets',
                'Ant Buildfile',
                'Ant',
                'APDL (ANSYS) Syntax Highlighting',
                'Aqueducts',
                'AriaTemplates Highlighter',
                'AriaTemplates Snippets',
                'ARM Assembly',
                'Arnold Clark Snippets for Ruby',
                'ASCII Comment Snippets',
                'AsciiDoc',
                'Async Snippets',
                'AVR-ASM-Sublime',
                'Awk',
                'Backbone Baguette',
                'Backbone.js',
                'Backbone.Marionette',
                'Base16 Color Schemes',
                'Behat Features',
                'Behat Snippets',
                'Behat',
                'BEMHTML',
                'BHT-BASIC',
                'Blade Snippets',
                'Blusted Scheme',
                'Boo',
                'Bootstrap 3 Snippets',
                'Boron Color Scheme',
                'Bubububububad and Boneyfied Color Schemes',
                'C# Compile & Run',
                'CakePHP (Native)',
                'CakePHP (tmbundle)',
                'Capybara Snippets',
                'CasperJS',
                'CFeather',
                'Chai Completions',
                'Chaplin.js',
                'Cheetah Syntax Highlighting',
                'Chef',
                'ChordPro',
                'Chuby Ninja Color Scheme',
                'ChucK Syntax',
                'Ciapre Color Scheme',
                'Clay Schubiner Color Schemes',
                'CLIPS Rules',
                'ClosureMyJS',
                'CMake',
                'CMS Made Simple Snippets',
                'Coco R Syntax Highlighting',
                'CodeIgniter 2 ModelController',
                'CodeIgniter Snippets',
                'CodeIgniter Utilities',
                'CoffeeScriptHaml',
                'ColdBox Platform',
                'Color Scheme - Eggplant Parm',
                'Color Scheme - Frontend Delight',
                'Color Scheme - saulhudson',
                'Color Scheme - Sleeplessmind',
                'Color Schemes by carlcalderon',
                'Comment-Snippets',
                'ComputerCraft Package',
                'CoreBuilder',
                'Creole',
                'CSS Media Query Snippets',
                'CSS Snippets',
                'Cube2Media Color Scheme',
                'CUDA C++',
                'CUE Sheet',
                'Dafny',
                'Dark Pastel Color Scheme',
                'Dayle Rees Color Schemes',
                'DBTextWorks',
                'Derby - Bourbon & Neat Autocompletions',
                'DFML (for Dwarf Fortress raws)',
                'Dictionaries',
                'Dimmed Color Scheme',
                'DobDark Color Scheme',
                'Doctrine Snippets',
                'Doctypes',
                'Dogs Colour Scheme',
                'Dotfiles Syntax Highlighting',
                'DotNetNuke Snippets',
                'Drupal Snippets',
                'Drupal',
                'Dust.js',
                'Dylan',
                'eco',
                'ECT',
                'Elixir',
                'Elm Language Support',
                'Ember.js Snippets',
                'Emmet Css Snippets',
                'EmoKid Color Scheme',
                'Enhanced Clojure',
                'Enhanced HTML and CFML',
                'Enlightened Color Scheme',
                'ERB Snippets',
                'Esuna Framework Snippets',
                'Express Color Scheme',
                'ExpressionEngine',
                'F#',
                'Failcoder Color Scheme',
                'FakeImg.pl Image Placeholder Snippet',
                'FarCry',
                'FASM x86',
                'Fat-Free Framework Snippets',
                'fish-shell',
                'FLAC',
                'Flex',
                'Focus',
                'Foundation Snippets',
                'Fountain',
                'FreeMarker',
                'Front End Snippets',
                'Future Funk - Color Scheme',
                'Gaelyk',
                'Gauche',
                'Genesis',
                'Git Config',
                'GMod Lua',
                'Google Closure Library snippets',
                'GoogleTesting',
                'Grandson-of-Obsidian',
                'Grid6',
                'GYP',
                'Haml',
                'Hamlpy',
                'Handlebars',
                'hlsl',
                'Homebrew-formula-syntax',
                'hosts',
                'HTML Compressor',
                'HTML Email Snippets',
                'HTML Mustache',
                'HTML Snippets',
                'HTML5 Doctor CSS Reset snippet',
                'HTML5',
                'HTMLAttributes',
                'IcedCoffeeScript',
                'Idiomatic-CSS-Comments-Snippets',
                'Idoc',
                'ImpactJS',
                'INI',
                'Issues',
                'Jade Snippets',
                'Jade',
                'Java Velocity',
                'JavaScript Console',
                'JavaScript Patterns',
                'JavaScript Snippets',
                'JavaScriptNext - ES6 Syntax',
                'Jinja2',
                'jQuery Mobile Snippets',
                'jQuery Snippets for Coffeescript',
                'jQuery Snippets pack',
                'jQuery',
                'JS Snippets',
                'JsBDD',
                'Julia',
                'knockdown',
                'KnowledgeBase',
                'Kohana 2.x Snippets',
                'Kohana',
                'Koken',
                'Kotlin',
                'KWrite Color Scheme',
                'Language - Up-Goer-5',
                'Laravel 4 Snippets',
                'Laravel Bootstrapper Snippets',
                'Laravel Color Scheme',
                'Laravel Snippets',
                'Lasso',
                'LaTeX Blindtext',
                'LaTeX Track Changes',
                'LaTeX-cwl',
                'Lazy Backbone.js',
                'Ledger syntax highlighting',
                'Legal Document Snippets',
                'LESS',
                'LESS-build',
                'Lift Snippets',
                'lioshi Color Scheme',
                'Liquid',
                'Lithium Snippets',
                'LLVM',
                'Lo-Dash Snippets for CoffeeScript',
                'Logger Snippets',
                'Loom Game Engine',
                'M68k Assembly',
                'Madebyphunky Color Scheme',
                'Mako',
                'Maperitive',
                'Markdown Extended',
                'MasmAssembly',
                'Mason',
                'MelonJS Completions',
                'MinimalFortran',
                'MinkExtension default feature step completions',
                'MIPS Syntax',
                'Mirodark Color Scheme',
                'Missing Palette Commands',
                'Mocha Snippets',
                'MODx Revolution Snippets',
                'Mojolicious',
                'MongoDB - PHP Completions',
                'Mongomapper Snippets',
                'Monokai Blueberry Color Scheme',
                'Monokai Extended',
                'Moscow ML',
                'Mplus',
                'Mreq Color Scheme',
                'MultiLang Color Scheme',
                'Neat Sass Snippets',
                'Nemerle',
                'Neon Theme',
                'NESASM',
                'Nette',
                'nginx',
                'Nimrod',
                'NSIS Autocomplete (Add-ons)',
                'NSIS Autocomplete and Snippets',
                'NSIS',
                'objc .strings syntax language',
                'Oblivion Color Scheme',
                'Oceanic Color Scheme',
                'OpenEdge ABL',
                'OpenGL Shading Language (GLSL)',
                'Papyrus Assembly',
                'PEG.js',
                'Perv - Color Scheme',
                'Phix Color Scheme',
                'PHP Haml',
                'PHP MySQLi connection',
                'PHP-Twig',
                'PHPUnit Completions',
                'PHPUnit Snippets',
                'PKs Color Scheme',
                'Placeholders',
                'Placester',
                'Play 2.0',
                'Pre language syntax highlighting',
                'Processing',
                'Prolog',
                'Puppet',
                'PyroCMS Snippets',
                'Python Auto-Complete',
                'Python Nose Testing Snippets',
                'Racket',
                'Rails Developer Snippets',
                'RailsCasts Colour Scheme',
                'Raydric - Color Scheme',
                'Red Planet Color Scheme',
                'RPM Spec Syntax',
                'RSpec (snippets and syntax)',
                'rspec-snippets',
                'Ruby on Rails snippets',
                'ruby-slim.tmbundle',
                'RubyMotion Autocomplete',
                'RubyMotion Sparrow Framework Autocomplete',
                'Rust',
                'SASS Build',
                'SASS Snippets',
                'Sass',
                'scriptcs',
                'SCSS Snippets',
                'Selenium Snippets',
                'Sencha',
                'Silk Web Toolkit Snippets',
                'SilverStripe',
                'SimpleTesting',
                'Six - Future JavaScript Syntax',
                'SJSON',
                'Slate',
                'SLAX',
                'Smali',
                'Smarty',
                'SML (Standard ML)',
                'Solarized Color Scheme',
                'SourcePawn Syntax Highlighting',
                'SPARC Assembly',
                'Spark',
                'SQF Language',
                'SSH Config',
                'StackMob JS Snippets',
                'Stan',
                'Stylus',
                'SubLilyPond',
                'Sublime-KnockoutJS-Snippets',
                'sublime-MuPAD',
                'SublimeClarion',
                'SublimeDancer',
                'SublimeLove',
                'SublimePeek-R-help',
                'SublimeSL',
                'sublimetext.github.com',
                'Summerfruit Color Scheme',
                'Sundried Color Scheme',
                'Superman Color Scheme',
                'Susy Snippets',
                'Symfony2 Snippets',
                'Syntax Highlighting for Sass',
                'Test Double',
                # Skipped since unsure if themes port well 'Theme - Aqua',
                # Skipped since unsure if themes port well 'Theme - Centurion',
                # Skipped since unsure if themes port well 'Theme - Cobalt2',
                # Skipped since unsure if themes port well 'Theme - Farzher',
                # Skipped since unsure if themes port well 'Theme - Nexus',
                # Skipped since unsure if themes port well 'Theme - Night',
                # Skipped since unsure if themes port well 'Theme - Pseudo OSX',
                # Skipped since unsure if themes port well 'Theme - Reeder',
                # Skipped since unsure if themes port well 'Theme - Refined',
                # Skipped since unsure if themes port well 'Theme - Refresh',
                # Skipped since unsure if themes port well 'Theme - Tech49',
                'Three.js Autocomplete',
                'TideSDK Autocomplete',
                'tipJS Snippets',
                'TJ3-syntax-sublimetext2',
                'Tmux',
                'Todo',
                'TomDoc',
                'Tomorrow Color Schemes',
                'tQuery',
                'TreeTop',
                'Tritium',
                'Tubaina (afc)',
                'Twee',
                'Twig',
                'Twitter Bootstrap ClassNames Completions',
                'Twitter Bootstrap Snippets',
                'TypeScript',
                'Ublime Color Schemes',
                'Underscore.js Snippets',
                'UnindentPreprocessor',
                'Unittest (python)',
                'Unity C# Snippets',
                'Unity3D Build System',
                'Unity3d LeanTween Snippets',
                'Unity3D Shader Highlighter and Snippets',
                'Unity3D Snippets and Completes',
                'Unity3D',
                'UnofficialDocs',
                'Vala',
                'Various Ipsum Snippets',
                'VBScript',
                'VDF',
                'Verilog',
                'VGR-Assistant',
                'Vintage Surround',
                'Vintage-Origami',
                'WebExPert - ColorScheme',
                'WebFocus',
                'Wombat Theme',
                'WooCommerce Autocomplete',
                'Wordpress',
                'World of Warcraft TOC file Syntax',
                'World of Warcraft XML file Syntax',
                'WoW Development',
                'XAML',
                'XpressEngine',
                'XQuery',
                'XSLT Snippets',
                'Yate',
                'Yii Framework Snippets',
                'YUI Compressor',
                'ZenGarden',
                'Zenoss',
                'Zissou Color Schemes',
                'Zurb Foundation 4 Snippets',
                'Mustang Color Scheme',
                'Kimbie Color Scheme'
            ]

            st3_only = [
                'Less Tabs',
                'Toggl Timer',
                'Javatar',
                'WordPress Generate Salts',
                'subDrush',
                'LaTeXing3',
                'Markboard3',
                'Web Inspector 3',
                'PHP Companion',
                'Python IDE',
                'ScalaWorksheet',
                'Vintageous',
                'Strapdown Markdown Preview',
                'StripHTML',
                'MiniPy',
                'Package Bundler',
                'Koan',
                'StickySearch',
                'CodeSearch',
                'Anaconda'
            ]


            compatible_version = '<3000'
            if name in st3_compatiable:
                compatible_version = '*'

            if name in no_python:
                compatible_version = '*'

            if name in st3_only:
                compatible_version = '>=3000'

            entry['details'] = repository

            if repo_match.group(1).lower() == 'github.com':
                release_url = 'https://github.com/%s/%s/tree/%s' % (repo_match.group(2), repo_match.group(3), branch)
            else:
                release_url = 'https://bitbucket.org/%s/%s/src/%s' % (repo_match.group(2), repo_match.group(3), branch)
            entry['releases'] = [
                OrderedDict([
                    ('sublime_text', compatible_version),
                    ('details', release_url)
                ])
            ]

            if name in st3_with_branch:
                if repo_match.group(1).lower() == 'github.com':
                    release_url = 'https://github.com/%s/%s/tree/%s' % (repo_match.group(2), repo_match.group(3), st3_with_branch[name])
                else:
                    release_url = 'https://bitbucket.org/%s/%s/src/%s' % (repo_match.group(2), repo_match.group(3), st3_with_branch[name])
                entry['releases'].append(
                    OrderedDict([
                        ('sublime_text', '>=3000'),
                        ('details', release_url)
                    ])
                )

            if prev_names:
                entry['previous_names'] = prev_names
            master_list[name] = entry

        else:
            repository = repository.replace('http://sublime.wbond.net/', 'https://sublime.wbond.net/')
            repositories.append(repository)


def dump(data, f):
    json.dump(data, f, indent="\t", separators=(',', ': '))


includes = []

if not os.path.exists(new_repository_subfolder_path):
    os.mkdir(new_repository_subfolder_path)

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
        dump(data, f)

with open(new_channel_path, 'w', encoding='utf-8') as f:
    data = OrderedDict()
    data['schema_version'] = '2.0'
    data['repositories'] = repositories
    dump(data, f)

with open(new_repository_path, 'w', encoding='utf-8') as f:
    data = OrderedDict()
    data['schema_version'] = '2.0'
    data['packages'] = []
    data['includes'] = sorted(includes)
    dump(data, f)
