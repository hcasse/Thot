# aafig -- Thot aafig module
# Copyright (C) 2015  <hugues.casse@laposte.net>
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

"""Mopdule supporting unicode character escapes."""

import re

from thot import doc
from thot import tparser

line_re = re.compile(r"^\s*"
	r"(?P<end><\\/unicode>)|"
	r"(0x(?P<hex>[0-9a-fA-F]+)\s*:\s*(?P<hex_val>.+))|"
	r"((?P<dec>[0-9]+)\s*:\s*(?P<dec_val>.+))|"
	r"((?P<chr>[^\s]+)\s*:\s*(?P<chr_val>.+))"
	r"\s*$")

esc_re = re.compile("([+*./()|\\\\])")

def escape(t):
	r = esc_re.sub("\\\\\\1", t)
	return r

class UnicodeParser:

	def __init__(self, man):
		self.defs = []
		self.old = man.getParser()

	def parse(self, man, line):
		m = line_re.match(line)
		if m is None:
			man.error("unsupported syntax")
		elif m.group("end"):
			man.setParser(self.old)
			for (c, s) in self.defs:
				man.addWord((s, c))
		elif m.group("hex"):
			g = doc.Glyph(int(m.group("hex"), 16))
			self.defs.append((escape(m.group("hex_val")),
				lambda man, match: man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, g))))
		elif m.group("dec"):
			g = doc.Glyph(int(m.group("dec")))
			self.defs.append((escape(m.group("dec_val")),
				lambda man, match: man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, g))))
		else:
			g = doc.Word(m.group("chr"))
			self.defs.append((escape(m.group("chr_val")),
				lambda man, match: man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, g))))


class UnicodeSyntax(tparser.Syntax):

	def get_doc(self):
		return [("<unicode>CODE:TEXT*</unicode>", "define several escapes for Unicode characters.")]

	def get_lines(self):
		"""Get the pairs (function, RE) to parse lines."""
		return [(self.handle, r"^\s*<unicode>\s*$")]

	def handle(self, man, match):
		man.setParser(UnicodeParser(man))


__short__ = "definition of special sequences for Unicode characters"
__description__ = \
"""Unicode allows to defines special escapes to use Unicode symbols
in Thot documents. To find the right Unicode symbol, one can use the
website: http://shapecatcher.com/.

The syntax is:
<unicode>
(0xHHHH|D+|string):text
...
<unicode>
"""

__syntaxes__ = [
	UnicodeSyntax()
]
