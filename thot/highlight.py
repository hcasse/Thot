# highlight -- highlight call module
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

"""Thot module generating source content."""

import importlib
import os.path
import subprocess
import sys

from thot import doc, common

FEATURE = "highlight:feature"

# highlight command class

class Highlight(doc.Feature):

	BACKS = {
		'html'	: '',
		'ansi'	: '--out-format=ansi',
		'latex'	: '--out-format=latex',
		'rtf'	: '--out-format=rtf',
		'tex'	: '--out-format=tex',
		'xhtml'	: '--out-format=xhtml'
	}
	DOCBOOK_LANGS = {
		'py': 'python',
		'c': 'c',
		'c++': 'c++'
	}
	CSS_BACKS = [ 'html', 'xhtml' ]
	LANGS = []

	unsupported = []
	unsupported_backs = []
	checked = False
	command = None

	@staticmethod
	def getCommand():
		if not Highlight.checked:
			Highlight.checked = True
			(id, _) = common.getLinuxDistrib()
			if id == "LinuxMint":
				Highlight.command = "/usr/bin/highlight"
				common.onWarning("LinuxMint detected. Workaround to find 'highlight' command in /usr/bin/")
			else:
				Highlight.command = common.which("highlight")
				if not command:
					common.onWarning("no highlight command found: code will not be colored.")
		return Highlight.command

	def prepare(self, gen):
		gen.doc.set_info(INFO, "highlight")
		type = gen.getType()
		command = Highlight.getCommand()
		if not command:
			return

		# parse list of languages
		try:
			ans = subprocess.check_output(f"{command} --list-scripts=langs", shell = True).decode('utf-8')
			Highlight.LANGS = []
			for line in ans.split("\n"):
				try:
					p = line.index(":")
					if p >= 0:
						line = line[p+1:]
						for w in line.split():
							if w not in ('(', ')'):
								Highlight.LANGS.append(w)
				except ValueError:
					pass
		except subprocess.CalledProcessError:
			common.onWarning(f"cannot get supported languages from {command}, " +
					"falling back to default list.")

		# build the CSS file
		if type in Highlight.CSS_BACKS:
			if not gen.getTemplate().use_listing('highlight'):

				# generate the highlight file
				try:
					css = gen.new_resource('highlight/highlight.css')
					cfd = True
					if os.name == "nt":
						cfd = False
					process = subprocess.Popen(
						[f'{command} -f --syntax=c --style-outfile={css}'],
						stdin = subprocess.PIPE,
						stdout = subprocess.PIPE,
						close_fds = cfd,
						shell = True
					)
					_ = process.communicate("")
				except OSError:
					sys.stderr.write("ERROR: can not call 'highlight'\n")
					sys.exit(1)

				# add the file to the style
				styles = gen.doc.getVar('HTML_STYLES')
				if styles:
					styles += ':'
				styles += css
				gen.doc.setVar('HTML_STYLES', styles)

		# build .sty
		if type == 'latex':
			try:
				css = gen.new_resource('highlight/highlight.sty')
				process = subprocess.Popen(
					[f'{command} -f --syntax=c --style-outfile={css} {BACKS[type]}'],
					stdin = subprocess.PIPE,
					stdout = subprocess.PIPE,
					close_fds = True,
					shell = True
				)
				_ = process.communicate("")
			except OSError:
				sys.stderr.write("ERROR: can not call 'highlight'\n")
				sys.exit(1)

			# build the preamble
			preamble = gen.doc.getVar('LATEX_PREAMBLE')
			preamble += '\\usepackage{color}\n'
			preamble += '\\usepackage{alltt}\n'
			preamble += '\\input {%s}\n' % gen.get_resource_path(css)
			gen.doc.setVar('LATEX_PREAMBLE', preamble)


class HighlightCodeBlock(doc.Block):
	lang = None
	feature = None

	def __init__(self, man, lang, line = None):
		doc.Block.__init__(self, "code")
		self.lang = lang
		self.line_number = line
		man.doc.addFeature(HighlightCodeBlock.feature)
		self.set_info(doc.INFO_HTML_CLASSES, ["listing"])

	def dumpHead(self, out, tab):
		out.write(tab + "code(" + self.lang + ",\n")

	def gen(self, gen):

		# aggregate code
		text = ""
		for line in self.content:
			if text != "":
				text += '\n'
			text += line

		# generate the code
		type = gen.getType()
		if type == 'html':
			gen.genEmbeddedBegin(self)
			gen.genVerbatim('<pre class="code">\n')
			self.genCode(gen, text)
			gen.genVerbatim('</pre>')
			gen.genEmbeddedEnd(self)
		elif type == 'latex':
			gen.genEmbeddedBegin(self)
			self.genCode(gen, text)
			gen.genEmbeddedEnd(self)
		elif type == 'docbook':
			gen.genVerbatim('<programlisting xml:space="preserve" ')
			if self.lang in DOCBOOK_LANGS:
				gen.genVerbatim(f' language="{DOCBOOK_LANGS[self.lang]}"')
			gen.genVerbatim('>\n')
			gen.genText(self.toText())
			gen.genVerbatim('</programlisting>\n')
		else:
			common.onWarning(f'backend {type} unsupported for code block')

	def numbering(self):
		if self.get_caption() or self.get_labels():
			return "listing"
		else:
			return None

	def genCode(self, gen, text):
		"""Generate colorized code.
		gen -- back-end generator
		lang -- code language
		lines -- lines of the code"""

		type = gen.getType()
		if self.lang in Highlight.LANGS and type in Highlight.BACKS:
			command = Highlight.getCommand()

			# default behaviour if no command
			if not command:
				self.gen_asis(gen, text)
				return

			# other options
			opts = ""
			if self.line_number is not None:
				opts = opts + " -l"
				if self.line_number != 1:
					opts = f"{opts} -m {line}"

			# perform the command
			try:
				cfd = True
				if os.name == "nt":
					cfd = False
				process = subprocess.Popen(
					[f'{command} -f --syntax={self.lang} {Highlight.BACKS[type]} {opts}'],
					stdin = subprocess.PIPE,
					stdout = subprocess.PIPE,
					close_fds = cfd,
					shell = True
				)
				res, _ = process.communicate(text.encode('utf-8'))

				# generate the source
				gen.genVerbatim(res.decode('utf-8'))

			except OSError:
				gen.error("error during call of 'highlight'\n")
		else:
			if self.lang and self.lang not in Highlight.LANGS and self.lang not in Highlight.unsupported:
				gen.warn(f"{lang} unsupported highglight language")
				Highlight.unsupported.append(lang)
			if gen.getType() not in Highlight.BACKS and gen.getType() not in Highlight.unsupported_backs:
				gen.warn(f"{gen.getType()} unsupported highlight back-end")
				Highlight.unsupported.append(lang)
			self.gen_asis(gen, text)

	def gen_asis(self, gen, text):
		"""Generate code without formatting."""
		type = gen.getType()
		if type == 'html':
			gen.genText(text)
		elif type == 'latex':
			gen.genVerbatim("\\begin{verbatim}\n")
			gen.genTex(text)
			gen.genVerbatim("\n\\end{verbatim}\n")
		else:
			gen.genVerbatim(text)



# Pygments usage

class PygmentBackend:
	"""Pygment back-end."""

	def __init__(self, feature, formatter):
		self.feature = feature
		self.formatter = formatter

	def prepare(self, gen):
		"""Called to prepare a generation."""
		pass

	def gen(self, gen, code, lexer):
		"""Generate the code."""
		if lexer is None:
			self.gen_raw(gen, code)
		else:
			class Out:
				def write(self, text):
					gen.genVerbatim(text)
			opts = {}
			if code.line_number:
				opts["linenos"] = True
				opts["linenostart"] = code.line_number
			formatter = self.formatter(**opts)
			Pygments.MAIN.highlight(code.get_text(), lexer, formatter, Out())

	def gen_raw(self, gen, code):
		"""Generate raw code."""
		gen.genText(code.get_text())


class PygmentsDefault(PygmentBackend):
	"""Default pygments back-end."""

	def __init__(self, feature, formatter):
		PygmentBackend.__init__(self, feature, None)

	def gen(self, gen, code, lexer):
		self.gen_raw(gen, code)

	def gen_raw(self, gen, code):
		gen.genText(code.getText())


class PygmentsHTML(PygmentBackend):
	"""Pygment back-end for HTML."""

	def __init__(self, feature):
		PygmentBackend.__init__(self, feature, feature.FORM.HtmlFormatter)

	def prepare(self, gen):
		"""Prepare for HTML output."""
		if not gen.getTemplate().use_listing('pygments'):

			# generate the highlight file
			css = gen.new_resource('highlight/highlight.css')
			with open(css, "w") as out:
				out.write(self.formatter().get_style_defs('.highlight'))

			# add the file to the style
			styles = gen.doc.getVar('HTML_STYLES')
			if styles:
				styles += ':'
			styles += css
			gen.doc.setVar('HTML_STYLES', styles)

	def gen(self, gen, code, lexer):
		gen.genEmbeddedBegin(code)
		gen.genVerbatim('<pre class="code">\n')
		PygmentBackend.gen(self, gen, code, lexer)
		gen.genVerbatim('</pre>')
		gen.genEmbeddedEnd(code)


class PygmentsLatex(PygmentBackend):
	"""Pygments back-end for latex."""

	def __init__(self, feature):
		PygmentBackend.__init__(self, feature, Pygments.FORM.LatexFormatter)

	def prepare(self, gen):

		# build style file
		css = gen.new_resource('highlight/highlight.sty')
		with open(css, "w") as out:
			out.write(self.formatter().get_style_defs('.highlight'))

		# build the preamble
		preamble = gen.doc.getVar('LATEX_PREAMBLE')
		preamble += '\\usepackage{color}\n'
		preamble += '\\usepackage{alltt}\n'
		preamble += "\\usepackage{fancyvrb}\n"
		preamble += '\\input {%s}\n' % gen.get_resource_path(css)
		gen.doc.setVar('LATEX_PREAMBLE', preamble)

	def gen(self, gen, code, lexer):
		gen.genEmbeddedBegin(code)
		PygmentBackend.gen(self, gen, code, lexer)
		gen.genEmbeddedEnd(code)

	def gen_raw(self, gen, code):
		gen.genVerbatim("\\begin{verbatim}\n")
		gen.genText(code.get_text())
		gen.genVerbatim("\n\\end{verbatim}\n")


class PygmentsDocBook(PygmentBackend):
	"""Pygments back-end for DocBook."""

	def __init__(self, feature):
		PygmentBackend.__init__(self, feature, feature.formatters.HtmlFormatter())

	def gen(self, gen, code, lexer):
		gen.genEmbeddedBegin(code)
		gen.genVerbatim('<programlisting xml:space="preserve" ')
		if self.lang in DOCBOOK_LANGS:
			gen.genVerbatim(f' language="{DOCBOOK_LANGS[self.lang]}"')
		gen.genVerbatim('>\n')
		gen.genText(code.toText())
		gen.genVerbatim('</programlisting>\n')
		gen.genEmbeddedEnd(code)


class Pygments(doc.Feature):
	"""Feature managing code highlighting with module pygments."""

	BACK_MAP = {
		"html":		PygmentsHTML,
		"latex":	PygmentsLatex,
		"docbook":	PygmentsDocBook
	}
	MAIN = None
	LEX = None
	FORM = None
	UTIL = None

	@staticmethod
	def init():
		"""Initialize the use of Pygments and returns True if it is ok."""
		try:
			Pygments.MAIN = importlib.import_module("pygments")
			Pygments.LEX = importlib.import_module("pygments.lexers")
			Pygments.FORM = importlib.import_module("pygments.formatters")
			Pygments.UTIL = importlib.import_module("pygments.util")
			return True
		except ModuleNotFoundError:
			return False

	@staticmethod
	def get_feature(doc):
		feature = doc.get_info(FEATURE)
		if feature is None:
			feature = Pygments()
			doc.set_info(FEATURE, feature)
			doc.addFeature(feature)
		return feature

	def __init__(self):
		self.backend = None

		# link library

		# record information
		self.lexer_map = {}

	def prepare(self, gen):
		type = gen.getType()
		try:
			self.backend = self.BACK_MAP[gen.getType()](self)
		except KeyError:
			self.backend = PygmentsDefault(self)
		self.backend.prepare(gen)

	def get_lexer(self, lang):
		"""Get the lexer for the asked lang. Reurn None if lang is not found."""
		try:
			return self.lexer_map[lang]
		except KeyError:
			try:
				lexer = Pygments.LEX.get_lexer_by_name(lang)
			except Pygments.UTIL.ClassNotFound:
				lexer = None
			self.lexer_map[lang] = lexer
			return lexer

	def gen(self, gen, code):
		"""Generates the passed code."""
		self.backend.gen(gen, code, self.get_lexer(code.lang))


class PygmentsCodeBlock(doc.Block):
	"""Code block for Pygments module."""

	def __init__(self, man, lang, line = None):
		doc.Block.__init__(self, "code")
		self.lang = lang
		self.line_number = line
		self.feature = Pygments.get_feature(man.doc)

	def get_text(self):
		return "\n".join(self.content)

	def dumpHead(self, out, tab):
		out.write(tab + "code(" + self.lang + ",\n")

	def gen(self, gen):
		self.feature.gen(gen, self)

	def numbering(self):
		if self.get_caption() or self.get_labels():
			return "listing"
		else:
			return None


# selection of code highlighter
if Pygments.init():
	CodeBlock = PygmentsCodeBlock
else:
	HighlightCodeBlock.feature = Highlight()
	CodeBlock = HighlightCodeBlock


