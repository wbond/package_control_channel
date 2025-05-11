# Package Control Default Channel

The `channel.json`, `repository.json` and `repository/*.json` files contain a
list of repositories and packages for use with
[Package Control](https://packagecontrol.io).

The `channel.json` file is published at https://packagecontrol.io/channel_v3.json
and is included with Package Control as the default channel.

**Please be sure to follow the instructions at
https://packagecontrol.io/docs/submitting_a_package to help the process of adding your
package or repository go smoothly.**

## Style guide

A few words towards naming conventions etc, for entries in these files:

- Packages avoid having the word "Sublime" in their name (see [docs](https://packagecontrol.io/docs/submitting_a_package#Step_2)). 
- Syntax packages are named after the language it supports, without suffixes like "syntax" or "highlighting" (e.g. #8801).
- Labels:
  - Syntax packages have the "language syntax" label (see #9088).
  - Utility packages have the "utilities" label (see #9094).
  - Packages that introduce a [build system](https://www.sublimetext.com/docs/build_systems.html) have the "build system" label (see #9093).
  - Packages that introduce [snippets](https://www.sublimetext.com/docs/completions.html#snippets) have the "snippets" label (see #9095).
  - Packages that introduce [completion metadata](https://www.sublimetext.com/docs/completions.html#completion-metadata) have the "completions" label (see #9095).
  - Packages that introduce any other kind of auto-complete have the "auto-complete" label (see #9095).
