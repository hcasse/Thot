"""This module provides an interface to implement different ways
to generate the output from one or several input files. This interface
provides a way to interface back-end with the organization of the output."""

import os
import os.path
import re
import shutil

from thot import common
import thot.doc

class Relocator:
	"""These objects take in charge the fact that a file has to be moved
	to some building directory. It may be used to relocate and fix
	associated file or special transformation due to this move."""

	def move(self, spath, tpath, loc, man):
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

	def relocate(self, spath, tpath, loc):
		"""Perform the relocation of a file resource."""
		try:
			reloc = os.path.splitext(spath)
			reloc.move(spath, tpath, loc, self)
		except KeyError:
			shutil.copystat(spath, tpath)

	def make_path(self, path, ref):
		"""Build an absolute path for the given path that may be relative to the document path. Doc may be None, a path or a document."""
		if os.path.isabs(path):
			return path
		elif ref == None:
			ref = self.base_dir
		elif isinstance(ref, thot.doc.Document):
			dpath = ref.env["THOT_FILE"]
			if dpath != "":
				ref = os.path.abspath(os.path.dirname(dpath))
			else:
				ref = self.base_dir
		return os.path.abspath(os.path.join(str(ref), path))

	def add_resource(self, path, ref = None):
		"""Add a resource in the currently build. Returns the actual path of the resource in the build. If the path is relative, it is relative to the ref that may be a document or a path to a file containing the relative path. If ref is None, it path is relative to the base directory of the manager."""
		return None

	def create_resource(self, ext, id = None):
		"""Add a new resource file. Return the actual path of the
		created resource. With an id, the same resource is returned
		and can be tested for the need of update."""
		return None

	def get_resource_loc(self, path, ref = None):
		"""Get the resource location to do a If ref is given, it may be a path the location has to be relative to."""
		return path

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

	def get_link(self, node, ref = None):
		"""Get the link to the given node. Return None if there is no link.
		If ref is given, the path is relative to the given path."""
		try:
			path = os.path.abspath(node._thot_path)
			anchor = node._thot_anchor
			if ref != None:
				ref = self.make_path(ref, self.base_dir)
				if path == ref:
					res = "#%s" % anchor
				else:
					res = "%s#%s" % (os.path.relpath(path, os.path.dirname(ref)), anchor)
			else:
				res = "%s#%s" % (os.path.relpath(path, self.base_dir), anchor)
		except AttributeError:
			res = None
		#print("DEBUG:", path, anchor, "ref", ref, "to", res)
		return res

	def declare_link(self, node, path, anchor = None):
		"""Declare a link to the given node."""
		if anchor == None:
			anchor = "thot-%d" % self.anchor_count
			self.anchor_count += 1
		node._thot_path = path
		node._thot_anchor = anchor

	def needs_update(self, res, doc):
		"""Test if the date of the resource is later than the date
		of the document path."""
		rdate = os.stat(res).st_mtime
		ddate = os.stat(doc).st_mtime
		return ddate > rdate


class LocalManager(Manager):
	"""Manager keeping local file in place and creates non-local and new resource in a directory named "ID-imports" to make easier the
	exportation of the generated files."""

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
			if not os.path.exists(self.impdir):
				os.mkdir(self.impdir)
			elif not os.path.isdir(self.impdir):
				n = 0
				while True:
					npath = "%s-%d" % (self.impdir, n)
					if not os.path.exists(npath):
						os.rename(self.impdir, npath)
						os.mkdir(self.impdir)
						break
					n += 1
		return self.impdir

	def get_resource_link(self, path):
		return os.path.relpath(path, self.base_dir)

	def create_resource(self, ext, id = None):
		impdir = self.get_import()
		if id != None:
			name = "@file-%d.%s" % (self.tmp, ext)
			self.tmp += 1
		else:
			name = "%s.%s" % (id, ext)
		path = os.path.join(impdir, name)
		return path

	def add_resource(self, path, doc):
		apath = os.path.abspath(path)
		if apath.startswith(self.base_dir):
			return apath
		else:
			impdir = self.get_import()
			dir, name = os.path.split(path)
			while name in self.used:
				dir, dname = os.path.split(dir)
				name = "%s-%s" % (dname, name)
			fpath = os.path.join(impdir, name)
			self.used.append(name)
			self.map[path] = fpath
			return fpath
