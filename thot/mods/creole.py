# creole -- creole front-end
# Copyright (C) 2025  <hugues.casse@laposte.net>
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

"""Module implementing Creole syntax."""

import re
from thot import doc, tparser

# http://www.wikicreole.org/wiki/Home
#
# Extensions: .creole, .wiki
#
# Words
#
# //italic//
# **bold**
# [[link]]
# [[URL|label]]
# {{image|labe}}
#
# Blocks
#
# empty row: paragraph separation
# \\ forced line break
#
# * bullet list
# ** sub-bullet list
# # numbered list
# ## sub-numbered list
#
# ----	horizontal line
#
# {{{
#	no wiki area
# }}}
#
# |= table header |= ... 	|
# |  table cell	  | ...		|
#
# Heading
#
# ==	level 1
# ===	level 2
# ====	level 3

END_NOWIKI = re.compile(r"^}}}\s*$")

def handle_simple_link(man, match):
	link = match.group("link")
	url = man.fix_url(link)
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link(url)))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(link)))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))

def handle_label_link(man, match):
	label = match.group("linklab")
	url = man.fix_url(match.group("linkurl"))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link(url)))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(label)))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))

def handle_header(man, match):
	level = len(match.group("level")) - 1
	title = match.group("title")
	man.send(doc.ObjectEvent(doc.L_HEAD, doc.ID_NEW, doc.Header(level)))
	man.parse_text(title)
	man.send(doc.Event(doc.L_HEAD, doc.ID_TITLE))

def handle_item_list(man, match):
	man.send(doc.ItemEvent(doc.LIST_ITEM, len(match.group("depth"))))
	man.parse_text(match.group("text"))

def handle_number_list(man, match):
	man.send(doc.ItemEvent(doc.LIST_NUMBER, len(match.group("depth"))))
	man.parse_text(match.group("text"))

def handle_no_wiki(man, match):
	man.parse_block(doc.RawBlock(), tparser.RawParser(END_NOWIKI))

def handle_table(man, match):
	line = match.group("row")
	table = doc.Table()
	table.content.append(doc.Row(doc.Table.HEADER if line.startswith('=') else doc.Table.NORMAL))
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW_ROW, table))
	for text in match.group("row").split('|'):
		kind = doc.Table.NORMAL
		if text.startswith('='):
			kind = doc.Table.HEADER
			text = text[1:]
		man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW_CELL, doc.Cell(kind)))
		man.parse_text(text)


__short__ = "syntax for Creole format"

__description__ = \
"""This modules provides syntax for
[Creole wiki format](http://www.wikicreole.org/wiki/Home).

A summary of the supported syntax is described below:
"""

__syntax__ = True

__words__ = [
	(lambda man, match: man.send(doc.StyleEvent(doc.STYLE_BOLD)),
		r"\*\*",
		"""open and close bold style"""
	),
	(lambda man, match: man.send(doc.StyleEvent(doc.STYLE_ITALIC)),
		r"\/\/",
		"""open and close italic style"""
	),
	(
		handle_simple_link,
		r"\[\[(?P<link>[^|\]]+)\]\]",
		"link inside the wiki"
	),
	(
		handle_label_link,
		r"\[\[(?P<linkurl>[^|]+)\|(?P<linklab>[^]]*)\]\]",
		"link inside the wiki"
	),
	(lambda man, match: man.send(doc.ObjectEvent(doc.L_WORD, '', doc.LineBreak())),
		r"\\\\",
		"""insert a line break."""
	)
]

__lines__ = [
	(lambda man, match: man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, doc.Par())),
		"^$",
		"""ends the current paragraph and starts a new one."""
	),
		(handle_header,
		r"^(?P<level>==+)\s+(?P<title>.*)$",
		"""header with level 1 (==), 2 (===), 3 (====)."""
	),
	(handle_item_list,
		r"^(?P<depth>\*+)\s+(?P<text>.*)$",
		"""bulleted list."""
	),
	(handle_number_list,
		r"^(?P<depth>#+)\s+(?P<text>.*)$",
		"""numbered list."""
	),
	(lambda man, match: man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW, doc.HorizontalLine())),
		r"^----+$",
		"""horizontal rule."""
	),
	(handle_no_wiki,
		r"^{{{\s*$",
		"""no wiki area."""
	),
	(handle_table,
		r"^\|(?P<row>.*)\|\s*$",
		"""table row (cell separated with |, header with |=)."""
	)
]
