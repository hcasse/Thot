# dot -- Thot dot module
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

import re
import subprocess
import sys

import thot.common as common
import thot.doc as doc
import thot.tparser as tparser

count = 0

class DotBlock(doc.Block):
	"""A block containing .dot graph.
	See http://www.graphviz.org/ for more details."""
	kind = None

	def __init__(self, kind):
		doc.Block.__init__(self, "dot")
		if not kind:
			self.kind = 'dot'
		else:
			self.kind = kind

	def dumpHead(self, tab):
		print("%sblock.dot(" % tab)

	def gen(self, gen):
		global count
		path = gen.new_friend('dot/graph-%s.png' % count)
		cmd = '%s -Tpng -o %s' % (self.kind, path)
		common.onVerbose(lambda _: "CMD: %s" % cmd)
		count += 1
		try:
			process = subprocess.Popen(
				[cmd],
					stdin = subprocess.PIPE,
					stdout = subprocess.PIPE,
					stderr = subprocess.PIPE,
					close_fds = True,
					shell = True,
					encoding='utf8'
				)
			text = self.toText()
			(out, err) = process.communicate(text)
			if process.returncode != 0:
				sys.stderr.write(err)
				self.onError('error during dot call on %s' % text)
			if err:
				self.onError('error during dot call: %son %s' % (err, text))
			gen.genFigure(path, self, self.caption)
		except OSError as e:
			self.onError('can not process dot graph: %s' % str(e))

	def kind(self):
		return "figure"
	
	def numerating(self):
		return "figure"


DOT_CLOSE = re.compile("^</dot>")
DOT_CLOSE_OLD = re.compile("^@</dot>")

def handleDot(man, match):
	tparser.BlockParser(man, DotBlock(match.group(2)), DOT_CLOSE)

def handleDotOld(man, match):
	common.onDeprecated("@<dot> form is now deprecated. Use <dot> instead.")
	tparser.BlockParser(man, DotBlock(match.group(2)), DOT_CLOSE_OLD)

__short__ = "Import GrahViz Dot in THOT output."
__desdcription__ = __short__ + """

GraphViz at https://www.graphviz.org/.
Dot syntax available at https://www.graphviz.org/doc/info/lang.html.
"""
__version__ = "1.1"
__lines__ = [
	(handleDot, "^<dot(\s+(dot|neato|twopi|circo|fdp))?>",
		"Insert the provided Dot graph (ended by </dot>)."),
	(handleDotOld, "^@<dot(\s+(dot|neato|twopi|circo|fdp))?>",
		"Insert the provided Dot graph (ended by @</dot>.")
]

__words__ = []

