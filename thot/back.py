# back -- Thot commmon back-end structure
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

"""
Definition of the abstract class back.Generator to help generation
of output files.
"""

import os.path
import shutil
import sys

from thot import common
from thot import i18n

STDOUT = "<stdout>"


class Manager:
	"""The manager is in charge of organizing where to put files invovled in
	the building of a document."""

	def __init__(self, mon = common.DEFAULT_MONITOR):
		self.mon = mon

	def is_interactive(self):
		"""Called to test if the page will be served by an HTTP server implemented
		by Thot. This allows to pass custom commands to Thot. Default implementation
		returns false."""
		return False

	def use_resource(self, path):
		"""Inform the manager that a file path is used. It returns the path
		of the resource as used in the building. Notice that this call
		can be performed on the same used path and will return the same
		build path in this case."""
		return None

	def new_resource(self, path = None, ext = None):
		"""Create a new resource to be used in the bulding of the project.
		Returns  the build path. id is the path of the created resource;
		if path is none, a file a created with the given extension."""
		return None

	def relocate(self, spath, dpath):
		"""Called to relocate a used path (spath) )into the current build path (dpath).
		The default implementation just copies the file. Raise BackException
		if there is an error."""
		try:
			shutil.copyfile(spath, dpath)
			shutil.copystat(spath, dpath)
		except FileNotFoundError:
			raise common.BackException(f"file not found: {spath}")

	def get_resource_path(self, path, ref = None):
		"""Get a resource path to be used in the given reference source
		(if provided) or general for the manager.
		The default implementation returns an absolute path."""
		return os.path.abspath(path)

	def ensure_dir(self, dir):
		"""Ensure that the given directory is built.
		Raise a BackException in the reverse case."""
		if not os.path.exists(dir):
			try:
				os.makedirs(dir)
			except OSError as e:
				raise common.BackException(f"cannot create {dir}: {e}")
		elif not os.path.isdir(dir):
			raise common.BackException(f"{dir} is not a directory")


class LocalManager(Manager):
	"""A manager that keeps local files (in the same directory as output) as is
	and creates new files and move non-local files in a devoted directory named
	import directory and derived from the output path PATH by adding suffixing it
	with "imports"."""


	def __init__(self, out_path, mon = common.DEFAULT_MONITOR):
		Manager.__init__(self, mon = mon)
		self.out_dir = os.path.dirname(out_path)
		self.import_dir = os.path.splitext(out_path)[0] + "-imports"
		self.import_done = False
		self.map = { }
		self.tmp = 0
		self.used = []

	def get_import(self):
		"""Get the import directory and ensures it exists."""
		if not self.import_done:
			self.ensure_dir(self.import_dir)
			self.import_done = True
		return self.import_dir

	def new_resource(self, path = None, ext = None):
		if path is None:
			path = f"+file-{self.tmp}.{ext}"
			self.tmp += 1
		path = os.path.join(self.get_import(), path)
		dpath = os.path.dirname(path)
		self.ensure_dir(dpath)
		return path

	def use_resource(self, path):
		try:
			apath = os.path.abspath(path)
			return self.map[apath]
		except KeyError:
			if apath.startswith(os.path.abspath(self.out_dir)):
				self.map[apath] = apath
				return apath
			else:
				dir, name = os.path.split(path)
				while name in self.used:
					dir, dname = os.path.split(dir)
					name = f"{dname}-{name}"
				fpath = os.path.join(self.get_import(), name)
				self.used.append(name)
				self.map[apath] = fpath
				self.relocate(path, fpath)
				return fpath

	def get_resource_path(self, path, ref = None):
		path = os.path.abspath(path)
		if ref is None:
			return path
		else:
			gpath = os.path.dirname(ref)
			rpath = os.path.relpath(path, gpath)
			return rpath


class Generator:
	"""Abstract back-end generator."""
	manager = None
	doc = None
	out_path = None
	base_path = None
	import_path = None
	trans = None
	out = None
	tmp = -1

	def __init__(self, doc, manager = None, out = None):
		"""Build the abstract generator.
		doc -- document to generate."""
		self.doc = doc
		self.out = out
		self.trans = i18n.getTranslator(self.doc)
		if manager is not None:
			self.manager = manager
		else:
			self.manager = LocalManager(self.get_out_path())

	def getType(self):
		"""Get type of the back-end: html, latex, xml."""
		return None

	def get_out_ext(self):
		"""Get extension of the generated file (prefixed by ".")."""
		return ""

	def get_out_path(self):
		"""Get the path to the generated file."""
		if self.out_path is None:
			self.out_path = self.doc.getVar("THOT_OUT_PATH")
			if self.out_path == "":
				in_path = self.doc.getVar("THOT_FILE")
				if in_path == "":
					self.out_path = STDOUT
				else:
					self.out_path = os.path.splitext(in_path)[0] + self.get_out_ext()
		return self.out_path

	def get_base_path(self):
		"""Get the base path, that is, the directory that contains the input.
		If input is <stdin>, the current directory."""
		if self.base_path is None:
			in_path = self.doc.getVar("THOT_FILE")
			if in_path == "":
				self.base_path = os.getcwd()
			else:
				self.base_path = os.path.dirname(in_path)
		return self.base_path

	def get_import_dir(self):
		"""Get the directory containing the imports."""
		return self.manager.get_import()

	def openMain(self):
		"""Create and open an out file for the given document."""
		if self.out is None:
			out_path = self.get_out_path()
			if out_path == STDOUT:
				self.out = sys.stdout
			else:
				self.out = open(self.get_out_path(), "w", encoding="utf8")

	def closeMain(self):
		"""Close the main output."""
		if self.get_out_path() != STDOUT:
			self.out.close()
			self.out =None

	def use_resource(self, path):
		"""Declare a used resource in the generation of the current
		document."""
		return self.manager.use_resource(path)

	def new_resource(self, path = None, ext = None):
		"""Create a new resource used in the generation of the current
		document."""
		return self.manager.new_resource(path, ext)

	def get_resource_path(self, path):
		"""Get a resource path relative to the current document."""
		return self.manager.get_resource_path(path, self.get_out_path())

	# Node generation functions

	def genFootNote(self, note):
		pass

	def genQuoteBegin(self, level):
		pass

	def genQuoteEnd(self, level):
		pass

	def genTable(self, table):
		"""Called when a table need to be generated."""
		pass

	def genHorizontalLine(self):
		pass

	def genVerbatim(self, line):
		"""Put the given line as is in the generated code.
		The output line must meet the conventions of the output language."""
		pass

	def genText(self, text):
		"""Put the given text as normal in the output, possibly escaping some
		character to maintain right display."""
		pass

	def genParBegin(self):
		pass

	def genParEnd(self):
		pass

	def genList(self, list):
		"""Generate output for a list."""
		pass

	def genDefList(self, deflist):
		"""Called to generate a definition list."""
		pass

	def genStyleBegin(self, kind):
		"""Generate for beginning of a style. kind is one of doc.STYLE_XXX constant."""
		pass

	def genStyleEnd(self, kind):
		"""Generate for ending of a style. kind is one of doc.STYLE_XXX constant."""
		pass

	def genHeader(self, header):
		return False

	def genHeaderBegin(self, level):
		pass

	def genHeaderTitleBegin(self, level):
		pass

	def genHeaderTitleEnd(self, level):
		pass

	def genHeaderBodyBegin(self, level):
		pass

	def genHeaderBodyEnd(self, level):
		pass

	def genHeaderEnd(self, level):
		pass

	def genLinkBegin(self, url, title = None):
		"""Called to generate the entry tag for a link."""
		pass

	def genLinkEnd(self, url):
		"""Called to generate the exit tag for a link."""
		pass

	def genImage(self, url, node, caption):
		pass

	def genFigure(self, url, node, caption):
		"""Generate a figure made of an image."""
		pass

	def genGlyph(self, code):
		pass

	def genLineBreak(self):
		pass

	def genEmbeddedBegin(self, node):
		"""Start an embedded area with the given label (a paragraph).
		Usual kinds include "listing", "figure", "table", "algo"."""
		pass

	def genEmbeddedEnd(self, node):
		"""End of generation for an embedded."""
		pass

	def genRef(self, ref):
		"""Called to generate a reference."""
		pass

	def gen_line_break(self):
		"""Generate a line break."""
		pass

	def get_prefix(self, node):
		if node is None:
			return ""
		else:
			return node.getFileLine()

	def info(self, msg, *args, node = None):
		"""Display an information message."""
		self.manager.mon.info(self.get_prefix(node) + msg, *args)

	def warn(self, msg, *args, node = None):
		"""Display a warning with file and line."""
		self.manager.mon.warn(self.get_prefix(node) + msg, *args)

	def error(self, msg, *args, node = None):
		"""Display an error with file and line."""
		self.manager.mon.error(self.get_prefix(node) + msg, *args)

	def run(self):
		"""Perform the generation of the document."""
		pass

	def translate(self, text):
		"""Ask for a translation in the current language of the document."""
		return self.trans.get(text)


def get_output(doc):
	"""Get the output for the passed document.
	Raises a ThotException if there is an error."""
	out_name = doc.env["THOT_OUT_TYPE"]
	out_path = os.path.join(doc.env["THOT_LIB"], "backs")
	back = common.loadModule(out_name,  out_path)
	if back is None:
		raise common.ThotException(f"cannot load back-end  {out_name} at {out_path}")
	else:
		return back

