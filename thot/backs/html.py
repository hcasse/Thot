# html -- Thot html back-end
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

import html as my_html
import os
import re
import shutil
import sys
import urllib.parse as urlparse

import thot.back as back
import thot.backs.abstract_html as abstract_html
import thot.common as common
import thot.doc as doc
import thot.doc as tdoc
import thot.highlight as highlight
import thot.i18n as i18n

from thot.backs.abstract_html import escape_cdata
from thot.backs.abstract_html import escape_attr

def makeRef(nums):
	"""Generate a reference from an header number array."""
	return ".".join([str(i) for i in nums])

class PagePolicy:
	"""A page policy allows to organize the generated document
	according the preferences of the user."""
	gen = None
	page = None

	def __init__(self, gen, page):
		self.gen = gen
		self.page = page

	def onHeaderBegin(self, header):
		pass

	def onHeaderEnd(self, header):
		pass

	def unfolds(self, header):
		return True

	def ref(self, header, number):
		return	"#" + number

	def gen_header(self, gen):
		gen.gen_header()
		# out = gen.out
		# styles = gen.doc.getVar("HTML_STYLES")
		# if styles:
			# for style in styles.split(':'):
				# if style == "":
					# continue
				# new_style = gen.importCSS(style)
				# out.write('	<link rel="stylesheet" type="text/css" href="' + new_style + '">\n')
		# short_icon = gen.doc.getVar('HTML_SHORT_ICON')
		# if short_icon:
			# out.write('<link rel="shortcut icon" href="%s"/>' % short_icon)
		# self.gen.genScripts()

	def get_file(self, node):
		"""Return the file name containing the given node."""
		return ""

	
class AllInOne(PagePolicy):
	"""Simple page policy doing nothing: only one page."""

	def __init__(self, gen, page):
		PagePolicy.__init__(self, gen, page)

	def genRefs(self):
		"""Generate and return the references for the given generator."""
		self.gen.refs = { }
		self.makeRefs([1], { }, self.gen.doc)

	def makeRefs(self, nums, others, node):
		"""Traverse the document tree and generate references in the given map."""
		
		# number for header
		num = node.numbering()
		if num == 'header':
			r = makeRef(nums)
			self.gen.add_ref(node, "#%s" % r, r)
			nums.append(1)
			for item in node.getContent():
				self.makeRefs(nums, others, item)
			nums.pop()
			nums[-1] = nums[-1] + 1
		
		# number for embedded
		else:
			
			# set number
			if self.gen.doc.getLabelFor(node):
				if num:
					if num not in others:
						others[num] = 1
						n = 1
					else:
						n = others[num] + 1
					self.gen.add_ref(node, "#%s-%d" % (num, n), str(n))
					others[num] = n
		
			# look in children
			for item in node.getContent():
				self.makeRefs(nums, others, item)
	
	def gen_title(self, gen):
		gen.genTitleText()
	
	def gen_authors(self, gen):
		gen.genAuthors()

	def gen_menu(self, gen):
		self.gen.genContent([], 100)
		
	def gen_content(self, gen):
		self.gen.genBody()		

	def run(self):
		self.gen.openMain('.html')
		self.genRefs()
		self.gen.doc.pregen(self.gen)
		self.page.apply(self, self.gen)


class PerSection(PagePolicy):
	"""This page policy ensures there is one page per section."""

	def __init__(self, gen, page):
		PagePolicy.__init__(self, gen, page)

	def genRefs(self):
		"""Generate and return the references for the given generator."""
		self.gen.refs = { }
		self.makeRefs([1], { }, self.gen.doc, -1)

	def page_name(self, page):
		"""Compute the page name."""
		if page < 0:
			return "%s.html" % self.gen.root
		else:
			return "%s-%d.html" % (self.gen.root, page)

	def makeRefs(self, nums, others, node, page):
		"""Traverse the document tree and generate references in the given map."""
		
		# number for header
		num = node.numbering()
		if num == 'header':
			page = page + 1
			self.gen.add_ref(node, self.page_name(page), makeRef(nums))
			nums.append(1)
			for item in node.getContent():
				page = self.makeRefs(nums, others, item, page)
			nums.pop()
			nums[-1] = nums[-1] + 1
		
		# number for embedded
		else:
			
			# set number
			if num and self.gen.doc.getLabelFor(node):
				if num not in others.has_key:
					others[num] = 1
					n = 1
				else:
					n = others[num] + 1
				r = str(n)
				self.gen.add_ref(node, "%s#%s-%s" % (self.page_name(page), num, r), r)
				others[num] = n
		
			# look in children
			for item in node.getContent():
				page = self.makeRefs(nums, others, item, page)

		return page

	def process(self, header):

		# generate the page
		self.gen.openPage(header)
		self.path = self.path + [header]
		self.page.apply(self, self.gen)
		print("generated %s" % (self.gen.getPage(header)))
		
		# generate the su-headers
		for child in header.getContent():
			if child.getHeaderLevel() >= 0:
				self.process(child)
		self.path.pop()
		
	path = []
	
	def gen_title(self, gen):
		gen.genTitleText()
	
	def gen_authors(self, gen):
		gen.genAuthors()

	def gen_menu(self, gen):
		if not self.path:
			gen.genContent([], 0)
		else:
			gen.genContent(self.path, 100)
		
	def gen_content(self, gen):
		if not self.path:
			for node in self.gen.doc.getContent():
				if node.getHeaderLevel() != 0:
					node.gen(gen)
		else:
			for h in self.path:
				gen.genHeaderTitle(h)
			for child in self.path[-1].getContent():
				if child.getHeaderLevel() < 0:
					child.gen(gen)

	def run(self):
		
		# preparation
		self.gen.openMain('.html')
		self.gen.doc.pregen(self.gen)
		self.genRefs()

		# generate page
		self.page.apply(self, self.gen)
		print("generated %s" % self.gen.path)

		# generate chapter pages
		for node in self.gen.doc.getContent():
			if node.getHeaderLevel() == 0:
				self.process(node)


class PerChapter(PagePolicy):
	"""This page policy ensures there is one page per chapter."""
	node = None
	
	def __init__(self, gen, page):
		PagePolicy.__init__(self, gen, page)

	def genRefs(self):
		"""Generate and return the references for the given generator."""
		self.gen.refs = { }
		self.makeRefs([1], { }, self.gen.doc, self.gen.root + ".html")

	def makeRefs(self, nums, others, node, page):
		"""Traverse the document tree and generate references in the given map."""
		
		# number for header
		num = node.numbering()
		if num == 'header':
			if node.header_level == 0:
				page = "%s-%d.html" % (self.gen.root, nums[0] - 1)
				self.gen.add_ref(node, page, str(nums[0]))
			else:
				r = makeRef(nums)
				self.gen.add_ref(node, "%s#%s" % (page, r), r)
			nums.append(1)
			for item in node.getContent():
				self.makeRefs(nums, others, item, page)
			nums.pop()
			nums[-1] = nums[-1] + 1
		
		# number for embedded
		else:
			
			# set number
			if num and self.gen.doc.getLabelFor(node):
				if num not in others:
					others[num] = 1
					n = 1
				else:
					n = others[num] + 1
				r = str(n)
				self.gen.add_ref(node, "%s#%s-%s" % (page, num, r), r)
				others[num] = n
		
			# look in children
			for item in node.getContent():
				self.makeRefs(nums, others, item, page)
	
	def gen_title(self, gen):
		gen.genTitleText()
	
	def gen_authors(self, gen):
		gen.genAuthors()

	def gen_menu(self, gen):
		if not self.node:
			self.gen.genContent([], 0)
		else:
			self.gen.genContent([self.node], 100)
		
	def gen_content(self, gen):
		if not self.node:		
			for node in self.gen.doc.getContent():
				if node.getHeaderLevel() != 0:
					node.gen(gen)
		else:
			self.node.gen(self.gen)

	def run(self):
		chapters = []

		# generate main page
		self.gen.openMain('.html')
		self.genRefs()
		self.gen.doc.pregen(self.gen)
		for node in self.gen.doc.getContent():
			if node.getHeaderLevel() == 0:
				chapters.append(node)
		self.page.apply(self, self.gen)
		print("generated %s" % self.gen.path)

		# generate chapter pages
		for node in chapters:
			self.gen.openPage(node)
			self.node = node
			self.page.apply(self, self.gen)
			self.gen.closePage()
			print("generated %s" % (self.gen.getPage(node)))


class Generator(abstract_html.Generator):
	"""Generator for HTML output."""

	def __init__(self, doc):
		abstract_html.Generator.__init__(self, doc)

	def getType(self):
		return 'html'

	def genTitleText(self):
		"""Generate the text of the title."""
		self.out.write(escape_cdata(self.doc.getVar('TITLE')))
	
	def genTitle(self):
		self.out.write('<div class="header">\n')
		self.out.write('	<div class="title">')
		self.genTitleText()
		self.out.write('</div>\n')
		self.out.write('	<div class="authors">')
		self.genAuthors()
		self.out.write('</div>\n')
		self.out.write('</div>')

	def genBodyHeader(self):
		self.out.write('<div class="page">\n')

	def genBodyFooter(self):
		self.out.write('</div>\n')

	def genBody(self):
		self.genBodyHeader()
		self.doc.gen(self)
		#self.genFootNotes()
		self.genBodyFooter()

	def genFooter(self):
		self.out.write("</div>\n</body>\n</html>\n")

	def genContentEntry(self, node, indent):
		"""Generate a content entry (including numbering, title and link)."""
		self.out.write('%s<a href="%s">' % (indent, self.get_href(node)))
		self.out.write(self.get_number(node))
		self.out.write(' ')
		node.genTitle(self)
		self.out.write('</a>\n')

	def expandContent(self, node, level, indent):
		"""Expand recursively the content and to the given level."""
		if node.getHeaderLevel() >= level:
			return
		one = False
		for child in node.getContent():
			if child.getHeaderLevel() >= 0:
				if not one:
					one = True
					self.out.write('%s<ul class="toc">\n' % indent)
				self.out.write("%s<li>\n" % indent)
				self.genContentEntry(child, indent)
				self.expandContent(child, level, indent + "  ")
				self.out.write("%s</li>\n" % indent)
		if one:
			self.out.write('%s</ul>\n' % indent)

	def expandContentTo(self, node, path, level, indent):
		"""Expand, not recursively, the content until reaching the end of the path.
		From this, expand recursively the sub-nodes."""
		if not path:
			self.expandContent(node, level, indent)
		else:
			one = False
			for child in node.getContent():
				if child.getHeaderLevel() >= 0:
					if not one:
						one = True
						self.out.write('%s<ul class="toc">\n' % indent)
					self.out.write("%s<li>\n" % indent)
					self.genContentEntry(child, indent)
					if path[0] == child:
						self.expandContentTo(child, path[1:], level, indent + '  ')
					self.out.write("%s</li>\n" % indent)
			if one:
				self.out.write('%s</ul>\n' % indent)
				
	def genContent(self, path, level):
		"""Generate the content without expanding until ending the path
		(of headers) with an expanding maximum level.
		"""
		self.out.write('<div class="toc">\n')
		self.out.write('<h1><a name="toc">' + escape_cdata(self.trans.get(i18n.ID_CONTENT)) + '</name></h1>\n')
		self.expandContentTo(self.doc, path, level, '  ')
		self.out.write('</div>\n')

	def getPage(self, header):
		if header not in self.pages:
			self.pages[header] = "%s-%d.html" % (self.root, self.page_count)
			self.page_count += 1
		return self.pages[header]

	def openPage(self, header):
		path = self.getPage(header)
		self.stack.append((self.out, self.footnotes))
		self.out = open(path, 'w')
		self.footnotes = []

	def closePage(self):
		self.out.close()
		self.out, self.footnotes = self.stack.pop()

	def run(self):

		# select the policy
		template = self.getTemplate()
		self.struct = self.doc.getVar('HTML_ONE_FILE_PER')
		if self.struct == 'document' or self.struct == '':
			policy = AllInOne(self, template)
		elif self.struct == 'chapter':
			policy = PerChapter(self, template)
		elif self.struct == 'section':
			policy = PerSection(self, template)
		else:
			common.onError('one_file_per %s structure is not supported' % self.struct)

		# generate the document
		policy.run()
		print("SUCCESS: result in %s" % self.path)


def output(doc):
	gen = Generator(doc)
	gen.run()

__short__ = "back-end for HTML output"
__description__ = \
"""Produces one or several HTML files. Auxiliary files (images, CSS, etc)
are stored in a directory named DOC-imports where DOC corresponds to the
the processed document DOC.thot.

Following variables are supported:
""" + common.make_var_doc([
	("HTML_ONE_FILE_PER",	"generated files: one of document (default), chapter, section"),
	("HTML_SHORT_ICON",		"short icon path for HTML file"),
	("HTML_STYLES",			"CSS styles to use (':' separated)"),
	("HTML_TEMPLATE",		"template used to generate pages")
])
