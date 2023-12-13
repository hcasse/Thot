# lexicon -- lexicon support for Thot
# Copyright (C) 2018  <hugues.casse@laposte.net>
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

# Provides the following syntax:
#	@term TERM=DEFINITION
#		Definition of new term.
#	@lexicon
#		To generate the lexicon.
#	##
#		Single #.
#	#term
#		Put a link to corresponding term.
#
#	Normal text is modified when a terml is used.

import re
import sys

import thot.common as common
import thot.doc as doc

def label(s):
	"""Computes a label for the given term."""
	return "__lex_%s" % s


class LexPar(doc.Par):
	
	def __init__(self, id):
		doc.Par.__init__(self)
		self.id = id

	def gen(self, gen):
		# Don't do anything at this point.
		pass

	def numbering(self):
		return "lexicon"


class Lexicon(doc.Node):
	
	def __init__(self, map):
		doc.Node.__init__(self)
		self.map = map
		self.appendInfo(doc.INFO_CLASS, "lexicon")

	def gen_html(self, gen):
		gen.genOpenTag("dl", self, [("class", "thot-lexicon")])
		terms = list(self.map.values())
		terms.sort(key = lambda x: x.id)
		for term in terms:
			gen.genOpenTag("dt", term)
			gen.genOpenTag("a", term,
				[("id", gen.get_href(term).split("#")[1])])
			gen.genText(term.id)
			gen.genCloseTag("a")
			gen.genCloseTag("dt")
			gen.genOpenTag("dd")
			doc.Container.gen(term, gen)
			gen.genCloseTag("dd")
		gen.genCloseTag("dl")

	def gen_latex(self, gen):
		pass
	
	def gen_docbook(self, gen):
		pass
	
	def gen(self, gen):
		if gen.getType() == "html":
			self.gen_html(gen)
		else:
			common.onWarning("lexicon cannot be generated for %s" % gen.getType())


class Term(doc.Word):
	
	def __init__(self, text):
		doc.Word.__init__(self, text)
		self.appendInfo(doc.INFO_CLASS, "lexicon")

	def gen_html(self, gen):
		node = gen.doc.getLabel(label(self.text))
		href = gen.get_href(gen.doc.getLabel(label(self.text)))
		gen.genOpenTag("a", self, [("href", href)])
		doc.Word.gen(self, gen)
		gen.genCloseTag("a")
	
	def gen(self, gen):
		if gen.getType() == "html":
			self.gen_html(gen)
		else:
			common.onWarning("lexicon term cannot be generated for %s" % gen.getType())


class Source:
	
	def __init__(self):
		self.lexicon = { }

	def resolve(self, id):
		if id not in self.lexicon:
			return None
		else:
			return Term(id)

	def exists(self, id):
		"""Test if an identifier exists."""
		return id in self.lexicon

	def add(self, id, desc):
		"""Add a new term."""
		self.lexicon[id] = desc 
		

def handleTerm(man, match):
	
	# record the term
	id = match.group("termid")
	de = match.group("termdef")
	if man.lexicon.exists(id):
		common.onError(man.message("term \"%s\" already defined!" % id))
		return
	term = LexPar(id)
	man.lexicon.add(id, term)
	
	# finalize the parsing
	man.doc.addLabel(label(id), term)
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, term))
	man.reparse(de)


def handleLexicon(man, match):
	if match.group("garbage"):
		common.onWarning(man.message("garbage after lexicon!"))
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, Lexicon(man.lexicon.lexicon)))
	#man.pop()

def init(man):
	src = Source()
	man.lexicon = src
	man.doc.add_hash_source(src)

__short__ = """Generation lexicon of terms and back link to definitions."""
__description__ = __short__
__version__ = "1.0"

__lines__ = [
	(handleLexicon,
		"^@lexicon\s*(?P<garbage>.*)$",
		"generate the lexicon at this point"),
	(handleTerm,
		"^@term\s+(?P<termid>\S+)\s+(?P<termdef>.*)$",
		"create a new term and its definition")
]

__html__ = [
	("<div class=\"lexicon\"> ... </a>",
		"generated lexicon"),
	("<div> <a ...> term </a> description </div>",
		"around a term in lexicon and its definition"),
	("<a class=\"lexicon\"> term </a>",
		"around a referenced term")
]
