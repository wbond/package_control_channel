import sublime
import sublime_plugin
import re


class FoldthiscodeCommand(sublime_plugin.TextCommand):
	def run(self, edit, fold):
		starts = [m.start() for m in re.finditer('//fold', self.view.substr(sublime.Region(0,self.view.size())))]
		ends = [m.start() for m in re.finditer('//endfold', self.view.substr(sublime.Region(0,self.view.size())))]
		stacked = []
		starts.append(self.view.size())
		ends.append(self.view.size())
		curs = 0
		cure = 0
		while curs+cure !=+ len(starts)+len(ends)-2:
			if ends[cure]<starts[curs]:
				if len(stacked) != 0:
					if fold:
						self.view.fold(sublime.Region(stacked[-1],ends[cure]+9))
					else:
						self.view.unfold(sublime.Region(stacked[-1],ends[cure]+9))
					cure += 1
			else:
				stacked.append(starts[curs])
				curs += 1