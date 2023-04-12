<!--
The manual review may take several days or weeks,
depending on the reviewer's availability and workload.
Patience padawan!

You can request a review from @packagecontrol-bot.
Please ensure the reviews pass and follow any instructions.

Please provide some information via this checklist,
feel free to remove what't not applicable.
-->

- [ ] I'm the package's author and/or maintainer.
- [ ] I have have read [the docs][1].
- [ ] I have tagged a release with a [semver][2] version number.
- [ ] My package repo has a description and a README describing what it's for and how to use it.
- [ ] My package doesn't add context menu entries. *
- [ ] My package doesn't add key bindings. **
- [ ] Any commands are available via the command palette.
- [ ] Preferences and keybindings (if any) are listed in the menu and the command palette, and open in split view.
- [ ] If my package is a syntax it doesn't also add a color scheme. ***
- [ ] If my package is a syntax it is named after the language it supports (without suffixes like "syntax" or "highlighting").
- [ ] I use [.gitattributes][3] to exclude files from the package: images, test files, sublime-project/workspace.

My package is ...

There are no packages like it in Package Control.
<!-- OR -->
My package is similar to ... However it should still be added because ...


<!-- 
*)   Unless it definitely really needs them,
     they apply to the cursor's context
     and their visibility is conditional.
     Space in this menu is limited!
**)  There aren't enough keys for all packages,
     you'd risk overriding those of other packages.
     You can put commented out suggestions in a keymap file, 
     and/or explain how to create bindings in your README.
***) We have hundreds of color schemes,
     and plenty of scopes to make any syntax work. 

For bonus points also considered how the review guidelines apply to your package:
https://github.com/wbond/package_control_channel/wiki#reviewing-a-package-addition

For updates to existing packages:
If your package isn't using tag based releases,
please switch to tags now.
 -->

[1]: https://packagecontrol.io/docs/submitting_a_package
[2]: https://semver.org
[3]: https://www.git-scm.com/docs/gitattributes#_export_ignore
