# gnuplot -- Thot gnuplot module
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

"""Module supporting generation of output with gnuplot."""

import re
import subprocess
import sys

from thot import doc
from thot import tparser

count = 0
has_gnuplot = True

class GnuPlotBlock(doc.Block):
	"""A block containing .gnu graph.
	See http://gnuplot.info/ for more details."""
	w = None
	h = None

	def __init__(self, w, h):
		doc.Block.__init__(self, "gnuplot")
		self.w = w
		self.h = h

	def dumpHead(self, out, tab):
		out.write(f"{tab}sblock.gnuplot(\n")

	def gen(self, gen):

		# gnuplot exists ?
		global count
		global has_gnuplot
		if not has_gnuplot:
			return

		# prepare the size
		opt = ""
		if self.w:
			if not self.h:
				self.h = self.w
			opt = f"size {self.w},{self.h}"

		path = gen.new_resource(f'gnuplot/graph-{count}.png')
		count += 1
		try:
			process = subprocess.Popen(
				[ 'gnuplot' ],
					stdin = subprocess.PIPE,
					stdout = subprocess.PIPE,
					stderr = subprocess.PIPE,
					close_fds = True,
					shell = True
				)
			(_, err) = process.communicate(("set terminal png transparent " +
				f"{opt} crop\nset output \"{path}\"\n{self.toText()}").encode('utf-8'))
			if process.returncode == 127:
				has_gnuplot = False
				self.onWarning("gnuplot is not available")
				return
			if process.returncode:
				print(f"ERROR: {process.returncode}")
				sys.stderr.write(err.decode('utf-8'))
				self.onError('error during gnuplot call')
			gen.genEmbeddedBegin(self)
			gen.genImage(path, self, self.get_caption())
			gen.genEmbeddedEnd(self)
		except OSError as e:
			self.onError(f'can not process gnuplot: {e}')

	def numbering(self):
		if self.get_caption() or self.get_labels():
			return "figure"
		else:
			return None


GNUPLOT_CLOSE = re.compile("^</gnuplot>")

def handleGnuPlot(man, match):
	tparser.BlockParser(man, GnuPlotBlock(match.group(2), match.group(4)), GNUPLOT_CLOSE)

GNUPLOT_OPEN = (handleGnuPlot, re.compile(r"^<gnuplot(\?([0-9]+)(x([0-9]+)))?>"))

def init(man):
	man.addLine(GNUPLOT_OPEN)
