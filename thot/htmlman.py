"""This module provides an interface to implement different ways
to generate the output from one or several input files. This interface
provides a way to interface back-end with the organization of the output."""

import os
import os.path
import re
import shutil

from thot import common

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
	"""Manage the resources used during the generation."""

	def __init__(self):
		self.relocs = { ".css": CSSRelocator() }

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

	def add_resource(self, path, doc = None):
		"""Add a friend file to the output. Returns the actual path of the friend file. If doc is given and the resource path is relative, it is relative to the path of the document."""
		return None

	def create_resource(self, ext, id = None):
		"""Add a new resource file. Return the actual path of the
		created resource. With an id, the same resource is returned
		and can be tested for the need of update."""
		return None

	def get_resource_loc(self, path, doc = None):
		"""Get the resource location to do a link. This location may
		be relative to the given document."""
		return path

	def get_number(self, node):
		"""Get the number for a node that can support it. Return number
		if there is one or None."""
		return None

	def get_anchor(self, node):
		"""Get the anchor of the node (if any)."""
		return None

	def get_link(self, node):
		"""Get the link to the given node."""
		return None

	def needs_update(self, res, doc):
		"""Test if the date of the resource is later than the date
		of the document path."""
		rdate = os.stat(res).st_mtime
		ddate = os.stat(doc).st_mtime
		return ddate > rdate


class LocalManager(Manager):
	"""Manager keeping local file in place and creates non-local and new resource in a directory named "ID-imports" to make easier the
	exportation of the generated files."""

	def __init__(self, id, outdir = None):
		self.id = id
		if outdir != None:
			self.outdir = os.path.abspath(outdir)
		else:
			self.outdir = os.path.abspath(os.getcwd())
		self.map = {}
		self.used = []
		self.impdir = None
		self.tmp = 0

	def get_import(self):
		"""Get and create the import directory."""
		if self.impdir == None:
			self.impdir = os.path.join(self.outdir, "%s-imports" % self.id)
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
		return os.path.relpath(path, self.outdir)

	def create_resource(self, ext, id = None):
		impdir = self.get_import()
		if id != None:
			name = "@file-%d.%s" % (self.tmp, ext)
			self.tmp += 1
		else:
			name = "%s.%s" % (id, ext)
		path = os.path.join(impdir, name)
		return path

	def add_resource(self, path):
		apath = os.path.abspath(path)
		if apath.startswith(self.outdir):
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
