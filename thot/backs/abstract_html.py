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

import os
import re
import shutil
import sys
import urllib.parse as urlparse

import thot.back as back
import thot.common as common
import thot.doc as doc
import thot.doc as tdoc
import thot.highlight as highlight
import thot.htmlman as htmlman
import thot.i18n as i18n

def escape_cdata(s):
	"""Escape in the string s characters that are invalid in CDATA
	of XML text."""
	return common.escape(s)

def escape_attr(s):
	"""Escape in the string s characters that are invalid in attribute
	of XML elements."""
	return common.escape(s, True)

#CSS_URL_RE = re.compile('url\(([^)]*)\)')

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
	doc.STYLE_MONOSPACE: 	('<tt>', '</tt>'),
	doc.STYLE_STRIKE: 		('<strike>', '</strike>'),
	doc.STYLE_BIGGER:		('<big>', '</big>'),
	doc.STYLE_SMALLER:		('<small>', '</small>'),
	doc.STYLE_CITE:			('<cite>', '</cite>'),
	doc.STYLE_CODE:			('<code>', '</code>')
}

def getStyle(style):
	if style in STYLES:
		return STYLES[style]
	else:
		raise Exception('style ' + style + ' not supported')


class Script:
	
	def __init__(self):
		self.content = None
		self.src = None
		self.do_async = None
		self.charset = None
		self.defer = None
		self.type = None
	
	def gen(self, out):
		out.write("\t<script")
		if self.src != None:
			out.write(" src=\"%s\"" % escape_attr(self.src))
		if self.do_async != None and self.do_async:
			out.write(" async=\"async\"")
		if self.defer != None and self.defer:
			out.write(" defer=\"defer\"")
		if self.charset != None:
			out.write(" charset=\"%s\"" % escape_attr(self.charset))
		if self.type != None:
			out.write(" type=\"%s\"" % escape_attr(self.type))
		out.write(">")
		if self.content != None:
			out.write("\n")
			out.write(self.content)
			out.write("\n\t")
		out.write("</script>\n")


# pages
class PageHandler:
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


class Page:
	"""Abstract class for page generation."""

	def apply(self, handler, gen):
		"""Called to generate a page."""
		pass


# PlainPage class
class PlainPage(Page):
	"""Simple plain page."""
	
	def apply(self, handle, gen):
		out = gen.out
		
		# output header
		out.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n')
		out.write('<html>\n')
		out.write('<head>\n')
		out.write("	<title>")
		handle.gen_title(gen)
		out.write("</title>\n")
		out.write('	<meta name="AUTHOR" content="' + escape_attr(gen.doc.getVar('AUTHORS')) + '">\n')
		out.write('	<meta name="GENERATOR" content="Thot - HTML">\n');
		out.write('	<meta http-equiv="Content-Type" content="text/html; charset=' + escape_attr(gen.doc.getVar('ENCODING')) + '">\n')
		handle.gen_header(gen)
		out.write('</head>\n<body>\n<div class="main">\n')
		
		# output the title
		out.write('<div class="header">\n')
		out.write('	<div class="title">')
		handle.gen_title(gen)
		out.write('</div>\n')
		out.write('	<div class="authors">')
		handle.gen_authors(gen)
		out.write('</div>\n')
		out.write('</div>')
		
		# output the menu
		handle.gen_menu(gen)
		
		# output the content
		out.write('<div class="page">\n')
		handle.gen_content(gen)
		gen.genFootNotes()
		out.write('</div>\n')		

		# output the footer
		out.write("</div>\n</body>\n</html>\n")



# TemplatePage class
template_re = re.compile("<thot:([^/]+)\/>")

class TemplatePage(Page):
	"""Page supporting template in HTML. The template may contain
	the following special elements:
	* <thot:title> -- document title,
	* <thot:authors> -- list of authors,
	* <thot:menu> -- table of content of the document,
	* <thot:content> -- content of the document.
	"""
	path = None
	
	def __init__(self, path):
		self.path = path
	
	def apply(self, handler, gen):
		map = {
			"authors": handler.gen_authors,
			"content": handler.gen_content,
			"header":  handler.gen_header,
			"title":   handler.gen_title,
			"toc":    handler.gen_menu
		}
		global template_re

		try:
			tpl = open(self.path, "r")
			n = 0
			for line in tpl.readlines():
				n = n + 1
				f = 0
				for m in template_re.finditer(line):
					gen.out.write(line[f:m.start()])
					f = m.end()
					try:
						kw = m.group(1)
						map[kw](gen)
					except KeyError as e:
						common.onError("unknown element %s at %d" % (kw, n))					
				gen.out.write(line[f:])
			
		except IOError as e:
			common.onError(str(e))


# Ref classes
class Ref:
	"""Abstract class representing a reference inside a document or
	a set of documents."""

	def label(self):
		"""Return the label associated with reference: for example,
		for a chapter, this is the title of the chapter."""
		return ""

	def number(self):
		"""Return the number associated with the referenced: chapter
		number for a chapter."""
		return ""

	def link(self, relative=None):
		"""Return the URL link corresponding to the reference:
		the link absolute (relatively to the project root) or
		relative to the given file."""
		return ""

class HeaderRef:
	"""A reference for header."""

	def __init__(self, file, node):
		self.file = file
		self.node = node

	def label(self):
		pass

	def number(self):
		pass

	def link(self, relative):
		pass



# Generator class
class Generator(back.Generator):
	"""Generator for HTML output."""
	trans = None
	doc = None
	path = None
	root = None
	from_files = None
	to_files = None
	footnotes = None
	struct = None
	pages = None
	page_count = None
	stack = None
	label = None
	refs = None
	scripts = None
	template = None
	man = None

	def __init__(self, doc, man = None):
		back.Generator.__init__(self, doc)
		self.footnotes = []
		self.pages = { }
		self.page_count = 0
		self.stack = []
		self.refs = { }
		self.scripts = []
		if man != None:
			self.man = man
		else:
			path = doc.getVar("THOT_FILE")
			self.man = htmlman.LocalManager(
				os.path.splitext(os.path.basename(path))[0],
				outdir = os.path.dirname(path))

	def getType(self):
		return "html"

	def getTemplate(self):
		"""Get the template of page."""
		if self.template == None:
			self.template = self.doc.getVar('HTML_TEMPLATE')
			if self.template:
				self.template = TemplatePage(self.template)
			else:
				self.template = PlainPage()
		return self.template

	def gen_header(self):
		out = self.out
		styles = self.doc.getVar("HTML_STYLES")
		if styles:
			for style in styles.split(':'):
				if style == "":
					continue
				new_style = self.importCSS(style)
				out.write('	<link rel="stylesheet" type="text/css" href="' + new_style + '">\n')
		short_icon = self.doc.getVar('HTML_SHORT_ICON')
		if short_icon:
			out.write('<link rel="shortcut icon" href="%s"/>' % short_icon)
		self.genScripts()

	def newScript(self):
		"""Create and record a new script for the header generation."""
		s = Script()
		self.scripts.append(s)
		return s
	
	def genScripts(self):
		"""Generate the script needed by the page. This functions can be called in two forms."""
		for s in self.scripts:
			s.gen(self.out)
	
	# def importCSS(self, spath, base = ""):
		# """Perform import of files found in a CSS stylesheet.
		# spath -- path to the original CSS stylesheet.
		# base -- base path of the source."""

		# # get target path
		# if spath.startswith(self.getImportDir()):
			# return spath
		# path = self.get_friend(spath, base)
		# if path:
			# return path
		# if os.path.isabs(spath):
			# base = os.path.dirname(spath)
			# spath = os.path.basename(spath)
		# tpath = self.new_friend(spath)
		# spath = os.path.join(base, spath)

		# # open files
		# try:
			# input = open(spath)
		# except FileNotFoundError as e:
			# raise common.BackException(str(e))
		# output = open(tpath, "w")
		# rbase = os.path.dirname(spath)

		# # perform the copy
		# for line in input:
			# m = CSS_URL_RE.search(line)
			# while m:
				# output.write(line[:m.start()])
				# url = m.group(1)
				# res = urlparse.urlparse(url)
				# if res[0]:
					# output.write(m.group())
				# else:
					# rpath = os.path.relpath(os.path.join(rbase, res[2]), base)
					# rpath = self.use_friend(rpath, base)
					# output.write("url(%s)" % self.relative_friend(rpath, os.path.dirname(tpath)))
				# line = line[m.end():]
				# m = CSS_URL_RE.search(line)
			# output.write(line)

		# # return path
		# return tpath

	# def genFootNote(self, note):
		# if note.kind != doc.FOOTNOTE_REF:
			# self.footnotes.append(note)
		# if note.kind != doc.FOOTNOTE_DEF:
			# if note.ref:
				# id = note.id
				# ref = "#footnote-custom-%s" % note.ref
			# else:
				# id = str(len(self.footnotes))
				# ref = "#footnote-%s" % id
			# self.out.write('<a class="footnumber" href="%s">%s</a>' % (ref, id))

	def genFootNotes(self):
		if not self.footnotes:
			return
		num = 1
		self.out.write('<div class="footnotes">\n')
		for note in self.footnotes:
			self.out.write('<p class="footnote">\n')
			if note.ref:
				id = note.id 
				ref = "footnote-custom-%s" % note.ref
			else:
				id = str(num)
				ref = "footnote-%d" % num
			self.out.write('<a class="footnumber" name="%s">%s</a> ' % (ref, id))
			num = num + 1
			for item in note.content:
				item.gen(self)
			self.out.write('</p>\n')
		self.out.write('</div>')

	def genQuoteBegin(self, level):
		for i in range(0, level):
			self.out.write('<blockquote>')
		self.out.write('\n')

	def genQuoteEnd(self, level):
		for i in range(0, level):
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
				if not align or align == doc.TAB_LEFT:
					pass
				elif align == doc.TAB_RIGHT:
					self.out.write(' align="right"')
				else:
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

	def genOpenTag(self, tag, node = None, attrs = []):
		"""Generate an opening tag using the information attributes of the
		given node."""
		self.out.write("<%s" % tag)
		if node:
			cls = node.getInfo(doc.INFO_CLASS)
			if cls:
				self.out.write(" class=\"%s\"" % " ".join(cls))
			css = node.getInfo(doc.INFO_CSS)
			if css:
				self.out.write(" style=\"%s\"" % css)
			lang = node.getInfo(doc.INFO_LANG)
			if css:
				self.out.write(" lang=\"%s\"" % lang)
		if attrs:
			self.out.write(" ")
			self.out.write(" ".join(["%s=\"%s\"" % p for p in attrs]))
		self.out.write(">")

	def genCloseTag(self, tag):
		"""Generate a closing tag."""
		self.out.write("</%s>" % tag)

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
			item.get_term().gen(self)
			self.out.write("</dt><dd>")
			item.get_def().gen(self)
			self.out.write("</dd>")
		self.out.write("</dl>\n")

	def genStyleBegin(self, kind):
		tag, _ = getStyle(kind)
		self.out.write(tag)

	def genStyleEnd(self, kind):
		_, tag = getStyle(kind)
		self.out.write(tag)

	def genHeaderTitle(self, header):
		"""Generate the title of a header."""
		number = self.man.get_number(header)
		anchor = self.man.get_anchor(header)
		self.out.write('<h' + str(header.getHeaderLevel() + 1) + '>')
		if anchor != None:
			self.out.write('<a name="' + number + '"></a>')
		if number != None:
			self.out.write(number)
		header.genTitle(self)
		self.out.write('</h' + str(header.getHeaderLevel() + 1) + '>\n')

	def genHeader(self, header):
		"""Generate a whole header element (title + content)."""
		self.genHeaderTitle(header)
		header.genBody(self)
		return True

	def genLinkBegin(self, url):

		# process the URL
		if ":" in url:
			if url.startswith("mailto:"):
				url = "mailto:" + "".join(["&#x%x;" % ord(c) for c in url[7:]])
		else:
			self.man.add_resource(url, self.doc)
			url = self.man.get_resource_loc(url, self.doc)

		# generate the code
		self.out.write('<a href="%s">' % url)

	def genLinkEnd(self, url):
		self.out.write('</a>')

	def genImageTag(self, url, node, caption):
		self.out.write('<img src="' + url + '"')
		if node.get_width() != None:
			self.out.write(' width="%d"' % node.get_width())
		if node.get_height() != None:
			self.out.write(' height="%d"' % node.get_height())
		if caption != None:
			self.out.write(' alt="' + escape_attr(caption.toText()) + '"')
		self.out.write('/>')
		
	def genImage(self, url, node, caption):
		print("DEBUG: url=", url)
		if ":" in url:
			new_url = url
		else:
			self.man.add_resource(url, self.doc)
			new_url = self.man.get_resource_loc(url, self.doc)
		print("DEBUG: new_url=", new_url)
		self.genImageTag(new_url, node, caption)

	def genFigure(self, url, node, caption):
		align = node.getInfo(tdoc.INFO_ALIGN)
		self.out.write('<div class="figure"')
		if align == tdoc.ALIGN_LEFT:
			self.out.write(' style="text-align:center;float:left"')
		elif align == tdoc.ALIGN_RIGHT:
			self.out.write(' style="text-align:center;float:right"')
		else:
			self.out.write(' style="text-align:center"')
		self.out.write('>\n')
		self.genImageTag(new_url, node, caption)
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
				email = author['email']
				self.out.write('<a href="mailto:' + escape_attr(email) + '">')
			self.out.write(escape_cdata(author['name']))
			if email:
				self.out.write('</a>')		

	def genLabel(self, node):
		caption = node.get_caption()
		if caption or node in self.refs:
			self.out.write('<div class="label">')
			if node in self.refs:
				r = self.refs[node]
				self.out.write("<a name=\"%s\" class=\"label-ref\">%s</a>" % (r[1], self.trans.caption(node.numbering(), r[1])))
			if caption:
				for item in caption.getContent():
					item.gen(self)
			self.out.write('</div>')

	def genEmbeddedBegin(self, node):
		self.out.write('<div class="%s">' % node.numbering())
		self.genLabel(node)

	def genEmbeddedEnd(self, node):
		if self.label:
			self.genLabel(self.label)
		self.out.write('</div>')

	def genRef(self, ref):
		node = self.doc.getLabel(ref.label)
		if not node:
			common.onWarning("label\"%s\" cannot be resolved" % ref.label)
		else:
			r = self.refs[node]
			self.out.write("<a href=\"%s\">%s</a>" % (r[0], r[1]))

	def add_ref(self, node, anchor, number = ""):
		"""Add a new reference to the given node represented by
		the given anchor, possibly a number."""
		self.refs[node] = (anchor, number)
	
	def get_href(self, node):
		"""Get the hypertext reference corresponding to the given node."""
		return self.refs[node][0]

	def get_number(self, node):
		"""Get the reference number corresponding to the given node."""
		return self.refs[node][1]


# module description
__short__ = "common facilities by HTML back-end"
__description__ = """Cannot be used as a back-end per se."""
