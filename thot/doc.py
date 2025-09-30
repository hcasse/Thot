# thot.doc -- Thot document description module
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

"""Base classes of Thot document representation."""

import re
import sys

from thot import common

INDENT = "  "

# levels
L_DOC=0
L_HEAD=1
L_PAR=2
L_WORD=3
LEVELS = ["DOC", "HEAD", "PAR", "WORD"]

# identifiers
ID_NEW = "new"				# ObjectEvent for L_HEAD
ID_END = "end"

ID_TITLE = "title"

ID_NEW_ITEM = "new_item"	# ItemEvent
ID_END_ITEM = "end_item"
ID_NEW_DEF  = "new_def"		# definition event
ID_END_TERM = "end term"
ID_END_DEF  = "end_def"

ID_NEW_TAB = "new_tab"
ID_END_TAB = "end_tab"
ID_NEW_ROW = "new_row"
ID_END_ROW = "end_row"
ID_NEW_CELL = "new_cell"
ID_END_CELL = "end_cell"

ID_NEW_STYLE = "new_style"	# TypedEvent
ID_END_STYLE = "end_style"	# TypedEvent

ID_NEW_LINK = "new_link"	# ObjectEvent
ID_END_LINK = "end_link"

ID_NEW_QUOTE = "new_quote"
ID_END_QUOTE = "end_quote"

ID_NUM_HEADER = "header"
ID_NUM_TABLE = "table"
ID_NUM_FIGURE = "figure"
ID_NUM_LISTING = "listing"

ID_EMBED_RAW = "raw"
ID_EMBED_FILE = "file"
ID_EMBED_CODE = "code"
ID_EMBED_DOT = "dot"
ID_EMBED_GNUPLOT = "gnuplot"

ID_CUSTOMIZE = "customize"


# variable reduction
VAR_RE = r"@\((?P<varid>[a-zA-Z_0-9]+)\)"
VAR_REC = re.compile(VAR_RE)


# alignment
ALIGN_NONE = 0
ALIGN_LEFT = 1
ALIGN_CENTER = 2
ALIGN_RIGHT = 3
ALIGN_JUSTIFY = 4
ALIGN_TOP = 1
ALIGN_BOTTOM = 3


# standard styles
STYLE_BOLD = "bold"
STYLE_STRONG = "strong"
STYLE_ITALIC = "italic"
STYLE_EMPHASIZED = "emphasized"
STYLE_MONOSPACE = "monospace"
STYLE_UNDERLINE = "underline"
STYLE_SUBSCRIPT = "subscript"
STYLE_SUPERSCRIPT = "superscript"
STYLE_STRIKE = "strike"
STYLE_BIGGER = "bigger"
STYLE_SMALLER = "smaller"
STYLE_CITE = "cite"
STYLE_CODE = "code"
STYLE_FOOTNOTE = "footnote"
STYLE_STRONG_EMPH = "strong-emph"

# standard footnote
FOOTNOTE_EMBED = "embed"
FOOTNOTE_REF = "ref"
FOOTNOTE_DEF = "def"

# standard lists
LIST_ITEM = "ul"
LIST_NUMBER = "ol"


# external optional information
#	Back-end are free to use the information attributes.
INFO_CLASS = "thot:class"				# string (class in CSS)
INFO_CSS = "thot:css"					# string (CSS code)
INFO_ALIGN = "thot:align"				# one of ALIGN_LEFT, ALIGN_CENTER or ALIGN_RIGHT
INFO_VALIGN = "thot:valign"				# one of ALIGN_TOP, ALIGN_CENTER or ALIGN_BOTTOM
INFO_ID = "thot:id"						# string (id in XML format)
INFO_LANG = "thot:lang"					# ISO 639-1 language code
INFO_LEFT_PAD = "thot:left_pad"			# real (number of 1 em)
INFO_RIGHT_PAD = "thot:right_pad"		# real (number of 1 em)
INFO_HSPAN = "thot:hspan"				# integer (number of cells)
INFO_VSPAN = "thot:vspan"				# integer (number of cells)
INFO_PERCENT_SIZE = "thot:percent_size"	# real (percent)
INFO_WIDTH = "thot:width"				# integer (pixels)
INFO_HEIGHT = "thot:height"				# integer (pixels)
INFO_CAPTION = "thot:caption"			# formatted text
INFO_NUMBER = "thot:number"				# number for a node (header, figure, etc)


# supported events
class Event:
	"""Base class of all events."""
	level = None
	id = None

	def __init__(self, level, id):
		"""Build a new event with level and id."""
		self.level = level
		self.id = id

	def make(self):
		"""Make an object matching the event."""
		return None

	def make_ext(self, man):
		"""Extended version of make() to support manager as argument.
		Default implemtation call simply make()."""
		return self.make()

	def __str__(self):
		return "event(" + LEVELS[self.level] + ", " + self.id + ")"


class ObjectEvent(Event):
	"""Event carrying an object to make."""
	object = None

	def __init__(self, level, id, object):
		Event.__init__(self, level, id)
		self.object = object

	def make(self):
		return self.object

	def __str__(self):
		return f"event({LEVELS[self.level]}, {self.id}, {self.object})"


class TypedEvent(Event):
	"""Event containing a type."""
	type = None

	def __init__(self, level, id, type):
		Event.__init__(self, level, id)
		self.type = type


class StyleEvent(TypedEvent):
	"""Event for a simple style."""

	def __init__(self, type):
		TypedEvent.__init__(self, L_WORD, ID_NEW_STYLE, type)

	def make(self):
		return Style(self.type)


class OpenStyleEvent(TypedEvent):
	"""Event for an open/close style."""

	def __init__(self, type):
		TypedEvent.__init__(self, L_WORD, ID_NEW_STYLE, type)

	def make(self):
		return OpenStyle(self.type)


class CloseEvent(TypedEvent):
	"""An event for a closing tag."""

	def __init__(self, level, id, type):
		TypedEvent.__init__(self, level, id, type)

	def make(self):
		raise common.ParseException(self.type + " closed but not opened !")


class CloseStyleEvent(CloseEvent):
	"""Event for an open/close style."""

	def __init__(self, type):
		CloseEvent.__init__(self, L_WORD, ID_END_STYLE, type)


class ItemEvent(TypedEvent):
	"""Event for list item."""
	depth = None

	def __init__(self, type, depth):
		TypedEvent.__init__(self, L_PAR, ID_NEW_ITEM, type)
		self.depth = depth

	def make(self):
		return List(self.type, self.depth)


class DefEvent(Event):
	"""Event for list definition."""

	def __init__(self, id = ID_NEW_DEF, depth = -1):
		Event.__init__(self, L_PAR, id)
		self.depth = depth

	def make_ext(self, man):
		list = man.factory.makeDefList(self.depth)
		list.add_item(man.factory.makeDefItem())
		return list


class QuoteEvent(Event):
	"""An event designing a quoted text."""
	depth = None

	def __init__(self, depth, begin = True):
		Event.__init__(self, L_PAR,
			ID_NEW_QUOTE if begin else ID_END_QUOTE)
		self.depth = depth

	def make(self):
		return Quote(self.depth)


class CustomizeEvent(Event):
	"""Event to customize some already created object. Its function
	is applied to the first found object of the given type if the
	match function returns true."""

	def __init__(self, level, id = ID_CUSTOMIZE):
		Event.__init__(self, level, id)

	def matches(self, object):
		"""Called to check if the given object matches.
		Default implementation returns true."""
		return True

	def process(self, object):
		"""Called to let the event process the current object."""
		pass



class Info:
	LABELS = "thot:labels"

	info = None

	def setInfo(self, id, val):
		"""Deprecated."""
		self.set_info(id, val)

	def set_info(self, id, val):
		"""Set an information value."""
		if not self.info:
			self.info = { }
		self.info[id] = val

	def appendInfo(self, id, val):
		"""Append the given value to identifier with identifier processed as a list."""
		if not self.info:
			self.info = { }
		try:
			self.info[id].append(val)
		except KeyError:
			self.info[id] = [ val ]

	def getInfo(self, id, dflt = None):
		"""Deprecated."""
		return self.get_info(id, dflt)

	def get_info(self, id, dflt = None):
		"""Get an information value. None if it not defined."""
		if not self.info:
			return None
		try:
			return self.info[id]
		except KeyError:
			return dflt

	def mergeInfo(self, info):
		"""Merge the given information with the current one."""
		if info.info:
			for k in info.info.keys():
				self.setInfo(k, info.info[k])


# nodes
class Node(Info):
	"""Base definition of document nodes.

	Each time an event is passed to the Node tree, the function onEvent()
	is called."""
	file = None
	line = None

	def __init__(self):
		pass

	def setFileLine(self, file, line):
		"""Set file/line information corresponding to the node."""
		if self.file is None:
			self.file = file
			self.line = line

	def getFileLine(self):
		"""Get formatted version of file/line (useful for message display)."""
		return f"{self.file}:{self.line}"

	def onError(self, msg):
		"""Called to display an error."""
		common.onError(f'{self.file}:{self.line}: {msg}')

	def onWarning(self, msg):
		"""Called to display a warning."""
		common.onWarning(f'{self.file}:{self.line}: {msg}')

	def onInfo(self, msg):
		"""Called to display an information to the user."""
		common.onInfo(f'{self.file}:{self.line}: {msg}')

	def onEvent(self, man, event):
		"""Called each time a new word is found.
		man -- current parser manager
		event -- current event."""
		if isinstance(event, CustomizeEvent) and event.matches(man.top()):
			event.process(man.top())
		else:
			man.forward(event)

	def isEmpty(self):
		"""Test if the node is empty (and can be removed)."""
		return False

	def dump(self, out=sys.stdout, tab=""):
		"""Output the given node to the output stream with tab indentation."""
		pass

	def getHeaderLevel(self):
		"""For a header node, get the level."""
		return -1

	def genTitle(self, gen):
		"""generate the title for a header node."""
		return None

	def getContent(self):
		"""Get the sub-nodes of the current nodes."""
		return []

	def gen(self, gen):
		"""Method to perform document generation.
		gen -- used generator."""
		pass

	def acceptLabel(self):
		"""Method called called when a label is found. Nodes not supporting
		just return False (default behaviour) else node return True."""
		return False

	def visit(self, visitor):
		"""Visit the current node, that is, call the method in
		visitor that matches the node."""
		pass

	def numbering(self):
		"""Return the group of numbering the node belongs to.
		Return None if there is no numbering (default).
		Level (0 is higher) for header numbering, "figure" pour image and the like,
		"listing" for code, etc."""
		return None

	def toText(self):
		"""Produce only the raw text of the node."""
		return ""

	def get_width(self):
		return self.get_info(INFO_WIDTH)

	def get_height(self):
		return self.get_info(INFO_HEIGHT)

	def get_align(self):
		return self.get_info(INFO_ALIGN)

	def get_caption(self):
		"""Return the associated caption. return none if there is no caption."""
		return self.get_info(INFO_CAPTION)

	def set_caption(self, caption):
		"""Set the caption of the node."""
		self.set_info(INFO_CAPTION, caption)

	def put_caption(self, caption):
		"""Called by the parser to put a caption on this. Return True if the
		caption is supported, False else (default implementation)."""
		return False

	def complete(self):
		"""Called when the node is popped from the document stack."""
		pass

	def aggregate(self, man, node):
		"""Called by the container when it adds a new node after the
		current one to let, for example, lists to aggregates.
		Must return True is aggregation arises. This function is
		allowed to update the stack."""
		return False

	def set_number(self, number):
		"""Record number for the node."""
		self.set_info(INFO_NUMBER, number)

	def get_number(self):
		"""Get the number associated with a node. Return None if there is no number."""
		return self.get_info(INFO_NUMBER)

	def get_labels(self):
		"""Get the list of labels, if any, for the node.
		Return [] if there is no label."""
		return self.get_info(Info.LABELS, [])


class Container(Node):
	"""A container is an item containing other items."""
	content = None

	def __init__(self, content = None):
		Node.__init__(self)
		if content is not None:
			self.content = content
		else:
			self.content = []

	def check_last(self):
		if self.content != [] and self.content[-1].isEmpty():
			del self.content[-1]

	def add(self, man, item):
		self.check_last()
		if self.content != []:
			if self.content[-1].aggregate(man, item):
				return
		if item is not None:
			self.content.append(item)
			man.push(item)

	def complete(self):
		self.check_last()

	def remove(self, item):
		"""Remove an item from the container."""
		self.content.remove(item)

	def append(self, item):
		"""Add child without refering to the parsing."""
		self.content.append(item)

	def last(self):
		return self.content[-1]

	def isEmpty(self):
		return self.content == []

	def dumpHead(self, out, tab):
		pass

	def dump(self, out=sys.stdout, tab=""):
		self.dumpHead(out, tab)
		for item in self.content:
			item.dump(out, tab + INDENT)
		out.write(tab + ")\n")

	def getContent(self):
		return self.content

	def gen(self, gen):
		for item in self.content:
			item.gen(gen)

	def toText(self):
		r = ""
		for item in self.content:
			r = r + item.toText()
		return r

	def clear(self):
		"""Clear all items of the container."""
		self.content = []

	def move_content(self, target):
		"""Move target from on container to target container."""
		target.content = self.content
		self.content = []


# Word family
class Word(Node):
	text = None

	def __init__(self, text):
		Node.__init__(self)
		self.text = text

	def dump(self, out=sys.stdout, tab=""):
		out.write(f"{tab}{self}\n")

	def gen(self, gen):
		gen.genText(self.text)

	def __str__(self):
		return f"word({self.text})"

	def visit(self, visitor):
		visitor.onWord(self)

	def toText(self):
		return self.text

	def __str__(self):
		return self.text


class Ref(Node):
	label = None

	def __init__(self, label):
		Node.__init__(self)
		self.label = label

	def dump(self, out=sys.stdout, tab=""):
		out.write(f"{tab}ref({self.label})\n")

	def gen(self, gen):
		gen.genRef(self)

	def __str__(self):
		return f"ref({self.label})"

	def visit(self, visitor):
		visitor.onRef(self)


class Tag(Node):

	def __init__(self, tag, doc):
		Node.__init__(self)
		self.tag = tag
		self.doc = doc

	def gen(self, gen):
		v = self.doc.resolve_hash(self.tag)
		if v is not None:
			v.gen(gen)
		else:
			gen.genText(self.tag)

	def dump(self, out=sys.stdout, tab=""):
		out.write(f"{tab}tag({self.tag})\n")

	def __str__(self):
		return f"tag({self.tag})"

	def visit(self, visitor):
		visitor.onTag(self)


class Image(Node):
	path = None

	def __init__(self, path, width = None, height = None, caption = None):
		Node.__init__(self)
		self.path = path
		if width:
			self.set_info(INFO_WIDTH, width)
		if height:
			self.set_info(INFO_HEIGHT, height)
		if caption:
			self.set_caption(caption)

	def dump(self, out=sys.stdout, tab=""):
		out.write(f"{tab}image({self.path}, {self.get_width()}, " +
			f"{self.get_height()}, {self.get_caption()})\n")

	def gen(self, gen):
		gen.genImage(self.path, self, self.get_caption())

	def visit(self, visitor):
		visitor.onImage(self)

	def accepts_caption(self):
		return True


class Glyph(Node):
	code = None

	def __init__(self, code):
		Node.__init__(self)
		self.code = code

	def dump(self, out=sys.stdout, tab=""):
		out.write(f"{tab}glyph({hex(self.code)})\n")

	def gen(self, gen):
		gen.genGlyph(self.code)

	def visit(self, visitor):
		visitor.onGlyph(self)


class LineBreak(Node):
	"""Represents a line-break in the paragraph flow."""

	def __init__(self):
		Node.__init__(self)

	def dump(self, out=sys.stdout, tab=""):
		print(f"{tab}line-break\n")

	def gen(self, gen):
		gen.gen_line_break()


# Style family
class Style(Container):
	style = None

	def __init__(self, style):
		Container.__init__(self)
		self.style = style

	def onEvent(self, man, event):
		if event.level is not L_WORD:
			man.forward(event)
		elif event.id is not ID_NEW_STYLE:
			self.add(man, event.make_ext(man))
		elif event.type == self.style:
			man.pop()
		else:
			self.add(man, event.make_ext(man))

	def dumpHead(self, out, tab):
		out.write(tab + "style(" + self.style + ",\n")

	def gen(self, gen):
		gen.genStyleBegin(self.style)
		Container.gen(self, gen)
		gen.genStyleEnd(self.style)

	def visit(self, visitor):
		visitor.onStyle(self)


class OpenStyle(Container):
	style = None

	def __init__(self, style):
		Container.__init__(self)
		self.style = style

	def onEvent(self, man, event):
		if event.level is not L_WORD:
			man.forward(event)
		elif event.id is not ID_END_STYLE:
			self.add(man, event.make_ext(man))
		elif event.type == self.style:
			man.pop()
		else:
			raise Exception("closing style without opening")

	def dumpHead(self, out, tab):
		out.write(tab + "style(" + self.style + ",\n")

	def gen(self, gen):
		gen.genStyleBegin(self.style)
		Container.gen(self, gen)
		gen.genStyleEnd(self.style)

	def visit(self, visitor):
		visitor.onStyle(self)


class FootNote(OpenStyle):
	"""A foot note. There a 3 kinds of note:
	* FOOTNOTE_EMBEDDED -- the note content is embedded in the text and the number
		automatically generated.
	* FOOTNOTE_REF -- only the note reference is given and the note content will
		be provided thereafter.
	* FOOTNOTE_DEF -- provide the content of a foot note whose reference is given
		by FOOTNOTE_REF.
	"""
	kind = None
	id = None		# footnote identifier as displayed to the user
	ref = None		# footnote identifier as used in the links

	def __init__(self, kind = FOOTNOTE_EMBED, ref = None, id = None):
		OpenStyle.__init__(self, 'footnote')
		self.kind = kind
		if not id:
			id = ref
		self.ref = ref
		self.id = id

	def dumpHead(self, out, tab):
		if self.kind == FOOTNOTE_EMBED:
			out.write(f'{tab}footnote(\n')
		else:
			out.write(f'{tab}footnote#{self.ref}(\n')

	def isEmpty(self):
		return False

	def gen(self, gen):
		gen.genFootNote(self)

	def visit(self, visitor):
		visitor.onFootNote(self)

	def toText(self):
		return ""


class Link(Container):
	"""A link in a text."""
	ref = None

	def __init__(self, ref, title = None):
		Container.__init__(self)
		self.ref = ref
		self.title = title

	def onEvent(self, man, event):
		if event.level is not L_WORD:
			man.forward(event)
		elif event.id is ID_END_LINK:
			man.pop()
		else:
			self.add(man, event.make_ext(man))

	def dumpHead(self, out, tab):
		out.write(f"{tab}link(\"{self.ref}\",\n")

	def gen(self, gen):
		gen.genLinkBegin(self.ref, self.title)
		Container.gen(self, gen)
		gen.genLinkEnd(self.ref)

	def visit(self, visitor):
		visitor.onLink(self)


# Par family
class Par(Container):

	def __init__(self, content = None):
		Container.__init__(self, content)

	def onEvent(self, man, event):
		if event.level is L_WORD:
			self.add(man, event.make_ext(man))
		else:
			man.forward(event)

	def dumpHead(self, out, tab):
		out.write(tab + "par(\n")

	def gen_content(self, gen):
		"""Generate the content of the paragraph."""
		Container.gen(self, gen)

	def gen(self, gen):
		gen.genParBegin()
		self.gen_content(gen)
		gen.genParEnd()

	def visit(self, visitor):
		visitor.onPar(self)

	def __str__(self):
		return f"par({' '.join(str(x) for x in self.getContent())})"


class Quote(Par):
	"""A quoted paragraph."""

	def __init__(self, depth):
		Par.__init__(self)
		self.depth = depth

	def onEvent(self, man, event):
		if event.id is ID_END_QUOTE:
			man.pop()
		elif event.id is ID_NEW_QUOTE:
			if event.depth == self.depth:
				pass
			else:
				man.forward(event)
		else:
			Par.onEvent(self, man, event)

	def dumpHead(self, out, tab):
		out.write(f"{tab}quote:{self.depth}(\n")

	def gen(self, gen):
		gen.genQuoteBegin(self.depth)
		Container.gen(self, gen)
		gen.genQuoteEnd(self.depth)

	def visit(self, visitor):
		visitor.onQuote(self)


class Embedded(Node):
	"""Class representing document part not part of the main
	text like figures, listing, tables, etc.
	It defines mainly a label."""

	def __init__(self):
		Node.__init__(self)

	def acceptLabel(self):
		return True

	def visit(self, visitor):
		visitor.onEmbedded(self)

	def getKind(self):
		"""Get the kind of embed object."""
		return "none"

	def numbering(self):
		return "figure"

	def put_caption(self, text):
		self.set_caption(text)
		return True


class Block(Embedded):

	def __init__(self, kind):
		Embedded.__init__(self)
		self.kind = kind
		self.content = []

	def get_kind(self):
		"""Get the kind of the block."""
		return self.kind

	def get_lines(self):
		"""Get the lines inside the block."""
		return self.content

	def add(self, line):
		self.content.append(line)

	def dumpHead(self, out, tab):
		out.write(f"{tab}{self.kind}(\n")

	def dump(self, out=sys.stdout, tab=""):
		self.dumpHead(out, tab)
		for line in self.content:
			out.write(tab + "  " + line + "\n")
		out.write(tab + ")\n")

	def isEmpty(self):
		return False

	def toText(self):
		"""Get the content as single text."""
		text = ''
		for line in self.content:
			text += line + '\n'
		return text

	def put_caption(self, text):
		self.set_caption(text)
		return True


class Figure(Block):
	path = None

	def __init__(self, path, width = None, height = None, caption = None, align = ALIGN_NONE):
		Block.__init__(self, "figure")
		self.path = path
		if width:
			self.setInfo(INFO_WIDTH, width)
		if height:
			self.setInfo(INFO_HEIGHT, height)
		if align:
			self.setInfo(INFO_ALIGN, align)
		if caption:
			self.set_caption(caption)

	def dump(self, out=sys.stdout, tab=""):
		caption = ""
		if self.get_caption() is not None:
			caption = self.get_caption().toText()
		out.write(f"{tab}figure({self.path}, {caption})\n")

	def gen(self, gen):
		gen.genFigure(self.path, self, self.get_caption())

	def visit(self, visitor):
		visitor.onEmbeddedImage(self)

	def numbering(self):
		return "figure"

	def acceptLabel(self):
		return True

	def put_caption(self, text):
		self.set_caption(text)
		return True


# List family
class ListItem(Container):
	"""Description of a list item."""

	def __init__(self):
		Container.__init__(self)
		self.content.append(Par())

	def dumpHead(self,out,  tab):
		out.write(tab + "item(\n")

	def visit(self, visitor):
		visitor.onListItem(self)


class List(Container):
	"""Description of any kind of list (numbered, unnumbered)."""
	kind = None
	depth = None

	def __init__(self, kind, depth):
		Container.__init__(self)
		self.kind = kind
		self.depth = depth

	def onEvent(self, man, event):
		if event.level is L_WORD:
			if self.isEmpty():
				self.content.append(ListItem())
				self.last().content.append(man.make_par())
			self.last().last().add(man, event.make_ext(man))
		elif event.id is ID_NEW_ITEM:
			if event.depth < self.depth:
				man.forward(event)
			elif event.depth > self.depth:
				self.last().add(man, event.make_ext(man))
			elif self.kind == event.type:
				self.content.append(ListItem())
			else:
				man.forward(event)
		elif event.id is ID_END_ITEM:
			man.pop()
		else:
			man.forward(event)

	def dumpHead(self, out, tab):
		out.write(tab + "list(" + self.kind + "," + str(self.depth) + ",\n")

	def getItems(self):
		"""Get the list of items in the list."""
		return self.content

	def gen(self, gen):
		gen.genList(self)

	def visit(self, visitor):
		visitor.onList(self)


class DefItem(Node):
	"""Description of a definition list item."""

	def __init__(self, term, body):
		Node.__init__(self)
		self.term = term
		self.body = body

	def get_term(self):
		"""Get the defined term as a container of text-level items."""
		return self.term

	def get_body(self):
		"""Get the body of the definition."""
		return self.body

	def get_def(self):
		"""Deprecated."""
		return self.get_body()

	def dump(self, out=sys.stdout, tab=""):
		out.write(tab + "item(\n")
		self.term.dump(out, tab + INDENT)
		out.write(tab + ',\n')
		self.body.dump(out, tab + INDENT)
		out.write(tab + ')\n')

	def visit(self, visitor):
		visitor.onDefItem(self)

	def isEmpty(self):
		return False

	def gen_term(self, gen):
		"""Generate the definition term content."""
		for item in self.term.getContent():
			item.gen(gen)

	def gen_body(self, gen):
		"""Generate the definition body content."""
		for item in self.body.getContent():
			item.gen(gen)


class DefList(Container):
	"""Description of definition list."""
	depth = None

	def __init__(self, depth):
		Container.__init__(self)
		self.depth = depth

	def onEvent(self, man, event):
		if event.level is L_WORD:
			man.push(self.last().get_term())
			man.send(event)
		elif event.id is ID_END_TERM:
			man.push(self.last().get_body())
		elif event.id is ID_NEW_DEF:
			if event.depth < self.depth:
				man.forward(event)
			elif event.depth > self.depth:
				self.last().add(man, event.make_ext(man))
			else:
				item = man.factory.makeDefItem()
				self.add_item(item)
				man.push(item.get_term())
		elif event.id is ID_END_DEF:
			man.pop()
		else:
			man.forward(event)

	def add_item(self, item):
		"""Add a DefItem to the list."""
		self.content.append(item)

	def dumpHead(self, out, tab):
		out.write(tab + "deflist(" + str(self.depth) + ",\n")

	def getItems(self):
		"""Get the list of items in the list."""
		return self.content

	def gen(self, gen):
		gen.genDefList(self)
		pass

	def visit(self, visitor):
		visitor.onDefList(self)


# Table
TAB_CENTER = 0
TAB_LEFT = -1
TAB_RIGHT = 1
TAB_NORMAL = 0
TAB_HEADER = 1

TABLE_KINDS = [ 'normal', 'header' ]
TABLE_ALIGNS = [ 'left', 'center', 'right' ]

class Cell(Par):
	kind = None

	def __init__(self, kind, align = None, span = None, vspan = None):
		Par.__init__(self)
		self.kind = kind
		if align:
			self.setInfo(INFO_ALIGN, align)
		if span:
			self.setInfo(INFO_HSPAN, span)
		if vspan:
			self.setInfo(INFO_VSPAN, vspan)

	def set_align(self, align):
		"""Set the alignment of the cell."""
		self.set_info(INFO_ALIGN, align)

	def get_align(self):
		return self.get_info(INFO_ALIGN, TAB_CENTER)

	def get_hspan(self):
		return self.get_info(INFO_HSPAN, 1)

	def get_vspan(self):
		return self.get_info(INFO_VSPAN, 1)

	def isEmpty(self):
		return False

	def dumpHead(self, out, tab):
		s = tab + 'cell(' + TABLE_KINDS[self.kind]
		align = self.getInfo(INFO_ALIGN)
		if align is not None:
			s += f", align={TABLE_ALIGNS[align + 1]}"
		hspan = self.getInfo(INFO_HSPAN)
		if hspan is not None:
			s += f", hspan={hspan}"
		vspan = self.getInfo(INFO_VSPAN)
		if vspan is not None:
			s += f", vspan={vspan}"
		out.write(s + "\n")

	def gen(self, gen):
		Container.gen(self, gen)

	def visit(self, visitor):
		visitor.onCell(self)

	def __str__(self):
		return f"cell({Par.__str__(self)})"


class Row(Container):
	kind = None

	def __init__(self, kind):
		Container.__init__(self)
		self.kind = kind

	def onEvent(self, man, event):
		if event.id is ID_NEW_CELL:
			self.add(man, event.make_ext(man))
		elif event.id is ID_END_CELL:
			pass
		elif event.id is ID_END_ROW:
			man.pop()
		else:
			man.forward(event)

	def getWidth(self):
		width = 0
		for cell in self.content:
			width += cell.get_hspan()
		return width

	def isEmpty(self):
		return False

	def dumpHead(self, out, tab):
		out.write(tab + 'row(\n')

	def getCells(self):
		"""Get the list of cells."""
		return self.content

	def visit(self, visitor):
		visitor.onRow(self)


class Table(Container):
	"""Repreentation of a table, that is composed or Rows that are
	composed, in turn, of cells."""
	width = None

	def __init__(self):
		Container.__init__(self)

	def getWidth(self):
		if self.width is None:
			self.width = self.content[0].getWidth()
		return self.width

	def onEvent(self, man, event):
		if event.id is ID_NEW_CELL:
			man.push(self.content[0])
			man.send(event)
		elif event.id is ID_NEW_ROW:
			self.add(man, event.make_ext(man).content[0])
		else:
			Container.onEvent(self, man, event)

	def gen(self, gen):
		gen.genTable(self)

	def isEmpty(self):
		return False

	def getRows(self):
		"""Get the list of rows."""
		return self.content

	def dumpHead(self, out, tab):
		out.write(tab + 'table(\n')

	def visit(self, visitor):
		visitor.onTable(self)

	def numbering(self):
		return "table"

	def acceptLabel(self):
		return True

	def put_caption(self, text):
		self.set_caption(text)
		return True


# main family
class HorizontalLine(Node):
	"""A simple horizontal line."""

	def __init__(self):
		Node.__init__(self)

	def dump(self, out=sys.stdout, tab=""):
		out.write(f"{tab}horizontal-line()\n")

	def gen(self, gen):
		gen.genHorizontalLine()

	def visit(self, visitor):
		visitor.onHorizontalLine(self)


class Header(Container):
	"""An header node made of a title and of content."""
	header_level = None
	title = None
	do_title = None

	def __init__(self, level):
		Container.__init__(self)
		self.level = L_HEAD
		self.header_level = level
		self.do_title = True
		self.title = Par()

	def onEvent(self, man, event):
		if event.level is L_WORD:
			if self.do_title:
				self.title.add(man, event.make_ext(man))
			else:
				self.add(man, man.make_par())
				man.send(event)
		elif event.level is L_PAR:
			self.add(man, event.make_ext(man))
		elif event.level is not L_HEAD:
			man.forward(event)
		elif event.id is ID_TITLE:
			self.do_title = False
		elif event.object.header_level <= self.header_level:
			man.forward(event)
		else:
			self.add(man, event.make_ext(man))

	def dumpHead(self, out, tab):
		out.write(tab + "header" + str(self.header_level) + "(\n")
		out.write(tab + "  title(\n")
		self.title.dump(out, tab + INDENT)
		out.write(tab + "  )\n")

	def isEmpty(self):
		return False

	def getLevel(self):
		return self.level

	def getHeaderLevel(self):
		"""Get the level of the header in range [0, 5]."""
		return self.header_level

	def getTitle(self):
		"""Get the title of the header."""
		return self.title

	def genTitle(self, gen):
		"""Generate the title."""
		for item in self.title.getContent():
			item.gen(gen)

	def genBody(self, gen):
		"""Generate the body of the header."""
		Container.gen(self, gen)

	def gen(self, gen):
		"""Generate the header."""
		if gen.genHeader(self):
			return
		gen.genHeaderBegin(self.header_level)
		gen.genHeaderTitleBegin(self.header_level)
		self.genTitle(gen)
		gen.genHeaderTitleEnd(self.header_level)
		gen.genHeaderBodyBegin(self.header_level)
		self.genBody(gen)
		gen.genHeaderBodyEnd(self.header_level)
		gen.genHeaderEnd(self.header_level)

	def acceptLabel(self):
		return True

	def visit(self, visitor):
		visitor.onHeader(self)

	def numbering(self):
		return self.header_level

	def set_title(self, title):
		"""Set the title of the header."""
		self.title = title

	def titleText(self):
		"""Return the title as raw text."""
		return self.title.toText()


class Feature:
	"""A feature allows to add special services at generation time.
	Feature method are called at generation time."""

	def prepare(self, gen):
		"""Function called before the generation."""
		pass

	def gen_header(self, gen):
		"""Function called during the generated document header is
		produced. Notice that not all back-end uses this function."""
		pass


class HashSource:
	"""A hash source provides a way to resolve hash word, prefixed by '#'."""

	def resolve(self, word):
		"""This function is called to resolve an hash word. If the word is
		not known by the source, a None is returned. Else a document word
		must be returned."""
		return None


class Document(Container):
	"""This is the top object of the document, containing the headings
	and also the configuration environment."""
	env = None
	features = None
	labels = { }
	inv_labels = { }
	hashes = None
	hash_srcs = None

	def __init__(self, env):
		Container.__init__(self)
		self.env = env
		self.features = []
		self.hashes = { }
		self.hash_srcs = []

	def onEvent(self, man, event):
		if event.level is L_WORD:
			self.add(man, man.make_par())
			man.send(event)
		elif event.level is L_DOC and event.id is ID_END:
			pass
		else:
			self.add(man, event.make_ext(man))

	def reduceVars(self, text):
		"""Reduce variables in the given text.
		- doc -- current document
		- text -- text to replace in."""
		return self.env.reduce(text)

	def getVar(self, name, default = ""):
		"""Get a variable and evaluates the variables in its content."""
		return self.env.get(name, default)

	def setVar(self, name, val):
		self.env.set(name, val)

	def dumpHead(self, out, tab):
		for k in iter(self.env):
			out.write(k + "=" + self.env[k] + "\n")
		out.write(tab + "document(\n")

	def addFeature(self, feature):
		"""Add a feature to the document."""
		assert feature is not None
		if feature not in self.features:
			self.features.append(feature)

	def get_features(self):
		"""Get the features of the document."""
		return self.features

	def pregen(self, gen):
		"""Call the prepare method of features of the document."""
		for feature in self.features:
			print("DEBUG:", feature)
			feature.prepare(gen)

	def add_label(self, label, node):
		"""Add a label for the given node."""
		self.labels[label] = node
		self.inv_labels[node] = label
		labels = node.get_info(Info.LABELS)
		if labels is None:
			labels = [label]
			node.set_info(Info.LABELS, labels)
		else:
			labels.append(label)

	def addLabel(self, label, node):
		"""Deprecated."""
		self.add_label(label, node)

	def get_label(self, label):
		"""Find the node matching the given label.
		Return None if there is no node matching the label."""
		try:
			return self.labels[label]
		except KeyError:
			return None

	def getLabel(self, label):
		"""Deprecated."""
		return self.get_label(label)

	def get_label_for(self, node):
		"""Get the labels, if any, for the given node."""
		return node.get_info(Info.LABELS, [])

	def getLabelFor(self, node):
		"""Deprecated."""
		return self.get_label_for(node)

	def get_labels(self):
		"""Get the labels defined in this document."""
		return self.labels.keys()

	def get_labelled_nodes(self):
		"""Get the node that supports a label."""
		return self.inv_labels.keys()

	def visit(self, visitor):
		"""Visit the content of a document using the visitor interface."""
		visitor.onDocument(self)

	def add_hash_source(self, src):
		"""Add an hash source (involved in the #WORD resolution).
		Several modules can add their own hash definitions. The src
		must implement the HashSource class."""
		self.hash_srcs.append(src)

	def resolve_hash(self, word):
		"""Try to resolve an hash word. If the word is known or provided
		by an hash source, it is returned. Else warning is displayed
		and None is returned."""
		try:
			return self.hashes[word]
		except KeyError:
			for src in self.hash_srcs:
				res = src.resolve(word)
				if res is not None:
					self.hashes[word] = res
					return res
			return None


class Visitor:
	"""Visitor default class."""

	def onDocument(self, doc):
		pass

	def onHeader(self, header):
		pass

	def onPar(self, par):
		pass

	def onQuote(self, quote):
		pass

	def onEmbedded(self, embeddded):
		pass

	def onList(self, list):
		pass

	def onDefList(self, list):
		pass

	def onTable(self, table):
		pass

	def onTag(self, tag):
		pass


class Factory:
	"""Factory to customize the building of objects."""

	def makeDocument(self, env):
		"""Build a document."""
		return Document(env)

	def makeHeader(self, level):
		"""Build a new header."""
		return Header(level)

	def makePar(self):
		"""Build a new paragraph."""
		return Par()

	def makeQuote(self, level):
		"""Build a new quote."""
		return Quote(level)

	def makeBlock(self, kind):
		"""Build a new block."""
		return Block(kind)

	def makeList(self, kind, depth):
		"""Build a new list."""
		return List(kind, depth)

	def makeListItem(self):
		"""Build a new list item."""
		return ListItem()

	def makeDefList(self, depth):
		"""Build a new definition list."""
		return DefList(depth)

	def makeDefItem(self, term = None, body = None):
		"""Build a definition list item."""
		if term is None:
			term = self.makePar()
		if body is None:
			body = self.makePar()
		return DefItem(term, body)

	def makeTable(self):
		"""Build a new table."""
		return Table()

	def makeRow(self, kind):
		"""Build a new table row."""
		return Row(kind)

	def makeCell(self, kind, align = TAB_CENTER, span = 1):
		"""Build a new table cell."""
		return Cell(kind, align, span)

	def makeWord(self, text):
		"""Build a word."""
		return Word(text)

	def makeImage(self, path, width = None, height = None, caption = None):
		"""Build an image."""
		return Image(path, width, height, caption)

	def makeEmbeddedImage(self, path, width = None, height = None, caption = None, align = ALIGN_NONE):
		"""Build an embedded image."""
		img = Image(path, width, height, caption)
		img.set_info(INFO_ALIGN, align)
		return img

	def makeGlyph(self, code):
		"""Build a glyph."""
		return Glyph(code)

	def makeStyle(self, style):
		"""Build a style."""
		return Style(style)

	def makeFootNote(self):
		"""Build a footnote."""
		return FootNote()

	def makeLink(self, ref):
		"""Make a link."""
		return Link(ref)

	def makeRef(self, ref):
		"""Make a reference."""
		return Ref(ref)

