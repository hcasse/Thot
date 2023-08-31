"""This module provides an interface to implement different ways
to generate the output from one or several input files. This interface
provides a way to interface back-end with the organization of the output."""

import os
import os.path
import re
import shutil

from thot import common
from thot import back
import thot.doc

class Relocator:
	"""These objects take in charge the fact that a file has to be moved
	to some building directory. It may be used to relocate and fix
	associated file or special transformation due to this move."""

	def move(self, spath, tpath, man):
		"""Move the file from source path to the target path.
		For information, location used for links and manager are
		given.

		If there is an error, must raise a BackException."""
		pass


class CSSRelocator(Relocator):
	"""Relocator for CSS files."""

	CSS_URL_RE = re.compile('url\(([^)]*)\)')

	def __init__(self):
		Relocator.__init__(".css")

	def move(self, opath, tpath, loc, man):

		# open files
		try:
			input = open(opath)
		except FileNotFoundError as e:
			raise common.BackException(str(e))
		output = open(tpath, "w")
		rbase = os.path.dirname(tpath)

		# perform the copy
		for line in input:
			m = CSSRelocator.CSS_URL_RE.search(line)
			while m:
				output.write(line[:m.start()])
				url = m.group(1)
				res = urlparse.urlparse(url)
				if res[0]:
					output.write(m.group())
				else:
					rpath = man.add_resource(res[2])
					rpath = os.path.relpath(rpath, rbase)
					output.write("url(%s)" % rpath)
				line = line[m.end():]
				m = CSSRelocator.CSS_URL_RE.search(line)
			output.write(line)



class Manager:
	"""Manage the resources used during the generation.

	Useful attributes include:
	* base_dir -- Directory path for relative paths in the document system."""

	def __init__(self, base_dir = None):
		self.relocs = { ".css": CSSRelocator() }
		if base_dir == None:
			self.base_dir = os.path.abspath(os.getcwd())
		else:
			self.base_dir = base_dir
		self.anchor_count = 0

	def add_relocator(self, ext, reloc):
		"""Add a new relocator."""
		self.relocs[ext] = reloc

	def relocate(self, spath, tpath):
		"""Perform the relocation of a file resource spath
		to the file tpath."""
		try:
			reloc = self.relocs[os.path.splitext(spath)]
			reloc.move(spath, tpath, loc, self)
		except KeyError:
			shutil.copystat(spath, tpath)

	def get_build_path(self, path):
		"""Get the actual build path for the resource identified by
		the given path. This is a good location for special processing
		of paths before making links."""
		return os.path.abspath(path)

	def use_resource(self, path):
		"""Add a resource in the currently build. Returns the actual build path of the resource in the build. If needed for the type of build, the resource may be copied."""
		return None

	def make_resource(self, ext = None, id = None):
		"""Make a new resource file. Return the actual build path of the
		created resource. With an id, the same resource is returned
		and can be tested for the need of update."""
		return None

	def get_resource_link(self, path, gen):
		"""Get the resource link to do an hyper-reference that is made relative to the given generator."""
		bpath = self.get_build_path(path)
		gpath = os.path.dirname(self.)
		return os.path.relpath(bpath, os.path.dirname(gen.get_build_path()))

	def declare_number(self, node, number):
		"""Record the assignment of a number to a node."""
		node._thot_number = number

	def get_number(self, node):
		"""Get the number for a node that can support it. Return number
		if there is one or None."""
		try:
			return node._thot_number
		except AttributeError:
			return None

	def get_anchor(self, node):
		"""Get the anchor of the node (if any)."""
		try:
			return node._thot_anchor
		except AttributeError:
			return None

	def get_link(self, node, gen):
		"""Get the link to the given node. Return None if there is no link.
		If ref is given, the path is relative to the given path."""
		try:
			path = self.get_resource_link(node._thot_path, gen)
			anchor = node._thot_anchor
			if path == '.':
				res = "#%s" % anchor
			else:
				res = "%s#%s" % (path, anchor)
		except AttributeError:
			res = None
		return res

	def declare_link(self, node, path, anchor = None):
		"""Declare a link to the given node with the given build path."""
		if anchor == None:
			anchor = "thot-%d" % self.anchor_count
			self.anchor_count += 1
		node._thot_path = path
		node._thot_anchor = anchor

	def needs_update(self, res, doc):
		"""Test if the date of the resource is later than the date of the document path."""
		rdate = os.stat(res).st_mtime
		ddate = os.stat(doc).st_mtime
		return ddate > rdate


class LocalManager(Manager):
	"""Manager keeping local file in place and creates non-local and new resource in a directory named "ID-imports" to make easier the exportation of the generated files."""

	def __init__(self, id, base_dir = None):
		Manager.__init__(self, base_dir)
		self.id = id
		self.map = {}
		self.used = []
		self.impdir = None
		self.tmp = 0

	def get_import(self):
		"""Get and create the import directory."""
		if self.impdir == None:
			self.impdir = os.path.join(self.base_dir, "%s-imports" % self.id)
			done = False
			if not os.path.exists(self.impdir):
				try:
					os.mkdir(self.impdir)
					done = True
				except (FileExistsError, FileNotFoundError):
					pass
			if not done:
				common.onError("cannot create import directory: %s" % self.impdir)
		return self.impdir

	def make_resource(self, ext = None, id = None):
		impdir = self.get_import()
		if id == None:
			name = "+file-%d.%s" % (self.tmp, ext)
			self.tmp += 1
		elif ext == None:
			name = id
		else:
			name = "%s.%s" % (id, ext)
		path = os.path.join(impdir, name)
		return path

	def use_resource(self, path):
		try:
			apath = os.path.abspath(path)
			return self.map[apath]
		except KeyError:
			if apath.startswith(self.base_dir):
				self.map[apath] = apath
				return apath
			else:
				impdir = self.get_import()
				dir, name = os.path.split(path)
				while name in self.used:
					dir, dname = os.path.split(dir)
					name = "%s-%s" % (dname, name)
				fpath = os.path.join(impdir, name)
				self.used.append(name)
				self.map[apath] = fpath
				self.relocate(path, fpath)
				return fpath

	def get_build_path(self, path):
		apath = os.path.abspath(path)
		return self.map[apath]
		
