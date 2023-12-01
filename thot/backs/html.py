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

import os

import thot.back as back
import thot.backs.abstract_html as abstract_html
import thot.common as common
import thot.doc as doc
import thot.i18n as i18n

from thot.backs.abstract_html import escape_cdata, escape_attr

def makeRef(nums):
	"""Generate a reference from an header number array."""
	return ".".join([str(i) for i in nums])

class LocalManager(back.LocalManager, abstract_html.Manager):
	"""Manager for HTML storing additional file in an import directory."""

	def __init__(self, out_path, mon = common.DEFAULT_MONITOR):
		abstract_html.Manager.__init__(self, mon = mon)
		back.LocalManager.__init__(self, out_path)


class PagePolicy:
	"""A page policy allows to organize the generated document
	according the preferences of the user.

	The page policy supports also numbering and recording of links
	of numbered nodes. Numbered nodes may be header (identifier by
	the level as integer or other elements recorded by a string identifier).
	Numbering are basically starting at 0."""

	def __init__(self, gen, page):
		self.gen = gen
		self.page = page
		self.man = gen.get_manager()
		self.nums = {}
		self.file = None
		self.file_stack = []
		self.hnums = None

	def get_number(self, node):
		"""Get the number for the given node or create it reset to 0."""
		type = node.numbering()
		try:
			return self.nums[type]
		except KeyError:
			self.nums[type] = 0
			return 0

	def assign_number(self, node, type):
		"""Produce a new number for the given type. For an header
		number, the numbers for lower header are reset."""

		# compute number
		try:
			num = self.nums[type]
			num = num + 1
			if isinstance(type, int):
				for i in range(type+1, 7):
					if i not in self.nums:
						break;
					else:
						del self.nums[i]
		except KeyError:
			num = 0
		self.nums[type] = num

		# declare the link
		self.man.declare_link(node, self.file)

		# build the number
		if not isinstance(type, int):
			return str(num + 1)
		else:
			if self.hnums == None:
				self.hnums = str(num + 1)
			else:
				self.hnums = "%s.%s" % (self.hnums, num + 1)
		self.man.declare_number(node, self.hnums)

	def push_file(self, path):
		"""Record the given file for the next reference generation."""
		self.file_stack.append(self.file)
		self.file = path

	def pop_file(self):
		"""Pop the currently generated file and return to the previous
		one."""
		self.file = self.file_stack.pop()

	def enter_header(self, node):
		"""Called each time an header is entered."""
		pass

	def leave_header(self, node):
		"""Called each time an header is left."""
		pass

	def format_number(self, node):
		"""Called to format the number of the given node."""
		num = node.numbering()
		if num == None:
			return None

	def make_numbers(self, node):
		"""Assign numbers to the given nodes and nodes below."""
		num = node.numbering()

		# no numbering or a document
		if num == None:
			if isinstance(node, doc.Document):
				for item in node.getContent():
					self.make_numbers(item)

		# header or numbered embedded
		else:
			if isinstance(num, int):
				old_hnums = self.hnums
				self.enter_header(node)
			self.assign_number(node, num)
			if isinstance(node, doc.Container):
				for item in node.getContent():
					self.make_numbers(item)
			if isinstance(num, int):
				self.leave_header(node)
				self.hnums = old_hnums

	def get_link(self, node):
		"""Get a link to the given node."""
		return self.man.get_link(node, self.file)

	def gen_header(self, gen):
		gen.gen_header()
		out = gen.out
		short_icon = gen.doc.getVar('HTML_SHORT_ICON')
		if short_icon:
			out.write('<link rel="shortcut icon" href="%s"/>' % short_icon)
		self.gen.gen_header_embedded()

	
class AllInOne(PagePolicy):
	"""Simple page policy doing nothing: only one page."""

	def __init__(self, gen, page):
		PagePolicy.__init__(self, gen, page)

	def gen_title(self, gen):
		gen.genTitleText()
	
	def gen_authors(self, gen):
		gen.genAuthors()

	def gen_menu(self, gen):
		self.gen.genContent([], 100)
		
	def gen_content(self, gen):
		self.gen.genBody()		

	def run(self):
		self.gen.openMain()
		self.file = os.path.abspath(self.gen.get_out_path())
		self.make_numbers(self.gen.doc)
		self.gen.doc.pregen(self.gen)
		self.page.apply(self, self.gen)


class PerChapter(PagePolicy):
	"""This page policy ensures there is one page per chapter."""

	def __init__(self, gen, page):
		PagePolicy.__init__(self, gen, page)
		self.todo = []
		self.current = None

	def page_name(self, page):
		"""Compute the page name."""
		if page < 0:
			return "%s.html" % self.gen.get_out_path()
		else:
			return "%s-%d.html" % (os.path.splitext(self.gen.get_out_path())[0], page)

	def enter_header(self, header):
		if header.getHeaderLevel() == 0:
			name = self.page_name(len(self.todo))
			self.push_file(name)
			self.todo.append((name, header))

	def leave_header(self, header):
		if header.getHeaderLevel() == 0:
			self.pop_file()

	def gen_title(self, gen):
		gen.genTitleText()
	
	def gen_authors(self, gen):
		gen.genAuthors()

	def gen_menu(self, gen):
		if self.current == None:
			gen.genContent([], 0)
		else:
			gen.genContent([self.current], 100)
		
	def gen_content(self, gen):
		if self.current == None:
			for node in self.gen.doc.getContent():
				if node.getHeaderLevel() != 0:
					node.gen(gen)
		else:
			self.current.gen(gen)

	def run(self):

		# preparation
		self.gen.openMain()
		self.file = os.path.abspath(self.gen.get_out_path())
		self.make_numbers(self.gen.doc)
		self.gen.doc.pregen(self.gen)

		# generate first page
		self.page.apply(self, self.gen)
		self.gen.info("generated %s", self.gen.get_out_path())

		# generate chapter pages
		for (name, header) in self.todo:
			self.current = header
			self.gen.openPage(name)
			self.page.apply(self, self.gen)
			self.gen.info("generated %s", name)


class PerSection(PerChapter):

	def __init__(self, gen, page):
		PerChapter.__init__(self, gen, page)
		self.header_stack = []

	def enter_header(self, header):
		name = self.page_name(len(self.todo))
		self.push_file(name)
		self.todo.append((name, header))
		self.header_stack.append(header)
		header.header_stack = list(self.header_stack)

	def leave_header(self, header):
		self.pop_file()
		self.header_stack.pop()

	def gen_menu(self, gen):
		if self.current == None:
			gen.genContent([], 0)
		else:
			gen.genContent(self.current.header_stack, 100)
	
	def gen_content(self, gen):

		# get content
		if self.current == None:
			content = self.gen.doc.getContent()			
		else:
			content = self.current.getContent()
			self.gen.genHeaderTitle(self.current)
			
		# print the content
		for node in content:
			if node.getHeaderLevel() < 0:
				node.gen(self.gen)
			else:
				self.gen.genHeaderTitle(node, self.gen.get_href(node))


POLICIES = {
	'': AllInOne,
	'document': AllInOne,
	'chapter': 	PerChapter,
	'section':	PerSection
}

class Generator(abstract_html.Generator):
	"""Generator for HTML output."""

	def __init__(self, doc, mon):
		abstract_html.Generator.__init__(self, doc)
		self.manager = LocalManager(self.get_out_path(), mon = mon)

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
		self.genBodyFooter()

	def genFooter(self):
		self.out.write("</div>\n</body>\n</html>\n")

	def get_href(self, node):
		return self.manager.get_link(node, self)

	def genContentEntry(self, node, indent):
		"""Generate a content entry (including numbering, title and link)."""
		self.out.write('%s<a href="%s">' % (indent, self.manager.get_link(node, self)))
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

	def openPage(self, path):
		self.out_path = os.path.abspath(path)
		self.out = open(path, 'w')
		self.footnotes = []

	def closePage(self):
		self.out.close()

	def run(self):

		# select the policy
		template = self.getTemplate()
		self.struct = self.doc.getVar('HTML_ONE_FILE_PER')
		try:
			policy = POLICIES[self.struct](self, template)
		except KeyError:
			self.error('one_file_per %s structure is not supported', self.struct)

		# generate the document
		policy.run()
		self.manager.mon.succeed("result in %s", self.get_out_path())


def output_ext(doc, mon):
	gen = Generator(doc, mon = mon)
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
