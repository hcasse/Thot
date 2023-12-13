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

import os.path
import re
import sys
import traceback

import thot.doc as doc
import thot.common as common

DEBUG = False

PARSERS = {
	".md": "markdown",
	".thot": None,
	".doku": "dokuwiki",
	".textile": "textile"
}


############### Word Parsing #####################

def handleVar(man, match):
	id = match.group('varid')
	val = man.doc.getVar(id)
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, man.factory.makeWord(val)))

def handleRef(man, match):
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, man.factory.makeRef(match.group("ref"))))

def handleDouble(man, match):
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word("#")))

def handle_term(man, word):
	"""Handle a hashed word."""
	#res = man.doc.resolve_hash(word)
	#if res == None:
	#	man.warn("hash term '#%s' is unknown!" % word)
	#	res = doc.Word(word)
	res = doc.Tag(word, man.doc)
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, res))

def handleSharp(man, match):
	handle_term(man, match.group("term"))

def handleParent(man, match):
	handle_term(man, match.group("pterm"))


__words__ = [
	(handleVar,
		doc.VAR_RE,
		"""use of a variable (replaced by the variable value)."""),
	(handleRef,
		"@ref:(?P<ref>[^@]+)@",
		"""reference to a labeled element."""),
	(handleDouble,
		"##",
		"""single '#'."""),
	(handleParent,
		"#\((?P<pterm>[^)\s]+)\)",
		"""definition of a term."""),
	(handleSharp,
		"#(?P<term>\w+)",
		"""reference to a defined term.""")
]
INITIAL_WORDS = [(f, e) for (f, e, _) in __words__]

def handleText(man, line, suffix = ' '):

	# init RE_WORDS
	if man.words_re == None:
		text = ""
		i = 0
		for (fun, wre) in man.words:
			if text != "":
				text = text + "|"
			text = text + "(?P<a" + str(i) + ">" + wre + ")"
			i = i + 1
		man.words_re = re.compile(text)

	# look in line
	match = man.words_re.search(line)
	while match:
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


############### Line Parsing ######################

def handleComment(man, match):
	pass

def handleAssign(man, match):
	man.doc.setVar(match.group(1), match.group(2))

def handleUse(man, match):
	name = match.group(1).strip()
	man.use(name)

def handleInclude(man, match):
	path = match.group(1).strip()
	if not os.path.isabs(path):
		path = os.path.join(os.path.dirname(man.file_name), path)
	try:
		file = open(path)
		man.parseInternal(file, path)
	except IOError as e:
		man.error('cannot include "%s": %s',  path, e)

def handleCaption(man, match):
	par = man.make_par()
	man.push(par)
	man.getParser().parse(man, match.group(1))
	while par != man.get():
		man.pop()
	man.pop()
	for item in man.iter():
		if item.setCaption(par):
			return
	raise common.ParseException("caption unsupported here")


def handleLabel(man, match):
	for item in man.iter():
		if item.acceptLabel():
			man.doc.addLabel(match.group(1), item)
			return
	ma.warn('label %s out of any container', match.group(1))


__lines__ = [
	(handleComment,
		"^@@.*",
		"""comment."""),
	(handleAssign,
		"^@([a-zA-Z_0-9]+)\s*=(.*)",
		"""definition of a variable."""),
	(handleUse,
		"^@use\s+(\S+)",
		"""use of a module."""),
	(handleInclude,
		'^@include\s+(.*)',
		"""inclusion of a THOT file."""),
	(handleCaption,
		'^@caption\s+(.*)',
		"""assignment of a caption to the previous element."""),
	(handleLabel,
		'^@label\s+(.*)',
		"""assignment of a label for references to the previous element.""")
]
INITIAL_LINES = [(f, re.compile(e)) for (f, e, _) in __lines__]


class LineParser:
	"""Abstract class of line parser."""

	def parse(self, manager, line):
		"""Parse the given line using the given manager."""
		pass


class DefaultParser(LineParser):
	"""Default parser that tries to parser the line with the manager
	recorded lines. Else scan the text with the manager recorded words."""

	def parse(self, handler, line):
		line = handler.doc.reduceVars(line)
		done = False
		for (fun, re) in handler.lines:
			match = re.match(line)
			if match:
				fun(handler, match)
				done = True
				break
		if not done:
			handleText(handler, line)


class Syntax:
	"""Base class of all syntaxes added to the parser."""

	def get_doc(self):
		"""Get the documentation for the syntax, a sequence of pairs
		(RE, description) where RE is a pseudo-regular expression
		describing the syntax and description is the descritpion of the
		syntax (possibly multi-line)."""
		return [("", "")]

	def get_lines(self):
		"""Get the pairs (function, RE) to parse lines."""
		return []

	def get_words(self):
		"""Get the pairs (function, RE) to parse words."""
		return []


class Manager:

	def __init__(self, document, mon = common.DEFAULT_MONITOR):
		self.factory = doc.Factory()
		self.mon = mon
		self.clear(document)

	def add_completer(self, completer):
		"""Add a completer, a function that will be called at the end of document analysis. This may be used to perform checking for example."""
		self.completers.append(completer)

	def make_par(self):
		"""Build a paragraph to be used in the document."""
		return self.factory.makePar()

	def set_info(self, id, info):
		"""Store parsing information for third-party contributor."""
		self.info[id] = info

	def get_info(self, id, default = None):
		"""Get parsing information."""
		try:
			return self.info[id]
		except KeyError:
			return default

	def reset(self, document):
		"""Reset the parser to process a new document."""
		self.doc = document
		self.item = document
		self.items = []
		self.parser = DefaultParser()
		self.line_num = None
		self.file_name = None
		self.info = {}
		self.completers = []

	def clear(self, document = None):
		"""Reset the parser in the initial state."""
		self.reset(document)
		words_re = None
		self.lines = INITIAL_LINES
		self.words = INITIAL_WORDS
		self.words_re = None
		self.added_lines = []
		self.added_words = []
		self.used_mods = []		

	def get_doc(self):
		"""Get the document currently built."""
		return self.doc
	
	def get_var(self, id, deflt = ""):
		return self.doc.getVar(id, deflt)

	def get(self):
		"""Get the current node."""
		return self.item

	def debug(self, msg):
		"""Used to output message."""
		print("DEBUG: %s" % msg)

	def send(self, event):
		"""Send an event along the node stack."""
		if DEBUG:
			self.debug("send(%s)" % event) 
		self.item.onEvent(self, event)

	def iter(self):
		"""Generate an iterator on the stack of items (from top to bottom)."""
		yield self.item
		for i in xrange(len(self.items) - 1, -1, -1):
			yield self.items[i]
	
	def top(self):
		"""Return the top item of the element stack."""
		return self.item
	
	def push(self, item):
		self.items.append(self.item)
		self.item = item
		item.setFileLine(self.file_name, self.line_num)
		if DEBUG:
			self.debug("push(%s)" % item)
			self.debug("stack = %s" % self.items)

	def pop(self):
		self.item.complete()
		self.item = self.items.pop()
		if DEBUG:
			self.debug("pop(): %s" % self.item)
			self.debug("stack = %s" % self.items)		

	def forward(self, event):
		if DEBUG:
			self.debug("forward(%s)" % event)
		self.pop()
		self.send(event)

	def setParser(self, parser):
		"""Change the parser."""
		self.parser = parser

	def getParser(self):
		"""Get the current parser."""
		return self.parser

	def parseInternal(self, file, name):
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

	def reparse(self, str):
		self.parser.parse(self, str)

	def parse(self, file, name = '<unknown>'):
		"""Parse the given file. The file may be an input stream or
		a file name. Raise common.ParseException in case of error."""
		if isinstance(file, str):
			try:
				with open(file) as input:
					self.parse(input, file)
				return
			except OSError as e:
				raise common.ParseException(str(e))				
		else:
			try:

				# manage the wiki parsing
				ext = os.path.splitext(name)[1]
				mod = PARSERS[ext]
				if mod != None:
					self.use(mod)

				# perform the parse
				self.parseInternal(file, name)
				self.send(doc.Event(doc.L_DOC, doc.ID_END))
				for completer in self.completers:
					completer(self)

			except common.ParseException as e:
				raise common.ParseException(self.message(e))

	def addLine(self, line):
		"""A syntax working on lines. The line parameter is pair
		(f, re) with f the function to call when the RE re is found."""
		self.added_lines.append(line)
		self.lines.append(line)

	def addWord(self, word):
		self.added_words.append(word)
		self.words.append(word)
		self.words_re = None

	def setSyntax(self, lines, words):
		"""Change the main syntax with the given list of line patterns
		and the given list of word patterns."""

		# process lines
		self.lines = []
		self.lines.extend(INITIAL_LINES)
		self.lines.extend(self.added_lines)
		self.lines.extend(lines)

		# process words
		self.words = []
		self.words.extend(INITIAL_WORDS)
		self.words.extend(self.added_words)
		self.words.extend(words)
		self.words_re = None

	def get_prefix(self):
		"""Generate a message prefixed with error line and file."""
		if self.file_name != None and self.line_num != None:
			file_name = os.path.relpath(self.file_name, os.curdir)
			return "%s:%d: " % (file_name, self.line_num)
		else:
			return ""

	def info(self, msg, *args):
		"""Display an information message."""
		self.mon.info(self.get_prefix() + msg, *args)

	def warn(self, msg, *args):
		"""Display a warning with file and line."""
		self.mon.warn(self.get_prefix() + msg, *args)

	def error(self, msg, *args):
		"""Display an error with file and line."""
		self.mon.error(self.get_prefix() + msg, *args)

	def use(self, name):
		"""Use a module in the current parser."""
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
			self.mon.fatal('cannot find module %s' % name)

	def fix_path(self, path):
		"""Fix the given path if it is not absolute to be relative to the current document path."""
		if os.path.isabs(path):
			rpath = path
		elif self.file_name == '<unknown>':
			rpath = os.path.join(os.getcwd(), path)
		else:
			rpath = os.path.join(os.path.dirname(self.file_name), path)
		return rpath

	def fix_url(self, url):
		"""Fix given URL into a valid absolute path if relative."""
		if ":" in url:
			return url
		else:
			return self.fix_path(url)

	def parse_text(self, text):
		"""Perform parsing of the given text without considering to match
		them with lines."""
		handleText(self, text)

	def parse_line(self, line):
		"""Parse the given line as usual text line."""
		self.parser.parse(self, line)


class BlockParser(LineParser):
	old = None
	block = None
	re = None

	def __init__(self, man, block, re):
		self.old = man.getParser()
		man.setParser(self)
		self.block = block
		self.re = re
		man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, self.block))

	def parse(self, man, line):
		if self.re.match(line):
			man.setParser(self.old)
		else:
			self.block.add(line)


	
