#
# thot.tparser -- Thot document parser
# Copyright (C) 2009  <hugues.casse@laposte.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Generic parser for Thot."""

from collections.abc import Callable
import os.path
import re
from re import Pattern
from typing import Any, IO, Iterator
from types import ModuleType

from thot import doc
from thot import common

DEBUG = False

type HandleFun = Callable[["Manager", re.Match], None]
type WordSyntax = list[tuple[HandleFun, str]]
type LineSyntax = list[tuple[HandleFun, re.Pattern]]
type CompleterFun = Callable[["Manager"], None]

PARSERS: dict[str, str|None] = {
	".creole":		"creole",
	".doku": 		"dokuwiki",
	".markdown":	"markdown",
	".md": 			"markdown",
	".mdown":		"markdown",
	".mkd": 		"markdown",
	".mkdown":		"markdown",
	".mdown":		"markdown",
	".textile": 	"textile",
	".thot": 		None,
	".wiki": "wiki"
}


def handleText(man: "Manager", line: str, suffix: str = ' ') -> None:

	# init RE_WORDS
	if man.words_re is None:
		text = ""
		i = 0
		for (fun, wre) in man.words:
			if text != "":
				text = text + "|"
			text = text + "(?P<a" + str(i) + ">" + wre + ")"
			i = i + 1
		man.words_re = re.compile(text)

	# look in line
	words_re = man.words_re
	match = words_re.search(line)
	while match is not None:
		assert match.lastgroup is not None
		idx = int(match.lastgroup[1:])
		fun, wre = man.words[idx]
		word = line[:match.start()]
		if word:
			man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, man.factory.makeWord(word)))
		line = line[match.end():]
		fun(man, match)
		match = man.words_re.search(line)

	# end of line
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, man.factory.makeWord(line + suffix)))


class LineParser:
	"""Abstract class of line parser."""

	def __init__(self):
		self.prev = None

	def parse(self, manager: "Manager", line: str) -> None:
		"""Parse the given line using the given manager."""
		pass


class DefaultParser(LineParser):
	"""Default parser that tries to parser the line with the manager
	recorded lines. Else scan the text with the manager recorded words."""

	def parse(self, manager: "Manager", line: str) -> None:
		line = manager.doc.reduceVars(line)
		done = False
		for (fun, re) in manager.lines:
			match = re.match(line)
			if match:
				fun(manager, match)
				done = True
				break
		if not done:
			handleText(manager, line)


class Syntax:
	"""Base class of all syntaxes added to the parser."""

	def get_doc(self) -> list[tuple[str, str]]:
		"""Get the documentation for the syntax, a sequence of pairs
		(RE, description) where RE is a pseudo-regular expression
		describing the syntax and description is the descritpion of the
		syntax (possibly multi-line)."""
		return [("", "")]

	def get_lines(self) -> list[tuple[HandleFun, re.Pattern]]:
		"""Get the pairs (function, RE) to parse lines."""
		return []

	def get_words(self) -> list[tuple[HandleFun, str]]:
		"""Get the pairs (function, RE) to parse words."""
		return []


class Manager(doc.AbstractManager):

	def __init__(self,
		document: doc.Document,
		builtin_word_syntax: WordSyntax,
		builtin_line_syntax: LineSyntax,
		mon: common.Monitor = common.DEFAULT_MONITOR
	):
		self.factory = doc.Factory()
		self.builtin_word_syntax = builtin_word_syntax
		self.builtin_line_syntax = builtin_line_syntax
		self.mon = mon
		self.words_re: None|re.Pattern =  None
		self.clear(document)

	def add_completer(self, completer: CompleterFun) -> None:
		"""Add a completer, a function that will be called at the end of document
		analysis. This may be used to perform checking for example."""
		self.completers.append(completer)

	def make_par(self) -> doc.Par:
		"""Build a paragraph to be used in the document."""
		return self.factory.makePar()

	def set_info(self, id: str, info: Any) -> None:
		"""Store parsing information for third-party contributor."""
		self.info[id] = info

	def get_info(self, id: str, default: Any = None) -> Any:
		"""Get parsing information."""
		try:
			return self.info[id]
		except KeyError:
			return default

	def reset(self, document: doc.Document) -> None:
		"""Reset the parser to process a new document."""
		self.doc = document
		self.item: doc.Node = document
		self.items: list[doc.Node] = []
		self.parser: LineParser = DefaultParser()
		self.line_num = 0
		self.file_name = ""
		self.info: dict[str, Any] = {}
		self.completers: list[CompleterFun] = []

	def close_to_top(self) -> None:
		"""Close the current stack to top-level."""
		self.item = self.doc
		self.items = []

	def clear(self, document: doc.Document) -> None:
		"""Reset the parser in the initial state."""
		self.reset(document)
		self.lines = self.builtin_line_syntax
		self.words = self.builtin_word_syntax
		self.words_re = None
		self.added_lines: LineSyntax = []
		self.added_words: WordSyntax = []
		self.used_mods: list[ModuleType] = []

	def get_doc(self) -> doc.Document:
		"""Get the document currently built."""
		return self.doc

	def get_var(self, id: str, deflt: str = "") -> str:
		return self.doc.getVar(id, deflt)

	def get(self) -> doc.Node:
		"""Get the current node."""
		return self.item

	def debug(self, msg: str) -> None:
		"""Used to output message."""
		print(f"DEBUG: {msg}")

	def send(self, event: doc.Event) -> None:
		"""Send an event along the node stack."""
		if DEBUG:
			self.debug(f"send({event})")
		self.item.onEvent(self, event)

	def iter(self) -> Iterator[doc.Node]:
		"""Generate an iterator on the stack of items (from top to bottom)."""
		yield self.item
		for i in range(len(self.items) - 1, -1, -1):
			yield self.items[i]

	def top(self) -> doc.Node:
		"""Return the top item of the element stack."""
		return self.item

	def push(self, item: doc.Node) -> None:
		self.items.append(self.item)
		self.item = item
		item.setFileLine(self.file_name, self.line_num)
		if DEBUG:
			self.debug(f"push({item})")
			self.debug(f"stack = {self.items}")

	def pop(self) -> doc.Node:
		self.item.complete()
		self.item = self.items.pop()
		if DEBUG:
			self.debug(f"pop(): {self.item}")
			self.debug(f"stack = {self.items}")
		return self.item

	def forward(self, event: doc.Event) -> None:
		if DEBUG:
			self.debug(f"forward({event})")
		self.pop()
		self.send(event)

	def setParser(self, parser: LineParser) -> None:
		"""Change the parser."""
		self.parser = parser

	def getParser(self) -> LineParser:
		"""Get the current parser."""
		return self.parser

	def parseInternal(self, file: IO, name: str) -> None:
		"""Parse a text made of several lines.
		file: object iterable resulting in several lines.
		name: name of the text (for error display purpose)."""
		prev_line = self.line_num
		prev_file = self.file_name
		self.line_num = 0
		self.file_name = name
		for line in file:
			self.line_num += 1
			if line[-1] == '\n':
				line = line[0:-1]
			self.parser.parse(self, line)
		self.line_num = prev_line
		self.file_name = prev_file

	def reparse(self, text: str) -> None:
		self.parser.parse(self, text)

	def parse(self, file: str|IO, name: str = '<unknown>') -> None:
		"""Parse the given file. The file may be an input stream or
		a file name. Raise common.ParseException in case of error."""
		if isinstance(file, str):
			try:
				with open(file, encoding="utf8") as input:
					self.parse(input, file)
				return
			except OSError as e:
				raise common.ParseException(str(e))
		else:
			try:

				# manage the wiki parsing
				ext = os.path.splitext(name)[1]
				try:
					parser = PARSERS[ext]
					if parser is not None:
						self.use(parser)
				except KeyError:
					pass

				# perform the parse
				self.parseInternal(file, name)
				self.send(doc.Event(doc.L_DOC, doc.ID_END))
				for completer in self.completers:
					completer(self)

			except common.ParseException as e:
				raise common.ParseException(f"{self.get_prefix()}:{e}")

	def addLine(self, line: tuple[HandleFun, re.Pattern]) -> None:
		"""A syntax working on lines. The line parameter is pair
		(f, re) with f the function to call when the RE re is found."""
		self.added_lines.append(line)
		self.lines.append(line)

	def addWord(self, word: tuple[HandleFun, str]) -> None:
		self.added_words.append(word)
		self.words.append(word)
		self.words_re = None

	def setSyntax(self, lines: LineSyntax, words: WordSyntax) -> None:
		"""Change the main syntax with the given list of line patterns
		and the given list of word patterns."""

		# process lines
		self.lines = []
		self.lines.extend(self.builtin_line_syntax)
		self.lines.extend(self.added_lines)
		self.lines.extend(lines)

		# process words
		self.words = []
		self.words.extend(self.builtin_word_syntax)
		self.words.extend(self.added_words)
		self.words.extend(words)
		self.words_re = None

	def get_prefix(self) -> str:
		"""Generate a message prefixed with error line and file."""
		if self.file_name is not None and self.line_num is not None:
			file_name = os.path.relpath(self.file_name, os.curdir)
			return f"{file_name}:{self.line_num}: "
		else:
			return ""

	def warn(self, msg: str, *args) -> None:
		"""Display a warning with file and line."""
		self.mon.warn(self.get_prefix() + msg, *args)

	def error(self, msg: str, *args) -> None:
		"""Display an error with file and line."""
		self.mon.error(self.get_prefix() + msg, *args)

	def use(self, name: str) -> None:
		"""Use a module in the current parser."""
		assert name is not None
		if name in self.used_mods:
			return
		path = self.doc.getVar("THOT_USE_PATH")
		mod = common.loadModule(name, path)
		if mod:
			self.used_mods.append(mod)
			if "init" in mod.__dict__:
				mod.init(self)

			# new syntax?
			if "__syntax__" in mod.__dict__:
				lines = []
				words = []
				if "__lines__" in mod.__dict__:
					lines = mod.__lines__
				if "__words__" in mod.__dict__:
					words = mod.__words__
				if "__syntaxes__" in mod.__dict__:
					for s in mod.__syntaxes__:
						lines = lines + s.get_lines()
						words = words + s.get_words()
				try:
					self.factory = mod.__factory__
				except AttributeError:
					pass
				self.setSyntax(
					[(l[0], re.compile(l[1])) for l in lines],
					[(w[0], w[1]) for w in words])

			# simple extension
			else:
				if"__lines__" in  mod.__dict__:
					for line in mod.__lines__:
						self.addLine((line[0], re.compile(line[1])))
				if "__words__" in mod.__dict__:
					for word in mod.__words__:
						self.addWord((word[0], word[1]))
				if "__syntaxes__" in mod.__dict__:
					for s in mod.__syntaxes__:
						for (f, r) in s.get_lines():
							self.addLine((f, re.compile(r)))
						for w in s.get_words():
							self.addWord(w)
		else:
			self.mon.fatal(f'cannot find module {name}')

	def fix_path(self, path: str) -> str:
		"""Fix the given path if it is not absolute to be relative to the current document path."""
		if os.path.isabs(path):
			rpath = path
		elif self.file_name == '<unknown>':
			rpath = os.path.join(os.getcwd(), path)
		else:
			rpath = os.path.join(os.path.dirname(self.file_name), path)
		return rpath

	def fix_url(self, url: str) -> str:
		"""Fix given URL into a valid absolute path if relative."""
		if ":" in url:
			return url
		else:
			return self.fix_path(url)

	def parse_text(self, text: str) -> None:
		"""Perform parsing of the given text without considering to match
		them with lines."""
		handleText(self, text)

	def parse_line(self, line: str) -> None:
		"""Parse the given line as usual text line."""
		self.parser.parse(self, line)

	def push_parser(self, parser: LineParser) -> None:
		"""Push a different line parser (recalling the previous one)."""
		parser.prev = self.parser
		self.parser = parser

	def pop_parser(self) -> None:
		"""Re-install the previous parser."""
		self.parser = self.parser.prev

	def parse_block(self, block: doc.Block, parser: LineParser) -> None:
		"""Parse a block with a special parser."""
		self.push_parser(parser)
		self.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, block))

	def get_factory(self) -> doc.Factory:
		return self.factory


class BlockParser(LineParser):
	"""Deprecated. Use RawParser instead."""

	def __init__(self, man: Manager, block: doc.Block, rex: Pattern):
		self.old = man.getParser()
		man.setParser(self)
		self.block = block
		self.re: Pattern = rex
		man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, self.block))

	def parse(self, manager: Manager, line: str) -> None:
		if self.re.match(line) is not None:
			manager.setParser(self.old)
		else:
			self.block.add(line)


class RawParser(LineParser):

	def __init__(self, rex: re.Pattern):
		self.re = rex

	def parse(self, manager: Manager, line: str) -> None:
		if self.re.match(line):
			manager.pop_parser()
		else:
			top = manager.top()
			assert isinstance(top, doc.Block)
			top.add(line)
