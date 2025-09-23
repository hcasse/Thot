# latexmath -- Thot latexmath module
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

"""Module for syntax for including Latex math."""

import re
import subprocess
import sys

from thot import common, doc, tparser

count = 0
formulae = { }

class Builder(doc.Feature):
	"""Builder for math expression and feature"""

	def genWord(self, man, w):
		"""Generate the HTML for a word formula."""
		pass

	def genBlock(self, man, b):
		"""Generate the HTML for a block formula."""
		pass


MATHJAX_SELECTOR = """
MathJax.Hub.Register.StartupHook("End Jax",function () {
  var BROWSER = MathJax.Hub.Browser;

  var canUseMML = (BROWSER.isFirefox && BROWSER.versionAtLeast("1.5")) ||
                  (BROWSER.isMSIE    && BROWSER.hasMathPlayer) ||
                  (BROWSER.isSafari  && BROWSER.versionAtLeast("5.0")) ||
                  (BROWSER.isOpera   && BROWSER.versionAtLeast("9.52") &&
                                       !BROWSER.versionAtLeast("14.0"));

  var CONFIG = MathJax.Hub.CombineConfig("MMLorHTML",{
    prefer: {
      MSIE:"MML", Firefox:"HTML", Opera:"HTML", Chrome:"HTML", Safari:"HTML",
      other:"HTML"
    }
  });

  var jax = CONFIG.prefer[BROWSER] || CONFIG.prefer.other;
  if (jax === "HTML") jax = "HTML-CSS"; else if (jax === "MML")  jax = "NativeMML";
  if (jax === "NativeMML" && !canUseMML) jax = CONFIG.prefer.other;
  return MathJax.Hub.setRenderer(jax);
});
"""

class MathWord(doc.Word):

	def __init__(self, text, builder):
		doc.Word.__init__(self, text)
		self.builder = builder

	def dump(self, out=sys.stdout, tab = ""):
		out.write(f"{tab}latexmath({self.text})\n")

	def gen(self, gen):
		if gen.getType() == "latex":
			gen.genVerbatim(f"${self.text}$")
		elif gen.getType() == "html":
			self.builder.genWord(gen, self)
		else:
			gen.genText(self.text)

class MathBlock(doc.Block):

	def __init__(self, builder):
		doc.Block.__init__(self, "eq")
		self.builder = builder
		self.text = None

	def dumpHead(self, out, tab):
		out.write(tab + "eq(" + self.text + ",\n")

	def getKind(self):
		return "equation"

	def numbering(self):
		return "equation"

	def gen(self, gen):

		if gen.getType() == "latex":
			gen.genVerbatim("\\begin{multiline*}")
			f = True
			for line in self.content:
				if f:
					f = False
				else:
					gen.genVerbatim(" \\\\")
				gen.genVerbatim("\n\t")
				gen.genVerbatim(line)
			gen.genVerbatim("\n\\end{multiline*}\n")

		elif gen.getType() == "html":
			self.builder.genBlock(gen, self)

		else:
			gen.genText(self.text)


class L2MLBuilder(Builder):

	def __init__(self, f):
		self.f = f

	def genWord(self, man, w):
		man.genVerbatim(self.f(w.text))

	def genBlock(self, man, b):
		man.genOpenTag("center")
		f = True
		for line in b.content:
			if f:
				f = False
			else:
				man.genVerbatim("<br/>")
			man.genVerbatim(self.f(line))
		man.genCloseTag("center")


class MathJAXBuilder(Builder):

	def prepare(self, gen):
		if gen.getType() == "html":
			gen.doc.setVar("LATEXMATH_SCRIPT", "yes")
			script = gen.newScript()
			script.do_async = True
			script.src = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML"
			script = gen.newScript()
			script.content = MATHJAX_SELECTOR
			script.type = "text/x-mathjax-config"

	def genWord(self, man, w):
		man.genVerbatim(f"\\({w.text}\\)")

	def genBlock(self, man, b):
		man.genVerbatim("$$")
		f = True
		for line in b.content:
			if f:
				f = False
			else:
				man.genVerbatim("\\\\\n")
			man.genVerbatim(line)
		man.genVerbatim("$$")


class MimetexMath(doc.Word):

	def __init__(self, text):
		doc.Word.__init__(self, text)

	def dump(self, out=sys.stdout, tab = ""):
		out.write(f"{tab}latexmath({self.text})\n")

	def prepare(self, man):
		pass

	def gen(self, gen):
		global count

		if gen.getType() == "latex":
			gen.genVerbatim(f"${self.text}$")
		else:
			cmd = mimetex.get()
			if not cmd:
				return
			rpath = ''
			if self.text in formulae:
				rpath = formulae[self.text]
			else:
				rpath = gen.new_friend(f"latexmath/latexmath-{count}.gif")
				count += 1
				try:
					proc = subprocess.Popen(
						[f"{cmd} -d '{self.text}' -e {rpath}"],
						stdout = subprocess.PIPE,
						stderr = subprocess.PIPE,
						shell = True
					)
					out, err = proc.communicate()
					if proc.returncode != 0:
						sys.stderr.write(out)
						sys.stderr.write(err)
						self.onWarning("bad latexmath formula.")
					else:
						formulae[self.text] = rpath
				except OSError:
					#MIMETEX_AVAILABLE = False
					self.onWarning("mimetex is not available: no latexmath !")
			if rpath:
				gen.genImage(rpath, None, self)

class MimetexBuilder(Builder):

	def gen(self, gen, text, part):
		global count

		cmd = mimetex.get()
		if not cmd:
			return
		rpath = ''
		if text in formulae:
			rpath = formulae[text]
		else:
			rpath = gen.new_resource(f"latexmath/latexmath-{count}.gif")
			count += 1
			try:
				proc = subprocess.Popen(
					[f"{cmd} -d '{text}' -e {rpath}"],
					stdout = subprocess.PIPE,
					stderr = subprocess.PIPE,
					shell = True
				)
				out, err = proc.communicate()
				if proc.returncode != 0:
					sys.stderr.write(out)
					sys.stderr.write(err)
					self.onWarning("bad latexmath formula.")
				else:
					formulae[text] = rpath
			except OSError:
				#MIMETEX_AVAILABLE = False
				gen.onWarning("mimetex is not available: no latexmath !")
		if rpath:
			gen.genImage(rpath, part, None)

	def genWord(self, man, w):
		self.gen(man, w.text, w)

	def genBlock(self, man, b):
		man.genOpenTag("center")
		f = True
		for line in b.content:
			if f:
				f = False
			else:
				man.genVerbatim("<br/>")
			self.gen(man, line, b)
		man.genCloseTag("center")


# Alternative management

DEFAULT = None
BUILDERS = { }
BUILDER = None

try:
	import latex2mathml.converter as m
	BUILDERS["latex2mathml"] = L2MLBuilder(m.convert)
	DEFAULT = "latex2mathml"
except ImportError as e:
	pass

BUILDERS["mathjax"] = MathJAXBuilder()
if DEFAULT is None:
	DEFAULT = "mathjax"

mimetex = common.CommandRequirement("mimetex",
	'mimetex not found but required by latexmath module: ignoring latexmath tags')
BUILDERS["mimetex"] = MimetexBuilder()
if DEFAULT is None:
	DEFAULT = "mimetex"

def selectBuilder(man):
	global BUILDER
	try:
		n = man.doc.getVar("LATEXMATH", DEFAULT)
		BUILDER = BUILDERS[n]
	except KeyError:
		man.onWarning(f"unknown mathlatex output: {v}. Reverting to use mimetex.")


# Syntax

END_BLOCK = re.compile(r"^\s*<\/eq>\s*$")

def handleMath(man, match):
	text = match.group("latexmath")
	if text == "":
		man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word("$")))
	else:
		man.doc.addFeature(BUILDER)
		man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, MathWord(text, BUILDER)))

def handleBlock(man, match):
	man.doc.addFeature(BUILDER)
	tparser.BlockParser(man, MathBlock(BUILDER), END_BLOCK)


# module declaration
__short__ = "Use of Latex math formuilae in Thot."
builders = ('\n').join([f'- {k}' for k in BUILDERS.keys()])
__description__ = __short__ + f"""

A quick summary of Latex math syntax is available at https://en.wikibooks.org/wiki/LaTeX/Mathematics .

Variable LATEXMATH select one of the back-end among:
{builders}
"""
__version__ = "1.3"
__words__ = [
	(handleMath, r"\$(?P<latexmath>[^$]*)\$",
		"Insert the given formula in the text.")
]
__lines__ = [
	(handleBlock, r"^\s*<eq\s*>\s*$",
		"Insert the given formula as a stand-alone equation (ended by </eq>.")
]

def init(man):
	selectBuilder(man)


