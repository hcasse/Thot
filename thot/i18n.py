# doc -- Thot document escription module
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

"""Thot module for managing internationalization."""

import locale
import os.path
import sys

from thot import common

ID_CONTENT = "Content"
ID_INTRODUCTION = "Introduction"
ID_OUTLINE = "Outline"


GLYPH_OPEN_DQUOTE = "$open-dquote"
GLYPH_CLOSE_DQUOTE = "$close-dquote"
GLYPH_OPEN_SQUOTE = "$open-squote"
GLYPH_CLOSE_SQUOTE = "$close-squote"

CAPTION_TABLE = "table"
CAPTION_FIGURE = "figure"
CAPTION_LISTING = "listing"

ALL = {
	ID_CONTENT			: "Content",
	ID_INTRODUCTION		: "Introduction",
	ID_OUTLINE			: "Outline",
	CAPTION_TABLE		: "Table %s",
	CAPTION_FIGURE		: "Figure %s",
	CAPTION_LISTING		: "Listing %s",
	GLYPH_OPEN_DQUOTE	: '\u201c',
	GLYPH_CLOSE_DQUOTE	: '\u201d',
	GLYPH_OPEN_SQUOTE	: '\u2018',
	GLYPH_CLOSE_SQUOTE	: '\u2019'
}

class Translator:
	"""Class providing translation to generate document
	according to a selected language."""

	def get_lang(self):
		"""Get the current language."""
		return None

	def get(self, text):
		"""Get translation for the given text that may be one
		of GLYPH_xxx or CAPTION_xxx or any free text. If the text cannot be
		translated, the text is returned as is."""
		return ""

	def get_raw(self, text):
		"""Look for a translation of the text or return none. Default
		implementation returns None."""
		return None


class DictTranslator(Translator):
	"""A translator based on a dictionary."""
	dict = None

	def __init__(self, dict):
		self.dict = dict

	def get(self, text):
		res = self.get_raw(text)
		if res is None:
			res = text
		return res

	def get_raw(self, text):
		try:
			return self.dict[text]
		except KeyError:
			return None


class DefaultTranslator(DictTranslator):
	"""A translator for english."""

	def __init__(self):
		DictTranslator.__init__(self, ALL)

	def get(self, text, default=None):
		return text


def getTranslator(doc):
	"""Find a translator for the given document."""

	# find the language
	lang = doc.getVar('LANG')
	if not lang:
		lang, _ = locale.getlocale()
		sys.stderr.write("INFO: using default language: " + lang + "\n")
	nlang = lang.lower().replace('-', '_')

	# look for the local version
	path = os.path.join(doc.getVar('THOT_LIB'), "langs")
	mod = common.loadModule(nlang, path)
	if mod:
		return mod.getTranslator(doc, nlang)

	# look for the global version
	comps = nlang.split('_')
	if comps[0] == 'en':
		return DictTranslator(ALL)
	else:
		mod = common.loadModule(comps[0], path)
		if mod:
			return mod.getTranslator(doc, comps[0])
		else:
			sys.stderr.write('WARNING: cannot find language ' + nlang + "\n")
			return DefaultTranslator()
