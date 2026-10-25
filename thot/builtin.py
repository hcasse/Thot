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

"""Thot built-in syntax."""

from collections.abc import Callable
import os.path
import re

from thot import common
from thot import doc
from thot.tparser import Manager, HandleFun, WordSyntax, LineSyntax


############### Word Parsing #####################

def handleVar(man: Manager, match: re.Match) -> None:
	id = match.group('varid')
	val = man.doc.getVar(id)
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, man.factory.makeWord(val)))

def handleRef(man: Manager, match: re.Match) -> None:
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, man.factory.makeRef(match.group("ref"))))

def handleDouble(man: Manager, match: re.Match) -> None:
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word("#")))

def handle_term(man: Manager, word: re.Match) -> None:
	"""Handle a hashed word."""
	res = doc.Tag(word.group(), man.doc)
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, res))

def handleSharp(man: Manager, match: re.Match) -> None:
	handle_term(man, match.group("term"))

def handleParent(man: Manager, match: re.Match) -> None:
	handle_term(man, match.group("pterm"))

__words__: list[tuple[HandleFun, str, str]] = [
	(handleVar,
		doc.VAR_RE,
		"""use of a variable (replaced by the variable value)."""),
	(handleRef,
		r"@ref:(?P<ref>[^@]+)@",
		"""reference to a labeled element."""),
	(handleDouble,
		r"##",
		"""single '#'."""),
	(handleParent,
		r"#\((?P<pterm>[^)\s]+)\)",
		"""definition of a term."""),
	(handleSharp,
		r"#(?P<term>\w+)",
		"""reference to a defined term.""")
]
INITIAL_WORDS: WordSyntax = [(f, e) for (f, e, _) in __words__]


############### Line Parsing ######################

def handleComment(man: Manager, match: re.Match) -> None:
	pass

def handleAssign(man: Manager, match: re.Match) -> None:
	man.doc.setVar(match.group(1), match.group(2))

def handleUse(man: Manager, match: re.Match) -> None:
	name = match.group(1).strip()
	man.use(name)

def handleInclude(man: Manager, match: re.Match) -> None:
	path = match.group(1).strip()
	if not os.path.isabs(path):
		path = os.path.join(os.path.dirname(man.file_name), path)
	try:
		file = open(path, encoding="utf8")
		man.parseInternal(file, path)
	except IOError as e:
		man.error('cannot include "%s": %s',  path, e)

def handleCaption(man: Manager, match: re.Match) -> None:
	par = man.make_par()
	man.push(par)
	man.getParser().parse(man, match.group(1))
	while par != man.get():
		man.pop()
	man.pop()
	for item in man.iter():
		if item.put_caption(par):
			return
	man.error("caption unsupported here")


def handleLabel(man: Manager, match: re.Match) -> None:
	for item in man.iter():
		if item.acceptLabel():
			man.doc.addLabel(match.group(1), item)
			return
	man.warn(f'label {match.group(1)} out of any container')


__lines__: list[tuple[HandleFun, str, str]] = [
	(handleComment,
		r"^@@.*",
		"""comment."""),
	(handleAssign,
		r"^@([a-zA-Z_0-9]+)\s*=(.*)",
		"""definition of a variable."""),
	(handleUse,
		r"^@use\s+(\S+)",
		"""use of a module."""),
	(handleInclude,
		r'^@include\s+(.*)',
		"""inclusion of a THOT file."""),
	(handleCaption,
		r'^@caption\s+(.*)',
		"""assignment of a caption to the previous element."""),
	(handleLabel,
		r'^@label\s+(.*)',
		"""assignment of a label for references to the previous element.""")
]
INITIAL_LINES: LineSyntax = [(f, re.compile(e)) for (f, e, _) in __lines__]


def make_manager(document: doc.Document, mon: common.Monitor = common.DEFAULT_MONITOR) -> Manager:
	"""Make a manager with built-in syntax."""
	return Manager(document, INITIAL_WORDS, INITIAL_LINES, mon)
