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

import thot.common as common
import thot.doc as doc
import thot.highlight as highlight
import thot.tparser as tparser

def handle_blockquote(man, match):
	# TODO
	# SYNTAX: > .* (can embed other paragraph / headers)
	pass

def handle_html(man, match):
	man.warn("Markdown  HTML inclusion is not supported.")

def handle_new_par(man, match):
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, doc.Par()))

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
	URL = man.fix_path(match.group('URL'))
	text = match.group('text')
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link(URL)))
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(text)))
	man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))

def handle_ref(man, match):
	try:
		url = man.fix_path(man.defs[match.group("id_ref")][0])
		man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW_LINK, doc.Link(url)))
		man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(match.group("text_ref"))))
		man.send(doc.CloseEvent(doc.L_WORD, doc.ID_END_LINK, "link"))		
	except KeyError:
		common.warn("reference %s is unknown!" % match.group("id_ref"))

def handle_id_def(man, match):
	man.defs[match.group("id")] = (match.group("URL"), match.group("text")) 

def handle_style(man, style):
	man.send(doc.StyleEvent(style))

def handle_word(man, word):
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(word)))

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
	id = match.group("id_img")
	caption = doc.Par()
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


def init(man):
	man.defs = { }


__short__ = "syntax for MarkDown format"

__description__ = \
"""This modules provides syntax for Markdown wiki format
(https://daringfireball.net/projects/markdown/).

A summary of the supported syntax is described below:
"""

__syntax__ = True

__words__ = [
	(handle_link,
		"\[(?P<text>[^\]]*)\]\s*\((?P<URL>[^)]*)\)",
		"""the text is marked with a link to the URL."""
	),
	(lambda man, match: handle_word(man, match.group("char")),
		"\\\\(?P<char>.)",
		"""protect a character from interpretation."""
	),
	(lambda man, match: handle_style(man, doc.STYLE_STRONG),
		"\\*\\*|__",
		"""open and close emphasis style"""
	),
	(lambda man, match: handle_style(man, doc.STYLE_EMPHASIZED),
		"[*_]",
		"""open and close emphasis style"""
	),
	(handle_backtrick,
		"``(?P<text_backtrick>(`[^`]|[^`])*)``",
		"""code text that can contain single backquote '`'"""
	),
	(handle_code_word,
		"`",
		"""open and close code text."""
	),
	(handle_image,
		r"!\[(?P<alttext_img>[^\]]*)\]\s*\((?P<id_img>[^\]]*)\)",
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
	)
]

__lines__ = [
	(handle_new_par,
		"^$",
		"""ends the current paragraph and starts a new one."""
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
		"^\[(?P<id>[^\]]+)\]:\s*(?P<URL>\S+)(?P<text>\s+.*)$",
		"""define a link with an identifier that can be referenced later."""
	),
	(handle_code_block,
		"^\s*```(?P<lang>\S*)\s*$",
		"""Code with the given language."""
	),
]
