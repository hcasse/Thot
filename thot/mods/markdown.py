# markdown -- markdown front-end
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

import re

from thot import common, doc, emoji, highlight, tparser

def get_ref_map(man):
	"""Get the reference map."""
	map = man.get_info("markdown-map")
	if map == None:
		map = {}
		man.set_info("markdown-map", map)
		man.add_completer(complete_ref_map)
	return map


def complete_ref_map(man):
	"""Completer that will be called to check wether all ref have been resolved."""
	map = get_ref_map(man)
	for (label, url) in map.items():
		if isinstance(url, list):
			man.warn("reference %s is not resolved!", label)
			for patch in url:
				patch.ref = "???"


def define_ref_link(man, label, url, title = None):
	"""Define a new link"""
	map = get_ref_map(man)
	try:
		patches = map[label]
		if not isinstance(patches, list):
			man.warn("%s defined twice!", label)
			return
		for patch in patches:
			patch.ref = url
			patch.title = title
	except KeyError:
		pass
	map[label] = (url, title)


def set_ref_link(man, node, label):
	"""Set the reference link and title if they exists.
	Record node for patch else."""
	map = get_ref_map(man)
	try:
		x = map[label]
		if isinstance(x, list):
			x.append(node)
		else:
			node.ref = x[0]
			node.title = x[1]
	except KeyError:
		map[label] = [node]


def handle_blockquote(man, match):
	# TODO
	# SYNTAX: > .* (can embed other paragraph / headers)
	pass

def handle_html(man, match):
	man.warn("Markdown  HTML inclusion is not supported.")

def handle_new_par(man, match):
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, Par()))

def handle_head_under(man, match, level, hrule):
	while man.top().getHeaderLevel() < 0:
		if isinstance(man.top(), doc.Par):
			title = man.top()
			if title.isEmpty() and hrule:
				man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, doc.HorizontalLine()))
				return
			man.pop()
			man.top().remove(title)
			hd = doc.Header(level)
			man.send(doc.ObjectEvent(doc.L_HEAD, doc.ID_NEW, hd))
			man.send(doc.Event(doc.L_HEAD, doc.ID_TITLE))
			hd.set_title(title)
			break
		man.pop()
		
def handle_header(man, match):
	level = len(match.group("level"))
	title = match.group("title")
	if title[-level:] == match.group("level"):
		title = title[:-level]
	man.send(doc.ObjectEvent(doc.L_HEAD, doc.ID_NEW, doc.Header(level-1)))
	tparser.handleText(man, title)
	man.send(doc.Event(doc.L_HEAD, doc.ID_TITLE))

def handle_item_list(man, match):
	man.send(doc.ItemEvent(doc.LIST_ITEM, 1))
	tparser.handleText(man, match.group("text"))

def handle_number_list(man, match):
	man.send(doc.ItemEvent(doc.LIST_NUMBER, 1))
	tparser.handleText(man, match.group("text"))

END_CODE = re.compile("^\s*```\s*$")
def handle_code_block(man, match):
	lang = match.group('lang')
	tparser.BlockParser(man, highlight.CodeBlock(man, lang), END_CODE)

def handle_hrule(man, match):
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, doc.HorizontalLine()))
	
def handle_link(man, match):
	URL = man.fix_url(match.group('URL'))
	text = match.group('text')
	title = match.group("title1")
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link(URL, title)))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(text)))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))

def handle_image_link(man, match):
	link = man.fix_url(match.group('link_imgl'))
	alt = match.group('alt_imgl')
	img = man.fix_url(match.group('image_imgl'))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link(link, alt)))
	caption = Par()
	caption.append(doc.Word(alt))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW,
		doc.Image(img, None, None, caption)))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))
	

def handle_ref(man, match):
	label = match.group("id_ref")
	link = doc.Link(None)
	set_ref_link(man, link, label)
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, link))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(match.group("text_ref"))))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))		

def handle_id_def(man, match):
	url = match.group("URL")
	if url.startswith('<'):
		url = url[1:]
	if url.endswith('>'):
		url = url[:-1]
	if ":" not in url:
		url = man.fix_path(url)
	define_ref_link(man, match.group("id"), url, match.group('text'))

def handle_style(man, style):
	man.send(doc.StyleEvent(style))

def handle_quote(man, match):
	depth = len(match.group(1))
	text = match.group(2)
	if text.strip() == "":
		man.send(doc.QuoteEvent(depth, False))
	else:
		man.send(doc.QuoteEvent(len(match.group(1))))
		tparser.handleText(man, text)

def handle_word(man, word):
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(word)))

def handle_emoji(man, match):
	text = emoji.get(match.group("emoji"))
	if text.startswith(":") and text.endswith(":"):
		man.error("unknown emoji %s", match.group("emoji"))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(text)))

def handle_code_word(man, match):
	man.send(doc.StyleEvent(doc.STYLE_CODE))

def handle_backtrick(man, match):
	text = match.group("text_backtrick")
	word = doc.Word(text)
	style = doc.Style(doc.STYLE_CODE)
	style.append(word)
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, style))

def handle_image(man, match):
	alttext = match.group("alttext_img")
	id = man.fix_url(match.group("id_img"))
	caption = Par()
	caption.append(doc.Word(alttext))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW,
		doc.Image(id, None, None, caption)))

def handle_auto_link(man, match):
	url = match.group('url_auto')
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link(url)))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(url)))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))

def handle_mailto_link(man, match):
	url = match.group('email_auto')
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link("mailto:" + url)))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(url)))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))

def handle_line_break(man, match):
	man.reparse(match.group(1))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.LineBreak()))


ID_TABLE_HEADER = "table-header"

class TableHeaderEvent(doc.Event):

	def __init__(self, aligns):
		doc.Event.__init__(self, doc.L_PAR, ID_TABLE_HEADER)
		self.aligns = aligns

class Row(doc.Row):

	def __init__(self, kind):
		doc.Row.__init__(self, kind)
		self.table = None

	def onEvent(self, man, event):
		doc.Row.onEvent(self, man, event)
		if event.id is doc.ID_NEW_CELL:
			self.table.set_align(len(self.content) - 1, self.content[-1])
		
class Table(doc.Table):

	def __init__(self):
		doc.Table.__init__(self)
		self.aligns = []
		self.content.append(Row(doc.TAB_NORMAL))
		self.content[-1].table = self

	def onEvent(self, man, event):
		if event.id is ID_TABLE_HEADER:
			self.aligns = event.aligns
			self.update_headers()
		else:
			doc.Table.onEvent(self, man, event)
			if event.id is doc.ID_NEW_ROW:
				self.content[-1].table = self

	def update_headers(self):
		for row in self.content:
			row.kind = doc.TAB_HEADER
			for i in range(0, len(row.content)):
				row.content[i].kind = doc.TAB_HEADER
				self.set_align(i, row.content[i])

	def set_align(self, i, cell):
		if i < len(self.aligns) and self.aligns[i] != None:
			cell.set_align(self.aligns[i])
			

def handle_table_header(man, match):
	aligns = []
	for bar in [s.strip() for s in match.group(1).split('|')]:
		if bar.startswith(':'):
			if bar.endswith(':'):
				align = doc.TAB_CENTER
			else:
				align = doc.TAB_LEFT
		elif bar.endswith(':'):
			align = doc.TAB_RIGHT
		else:
			align = None
		aligns.append(align)
	man.send(TableHeaderEvent(aligns))


def handle_row(man, match):
	table = Table()
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW_ROW, table))
	content = match.group(1).split('|')
	i = 0
	while i < len(content):
		if content[i].endswith('\\') and i + 1 < len(content):
			content[i] = content[i] + content[i+1]
			del content[i+1]
		else:
			i = i + 1
	for item in content:
		man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW_CELL, doc.Cell(doc.TAB_NORMAL)))
		tparser.handleText(man, item)


class DefEvent(doc.DefEvent):

	def __init__(self, term):
		doc.DefEvent.__init__(self, doc.ID_NEW_DEF, 0)
		self.term = term

	def make_ext(self, man):
		list = DefList(0)
		list.add_item(man.factory.makeDefItem(self.term))
		return list


class DefList(doc.DefList):

	def __init__(self, depth):
		doc.DefList.__init__(self, depth)

	def aggregate(self, man, node):
		if isinstance(node, DefList):
			self.add_item(node.content[0])
			man.push(self)
			man.push(self.last().get_term())
			return True
		else:
			return False
	

ID_MAKE_DEF = "make-event"

class Par(doc.Par):

	def __init__(self):
		doc.Par.__init__(self)

	def onEvent(self, man, event):
		if event.id == ID_MAKE_DEF:
			term = Par()
			self.move_content(term)
			man.send(DefEvent(term))
			man.send(doc.DefEvent(doc.ID_END_TERM))
		else:
			doc.Par.onEvent(self, man, event)

def handle_def(man, match):
	man.send(doc.Event(doc.L_PAR, ID_MAKE_DEF))
	man.parse_text(match.group(1))


def init(man):
	man.defs = { }


class Factory(doc.Factory):

	def makePar(self):
		return Par()

	def makeTable(self):
		return Table()

	def makeRow(self, kind):
		return Row(kind)

	def makeDefList(self, depth):
		return DefList(depth)


__short__ = "syntax for MarkDown format"

__description__ = \
"""This modules provides syntax for [Markdown wiki format](https://daringfireball.net/projects/markdown/).

Codes for emoji's can be found [here](https://gist.github.com/rxaviers/7360908).

A summary of the supported syntax is described below:
"""

__syntax__ = True

__factory__ = Factory()

__words__ = [
	(lambda man, match: handle_word(man, match.group("char")),
		"\\\\(?P<char>.)",
		"""protect a character from interpretation."""
	),
	(lambda man, match: handle_style(man, doc.STYLE_STRONG_EMPH),
		"\\*\\*\\*|___",
		"""open and close strong/emphasis style"""
	),
	(lambda man, match: handle_style(man, doc.STYLE_STRONG),
		"\\*\\*|__",
		"""open and close emphasis style"""
	),
	(lambda man, match: handle_style(man, doc.STYLE_STRIKE),
		"~~~",
		"""open and close strike-through style"""
	),
	(lambda man, match: handle_style(man, doc.STYLE_UNDERLINE),
		"==",
		"""open and close highlight style"""
	),
	(lambda man, match: handle_style(man, doc.STYLE_EMPHASIZED),
		"[*_]",
		"""open and close emphasis style"""
	),
	(lambda man, match: handle_style(man, doc.STYLE_SUBSCRIPT),
		"~",
		"""open and close subscript style"""
	),
	(lambda man, match: handle_style(man, doc.STYLE_SUPERSCRIPT),
		"\\^",
		"""open and close supersript style"""
	),
	(handle_backtrick,
		"``(?P<text_backtrick>(`[^`]|[^`])*)``",
		"""code text that can contain single backquote '`'"""
	),
	(handle_code_word,
		"`",
		"""open and close code text."""
	),
	(handle_image_link,
		r"\[!\[(?P<alt_imgl>[^\]]*)\]\s*\((?P<image_imgl>[^\)]*)\)\]\((?P<link_imgl>[^)]*)\)",
		"""insert image corresponding to id with alternate text alttext and with the given link"""
	),
	(handle_link,
		'\[(?P<text>[^\]]*)\]\s*\((?P<URL>[^)\s]*)(\s+"(?P<title1>[^"]*)")?\)',
		"""the text is marked with a link to the URL."""
	),
	(handle_image,
		r"!\[(?P<alttext_img>[^\]]*)\]\s*\((?P<id_img>[^\)]*)\)",
		"""insert image corresponding to id with alternate text alttext"""
	),
	(handle_auto_link,
		"<(?P<url_auto>[a-zA-Z_0-9]+://[^>]*)>",
		"""insert a link around the given url."""
	),
	(handle_mailto_link,
		"<(?P<email_auto>[a-zA-Z_0-9.]+@[a-zA-Z0-9_.]*)>",
		"""insert a link corresponding to the email address."""
	),
	(handle_html,
		"(?P<html><[^>]*>)",
		"""rough HTML code (may only be compatible with html back-end)"""
	),
	(handle_ref,
		"\[(?P<text_ref>[^\]]*)\]\s*\[(?P<id_ref>[^\]]*)\]",
		"""the text is marked with a link to reference id."""
	),
	(handle_emoji,
		"(?P<emoji>:[a-z_]+:)",
		"""insert the corresponding emoji."""
	)
]

__lines__ = [
	(handle_new_par,
		"^$",
		"""ends the current paragraph and starts a new one."""
	),
	(handle_line_break,
		"^(.*\S)\s+$",
		"""insert a line-break."""
	),
	(lambda man, match: handle_head_under(man, match, 1, False),
		"^=+$",
		"""header of level 1 which title is the preceding text."""
	),
	(lambda man, match: handle_head_under(man, match, 2, True),
		"^-+$",
		"""header of level 2 which title is the preceding text."""
	),
	(handle_header,
		"^(?P<level>#+)\s+(?P<title>.*)#*$",
		"""header which level corresponds to the number of '#'."""
	),
	(handle_hrule,
		"^(\* \* \*|\*\*\*|\*\*\*\*\*|- - -)$",
		"""horizontal rule."""
	),
	(handle_item_list,
		"^[*+-]\s+(?P<text>.*)$",
		"""start of item list or item."""),
	(handle_number_list,
		"^[0-9]+\.\s+(?P<text>.*)$",
		"""start of numbered list or item (number is not meaningful)."""
	),
	(handle_id_def,
		"^\[(?P<id>[^\]]+)\]:\s*(?P<URL>\S+)(\s+[\"'\(](?P<text>[^\)'\"]*)[\)'\"])?\s*$",
		"""define a link with an identifier that can be referenced later."""
	),
	(handle_code_block,
		"^\s*```(?P<lang>\S*)\s*$",
		"""Code with the given language."""
	),
	(handle_quote,
		"^(>+)(.*)$",
		"""quoted text."""),

	(handle_table_header,
		"^\s*\|((\s*:?-*:?\s*\|)+)\s*$",
		"""table header separator"""
	),

	(handle_row,
		"^\s*\|(([^\\\\]|(\\\\.))*)\|\s*$",
		"""table definition"""),

	(handle_def,
		"^:(.*)$",
		"list of definitions")
]
