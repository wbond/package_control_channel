# Package Control Default Channel

The `channel.json`, `repository.json` and `repository/*.json` files contain a
list of repositories and packages for use with
[Package Control](https://packagecontrol.io).

These source files are processed by a crawler[^io] and compiled into a single file,
`channel_v3.json`, which serves as the primary channel used by the Package
Control client. This compiled file is published at https://packagecontrol.io/channel_v3.json
and is included with Package Control as the default channel.

Libraries (previously named "dependencies") have their own registry at the moment.
You can find them at https://github.com/packagecontrol/channel.

[^io]: This infrastructure has its own repo at https://github.com/wbond/packagecontrol.io

**Please be sure to follow the instructions at
https://packagecontrol.io/docs/submitting_a_package to help the process of adding your
package or repository go smoothly.**

## Style guide

A few words towards naming conventions etc, for entries in these files:

- Packages avoid having the word "Sublime" in their name (see [docs](https://packagecontrol.io/docs/submitting_a_package#Step_2)). 
- Language support (aka "syntax" or "grammar") packages are named after the language it supports, without suffixes like "syntax" or "highlighting" (e.g. #8801).
- Labels are always in lowercase.
- Packages that provide ... 
  - a [language syntax](https://www.sublimetext.com/docs/syntax.html) have the "language syntax" label (see #9088).
  - (the colors for) [syntax highlighting](https://www.sublimetext.com/docs/color_schemes.html) have the "color scheme" label, whereas packages that provide [theming for the UI](https://www.sublimetext.com/docs/themes.html) have the "theme" label.
  - a [build system](https://www.sublimetext.com/docs/build_systems.html) have the "build system" label (see #9093).
  - [snippets](https://www.sublimetext.com/docs/completions.html#snippets) have the "snippets" label (see #9095).
  - [completion metadata](https://www.sublimetext.com/docs/completions.html#completion-metadata) have the "completions" label (see #9095).
  - any other kind of auto-complete have the "auto-complete" label (see #9095).
  - formatters have the "formatting" label, and optionally "prettify" or "minify", if appropriate.
- Utility packages have the "utilities" label (see #9094).

## Other notable repositories

This is the main repository of Sublime Text packages. However:

- Linter packages should in most cases be submitted over at [SublimeLinter](https://github.com/SublimeLinter/package_control_channel).
- Similarly, any language server protocol packages are managed via [SublimeLSP](https://github.com/sublimelsp/repository).
