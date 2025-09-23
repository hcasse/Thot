# abstract_html -- Thot html back-end
# Copyright (C) 2016  <hugues.casse@laposte.net>
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

"""Abstract back-end for HTML generation from Thot."""

import html
import os
import re

from thot import back, common, doc, i18n

EMBED_LABELS = {
	"figure":	i18n.CAPTION_FIGURE,
	"table":	i18n.CAPTION_TABLE,
	"listing":	i18n.CAPTION_LISTING
}

def obfuscate_ascii(text):
	"""Rewrite a version of text with character replaced by HTML escape
	on ASCII code."""
	return "".join([f"&#{ord(c)};" for c in text])

def obfuscate_url(url):
	"""Obfuscate URL if required: for now, only mailto:."""
	if url.startswith("mailto:"):
		return url[:7] + obfuscate_ascii(url[7:])
	else:
		return url

def escape_cdata(s):
	"""Escape in the string s characters that are invalid in CDATA
	of XML text."""
	return html.escape(s, True)

def escape_attr(s):
	"""Escape in the string s characters that are invalid in attribute
	of XML elements."""
	return html.escape(s, True)

LISTS = {
	'ul': ('<ul %s>', '<li>', '</li>', '</ul>'),
	'ol': ('<ol %s>', '<li>', '</li>', '</ol>'),
}
def getList(list):
	if list in LISTS:
		return LISTS[list]
	else:
		raise Exception('list ' + list + ' not supported')

STYLES = {
	doc.STYLE_BOLD: 		('<b>', '</b>'),
	doc.STYLE_STRONG: 		('<strong>', '</strong>'),
	doc.STYLE_ITALIC: 		('<i>', '</i>'),
	doc.STYLE_EMPHASIZED:	('<em>', '</em>'),
	doc.STYLE_UNDERLINE: 	('<u>', '</u>'),
	doc.STYLE_SUBSCRIPT: 	('<sub>', '</sub>'),
	doc.STYLE_SUPERSCRIPT: 	('<sup>', '</sup>'),
	doc.STYLE_MONOSPACE: 	('<code>', '</code>'),
	doc.STYLE_STRIKE: 		('<strike>', '</strike>'),
	doc.STYLE_BIGGER:		('<big>', '</big>'),
	doc.STYLE_SMALLER:		('<small>', '</small>'),
	doc.STYLE_CITE:			('<cite>', '</cite>'),
	doc.STYLE_CODE:			('<code>', '</code>'),
	doc.STYLE_STRONG_EMPH:	('<strong><em>', "</em></strong>")
}

def getStyle(style):
	if style in STYLES:
		return STYLES[style]
	else:
		raise Exception('style ' + style + ' not supported')


class Relocator:
	"""These objects take in charge the fact that a file has to be moved
	to some building directory. It may be used to relocate and fix
	associated file or special transformation due to this move."""

	def move(self, spath, tpath, man):
		"""Move the file from source path to the target path and
		perform relocation of references in side the source file.
		ref is the path of the resource
		If there is an error, must raise a BackException."""
		output = open(tpath, "w", encoding="utf8")
		self.move_to_stream(spath, tpath, output, man)
		output.close()

	def move_to_stream(self, spath, tpath, output, man):
		"""Move file spath and relocates the content to the output
		stream. The logical path of relocated spath is tpath."""
		pass


class CSSRelocator(Relocator):
	"""Relocator for CSS files."""

	CSS_URL_RE = re.compile(r'url\(([^)]*)\)')

	def __init__(self):
		Relocator.__init__(".css")

	def move_to_stream(self, spath, tpath, output, man):

		# open files
		try:
			input = open(spath, encoding="utf8")
		except FileNotFoundError as e:
			raise common.BackException(str(e))

		# perform the copy
		dir = os.path.dirname(spath)
		for line in input:
			m = CSSRelocator.CSS_URL_RE.search(line)
			while m:
				output.write(line[:m.start()])
				url = m.group(1)
				if ":" not in url:
					path = os.path.join(dir, url)
					rpath = man.use_resource(path)
					url = man.get_resource_link(rpath, tpath)
				output.write(f"url({url})")
				line = line[m.end():]
				m = CSSRelocator.CSS_URL_RE.search(line)
			output.write(line)


# Known relocators
RELOCATORS = {
	".css": CSSRelocator()
}


class Manager(back.Manager):
	"""Manager specialized for HTML output."""

	def __init__(self, mon = common.DEFAULT_MONITOR):
		back.Manager.__init__(self, mon = mon)
		self.anchor_count = 0

	def relocate(self, spath, dpath):
		try:
			reloc = RELOCATORS[os.path.splitext(spath)[1]]
			reloc.move(spath, dpath, self)
		except KeyError:
			back.Manager.relocate(self, spath, dpath)

	def declare_number(self, node, number):
		"""Record the assignment of a number to a node."""
		node.set_number(number)

	def declare_link(self, node, path, anchor = ""):
		"""Declare a link to the given node with the given build path. If no
		anchor is given, a new anchor is created. If anchor is None, no anchor
		is used."""
		if anchor == "":
			anchor = f"thot-{self.anchor_count}"
			self.anchor_count += 1
		node._thot_path = path
		node._thot_anchor = anchor

	def get_anchor(self, node):
		"""Get the anchor of the node (if any). None else."""
		try:
			return node._thot_anchor
		except AttributeError:
			return None

	def get_link(self, node, ref):
		"""Get the link to the given node. Return None if there is no link.
		If ref is given, the path is relative to the given path."""
		path = node._thot_path
		try:
			anchor = node._thot_anchor
		except AttributeError:
			return "<unlabelled node>"
		if path == ref:
			res = f"#{anchor}"
		else:
			path = self.get_resource_link(path, ref)
			if anchor is None:
				res = path
			else:
				res = f"{path}#{anchor}"
		return res

	def get_resource_link(self, path, ref):
		"""Get the link to a resource relative to the ref resource."""
		return self.get_resource_path(path, ref)

	def set_anchor(self, node, path, anchor):
		"""Assign a path and an anchor to a node."""
		node._thot_path = path
		node._thot_anchor = anchor


class Script:
	"""Use of script in a produced HTML page. After allocation, it may be
	customized by setting its attributes: content, src, do_async, charset, defer
	and type. Look https://www.w3schools.com/Tags/tag_script.asp for more details."""

	def __init__(self):
		self.content = None
		self.src = None
		self.do_async = None
		self.charset = None
		self.defer = None
		self.type = None

	def gen(self, gen):
		write = gen.genVerbatim
		write("\t<script")
		if self.src is not None:
			link = gen.get_manager().get_resource_link(self.src, gen.get_out_path())
			write(f" src=\"{escape_attr(link)}\"")
		if self.do_async is not None and self.do_async:
			write(" async=\"async\"")
		if self.defer is not None and self.defer:
			write(" defer=\"defer\"")
		if self.charset is not None:
			write(f" charset=\"{escape_attr(self.charset)}\"")
		if self.type is not None:
			write(f" type=\"{escape_attr(self.type)}\"")
		write(">")
		if self.content is not None:
			write("\n")
			write(self.content)
			write("\n\t")
		write("</script>\n")


# templates

class TemplateHandler:
	"""Provide support for generating pages."""

	def gen_header(self, gen):
		"""Called to generate header part of HTML file."""
		pass

	def gen_title(self, gen):
		"""Called to generate the title."""
		pass

	def gen_authors(self, gen):
		"""Called to generate list of authors."""
		pass

	def gen_menu(self, gen):
		"""Called to generate the menu."""
		pass

	def gen_content(self, gen):
		"""Called to generate the content."""
		pass


class Template:
	"""Abstract template class for the page generation."""

	def apply(self, handler, gen):
		"""Called to generate a page."""
		pass

	def use_listing(self, type):
		"""Inform the template that a listing has to be used and
		it will be generated according type that may be 'pygment' or
		'highligh'. The function returns True if the listing is taken
		in charge by the template, False else."""
		return False


class PlainTemplate(Template):
	"""Simple plain template."""

	def apply(self, handler, gen):
		out = gen.out

		# output header
		out.write('<!DOCTYPE html>\n')
		out.write('<html>\n')
		out.write('<head>\n')
		out.write("	<title>")
		handler.gen_title(gen)
		out.write("</title>\n")
		out.write('	<meta name="AUTHOR" content="' + escape_attr(gen.doc.getVar('AUTHORS')) + '">\n')
		out.write('	<meta name="GENERATOR" content="Thot - HTML">\n')
		out.write('	<meta http-equiv="Content-Type" content="text/html; charset=' +
			escape_attr(gen.doc.getVar('ENCODING')) + '">\n')
		handler.gen_header(gen)
		out.write('</head>\n<body>\n<div class="main">\n')

		# output the title
		out.write('<div class="header">\n')
		out.write('	<div class="title">')
		handler.gen_title(gen)
		out.write('</div>\n')
		out.write('	<div class="authors">')
		handler.gen_authors(gen)
		out.write('</div>\n')
		out.write('</div>')

		# output the menu
		handler.gen_menu(gen)

		# output the content
		out.write('<div class="page">\n')
		handler.gen_content(gen)
		gen.genFootNotes()
		out.write('</div>\n')

		# output the footer
		out.write("</div>\n</body>\n</html>\n")


class FileTemplate(Template):
	"""Template supporting a file in HTML. The template may contain
	the following special elements:
	* <thot:title> -- document title,
	* <thot:authors> -- list of authors,
	* <thot:menu> -- table of content of the document,
	* <thot:content> -- content of the document.
	* <thot:text>...</thot:text> -- where @VAR@ are replaced.
	"""

	RE = re.compile(r"<thot:([^/]+)\/>|<thot:text>(([^<]|<(?!/thot:text>)/)*)</thot:text>")

	def __init__(self, path, env = None, **defs):
		self.path = path
		self.defs = dict(defs)
		self.env = env

	def gen_text(self, text, gen):
		if self.env is not None:
			text = self.env.reduce(text)
		gen.out.write(text)

	def apply(self, handler, gen):
		"""Generate the page with standard thot:XXX are commands translated
		as handle command and the outputs are performed on the given
		generation gen."""
		self.defs["authors"] = handler.gen_authors
		self.defs["content"] = handler.gen_content
		self.defs["header"] =  handler.gen_header
		self.defs["title"] = handler.gen_title
		self.defs["toc"] = handler.gen_menu
		self.defs["footnotes"] = lambda gen: gen.genFootNotes()

		try:
			tpl = open(self.path, "r", encoding="utf8")
			n = 0
			for line in tpl.readlines():
				n = n + 1
				f = 0
				for m in FileTemplate.RE.finditer(line):
					gen.out.write(line[f:m.start()])
					f = m.end()
					kw = m.group(1)
					if kw is None:
						self.gen_text(m.group(2), gen)
					else:
						try:
							x = self.defs[kw]
						except KeyError:
							common.onWarning(f"unknown template element <thot:{kw}> at {self.path}:{n}")
							x = ""
						if callable(x):
							x(gen)
						else:
							self.gen_text(str(x), gen)
				gen.out.write(line[f:])

		except IOError as e:
			common.onError(str(e))



class Generator(back.Generator):
	"""Generator for HTML output."""
	trans = None
	doc = None
	footnotes = None
	struct = None
	pages = None
	page_count = None
	stack = None
	label = None
	scripts = None
	manager = None

	def __init__(self, doc, manager = None, template = None):
		back.Generator.__init__(self, doc)
		self.footnotes = []
		self.pages = { }
		self.page_count = 0
		self.stack = []
		#self.refs = { }
		self.scripts = []
		self.template = template
		self.manager = manager

	def getType(self):
		return "html"

	def get_out_ext(self):
		return ".html"

	def getTemplate(self):
		"""Get the template of page."""
		if self.template is None:
			self.template = self.doc.getVar('HTML_TEMPLATE')
			if self.template:
				self.template = FileTemplate(self.template)
			else:
				self.template = PlainTemplate()
		return self.template

	def is_distant_url(self, url):
		"""Test if the URL is distant, not local."""
		return ":" in url

	def gen_header(self):
		out = self.out
		styles = self.doc.getVar("HTML_STYLES")
		if styles:
			for style in styles.split(':'):
				if style == "":
					continue
				style_res = self.manager.use_resource(style)
				style_link = self.manager.get_resource_link(style_res, self.get_out_path())
				out.write('	<link rel="stylesheet" type="text/css" href="' + style_link + '">\n')
		short_icon = self.doc.getVar('HTML_SHORT_ICON')
		if short_icon:
			out.write(f'<link rel="shortcut icon" href="{short_icon}"/>')
		self.gen_header_embedded()

	def gen_style(self, text):
		self.out.write(f"<style>\n{text}\n</style>")

	def newScript(self):
		"""Create and record a new script for the header generation."""
		s = Script()
		self.scripts.append(s)
		return s

	def gen_header_embedded(self):
		"""Generate all that needs to be embedded in the header: script, header providers."""
		for script in self.scripts:
			script.gen(self)
		for feature in self.doc.get_features():
			feature.gen_header(self)

	def importCSS(self, spath, base = ""):
		self.manager.add_resource(spath, self.doc)
		return self.manager.get_resource_loc(spath, self.doc)

	def genFootNote(self, note):
		if note.kind != doc.FOOTNOTE_REF:
			self.footnotes.append(note)
		if note.kind != doc.FOOTNOTE_DEF:
			if note.ref:
				id = note.id
				ref = f"#footnote-custom-{note.ref}"
			else:
				id = str(len(self.footnotes))
				ref = f"#footnote-{id}"
			self.out.write(f'<a class="footnumber" href="{ref}">{id}</a>')

	def genFootNotes(self):
		if not self.footnotes:
			return
		num = 1
		self.out.write('<div class="footnotes">\n')
		for note in self.footnotes:
			self.out.write('<p class="footnote">\n')
			if note.ref:
				id = note.id
				ref = f"footnote-custom-{note.ref}"
			else:
				id = str(num)
				ref = f"footnote-{num}"
			self.out.write(f'<a class="footnumber" name="{ref}">{id}</a> ')
			num = num + 1
			for item in note.content:
				item.gen(self)
			self.out.write('</p>\n')
		self.out.write('</div>')

	def genQuoteBegin(self, level):
		for _ in range(0, level):
			self.out.write('<blockquote>')
		self.out.write('\n')

	def genQuoteEnd(self, level):
		for _ in range(0, level):
			self.out.write('</blockquote>')
		self.out.write('\n')

	def genTable(self, table):
		self.out.write('<div class="table">')
		self.out.write('<table>\n')
		for row in table.getRows():
			self.out.write('<tr>\n')
			for cell in row.getCells():

				if cell.kind == doc.TAB_HEADER:
					self.out.write('<th')
				else:
					self.out.write('<td')
				align = cell.getInfo(doc.INFO_ALIGN)
				if align is not None:
					if align == doc.TAB_LEFT:
						self.out.write(' align="left"')
					elif align == doc.TAB_RIGHT:
						self.out.write(' align="right"')
					elif align == doc.TAB_CENTER:
						self.out.write(' align="center"')
				hspan = cell.getInfo(doc.INFO_HSPAN)
				if hspan:
					self.out.write(' colspan="' + str(hspan) + '"')
				vspan = cell.getInfo(doc.INFO_VSPAN)
				if vspan:
					self.out.write(' rowspan="' + str(vspan) + '"')
				self.out.write('>')
				cell.gen(self)
				if cell.kind == doc.TAB_HEADER:
					self.out.write('</th>\n')
				else:
					self.out.write('</td>\n')

			self.out.write('</tr>\n')
		self.out.write('</table>\n')
		self.genLabel(table)
		self.out.write('</div>')

	def genHorizontalLine(self):
		self.out.write('<hr/>')

	def genVerbatim(self, line):
		self.out.write(line)

	def genText(self, text):
		self.out.write(escape_cdata(text))

	def genRaw(self, text):
		"""Generate raw text."""
		self.out.write(text)

	def genOpenTag(self, tag, node = None, attrs = None):
		"""Generate an opening tag using the information attributes of the
		given node."""
		if attrs is None:
			attrs = []
		self.out.write(f"<{tag}")
		if node:
			cls = node.getInfo(doc.INFO_CLASS)
			if cls:
				self.out.write(f" class=\"{' '.join(cls)}\"")
			css = node.getInfo(doc.INFO_CSS)
			if css:
				self.out.write(f" style=\"{css}\"")
			lang = node.getInfo(doc.INFO_LANG)
			if css:
				self.out.write(f" lang=\"{lang}\"")
		if attrs:
			self.out.write(" ")
			self.out.write(" ".join([f"{p[0]}=\"{p[1]}\"" for p in attrs]))
		self.out.write(">")

	def genCloseTag(self, tag):
		"""Generate a closing tag."""
		self.out.write(f"</{tag}>")

	def genParBegin(self):
		self.out.write('<p>\n')

	def genParEnd(self):
		self.out.write('</p>\n')

	def genList(self, list, attrs = ""):
		list_begin, item_begin, item_end, list_end = getList(list.kind)
		self.out.write((list_begin % attrs) + '\n')

		for item in list.getItems():
			self.out.write(item_begin)
			item.gen(self)
			self.out.write(item_end + '\n')

		self.out.write(list_end + '\n')

	def genDefList(self, deflist):
		self.out.write("<dl>\n")
		for item in deflist.getItems():
			self.out.write("<dt>")
			item.gen_term(self)
			self.out.write("</dt><dd>")
			item.gen_body(self)
			self.out.write("</dd>")
		self.out.write("</dl>\n")

	def genStyleBegin(self, kind):
		tag, _ = getStyle(kind)
		self.out.write(tag)

	def genStyleEnd(self, kind):
		_, tag = getStyle(kind)
		self.out.write(tag)

	def genHeaderTitle(self, header, href=None):
		"""Generate the title of a header."""
		number = header.get_number()
		anchor = self.manager.get_anchor(header)
		self.out.write('<h' + str(header.getHeaderLevel() + 1) + '>')
		if anchor is not None:
			self.out.write('<a name="' + anchor + '"></a>')
		if href is not None:
			self.out.write(f'<a href="{href}">')
		if number is not None:
			self.out.write(number + " ")
		header.genTitle(self)
		if href is not None:
			self.out.write('</a>')
		self.out.write('</h' + str(header.getHeaderLevel() + 1) + '>\n')

	def genHeader(self, header):
		"""Generate a whole header element (title + content)."""
		self.genHeaderTitle(header)
		header.genBody(self)
		return True

	def genLinkBegin(self, url, title = None):

		# process the URL
		if self.is_distant_url(url):
			url = obfuscate_url(url)
		else:
			url = self.manager.get_resource_link(url, self.get_out_path())

		# generate the code
		self.out.write(f'<a href="{url}"')
		if title is not None:
			self.out.write(f' title="{title}"')
		self.out.write('>')

	def genLinkEnd(self, url):
		self.out.write('</a>')

	def genImageTag(self, url, node, caption):
		if ":" in url:
			new_url = url
		else:
			self.manager.use_resource(url)
			new_url = self.manager.get_resource_link(url, self.get_out_path())
		self.out.write('<img src="' + new_url + '"')
		if node.get_width() is not None:
			self.out.write(f' width="{node.get_width()}"')
		if node.get_height() is not None:
			self.out.write(f' height="{node.get_height()}"')
		if caption is not None:
			self.out.write(' alt="' + escape_attr(caption.toText()) + '"')
		self.out.write('/>')

	def genImage(self, url, node, caption):
		self.genImageTag(url, node, caption)

	def genFigure(self, url, node, caption):
		align = node.getInfo(doc.INFO_ALIGN)
		self.out.write('<div class="figure"')
		if align == doc.ALIGN_LEFT:
			self.out.write(' style="text-align:center;float:left"')
		elif align == doc.ALIGN_RIGHT:
			self.out.write(' style="text-align:center;float:right"')
		else:
			self.out.write(' style="text-align:center"')
		self.out.write('>\n')
		self.genImageTag(url, node, caption)
		self.genLabel(node)
		self.out.write("</div>\n")

	def genGlyph(self, code):
		self.out.write('&#' + str(code) + ';')

	def genLineBreak(self):
		self.out.write('<br/>')

	def genAuthors(self):
		"""Generate the text of the authors."""
		authors = common.scanAuthors(self.doc.getVar('AUTHORS'))
		first = True
		for author in authors:
			if first:
				first = False
			else:
				self.out.write(', ')
			email = ""
			if 'email' in author:
				url = f"mailto:{author['email']}"
				self.out.write(f'<a href="{obfuscate_url(url)}">')
			self.out.write(escape_cdata(author['name']))
			if email:
				self.out.write('</a>')

	def genLabel(self, node):

		# get information
		anchor = self.manager.get_anchor(node)
		caption = node.get_caption()
		number = node.get_number()

		# generate the code
		if caption or anchor or number:
			self.out.write('<div class="label">')

			# generate action
			if anchor:
				self.out.write(f"<a name=\"{anchor}\" class=\"label-ref\"></a>")

			# generate number
			if number:
				try:
					label = self.translate(EMBED_LABELS[node.numbering()])
				except KeyError:
					label = f"{node.numbering()} %s"
				self.out.write(label % number)

			# generate caption
			if caption:
				if number:
					self.out.write(" : ")
				caption.gen_content(self)

			self.out.write("</div>")

	def genEmbeddedBegin(self, node):
		self.out.write(f'<div class="{node.numbering()}">')
		self.genLabel(node)

	def genEmbeddedEnd(self, node):
		if self.label:
			self.genLabel(self.label)
		self.out.write('</div>')

	def genRef(self, ref):
		node = self.doc.getLabel(ref.label)
		if not node:
			common.onWarning(f"label\"{ref.label}\" cannot be resolved")
		else:
			r = self.get_href(node)
			self.out.write(f"<a href=\"{r[0]}\">{r[1]}</a>")

	def gen_line_break(self):
		self.out.write("<br/>")

	#def add_ref(self, node, anchor, number = ""):
	#	"""Add a new reference to the given node represented by
	#	the given anchor, possibly a number."""
	#	self.refs[node] = (anchor, number)

	def get_href(self, node):
		"""Get the hypertext reference corresponding to the given node."""
		res = self.manager.get_link(node, self.get_out_path())
		return res

	def get_manager(self):
		"""Get the file manager for the generator."""
		return self.manager


# module description
__short__ = "Common facilities for HTML back-end"
__description__ = """Cannot be used as a back-end per se."""
