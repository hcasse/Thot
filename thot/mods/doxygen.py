# doxygen -- Thot Doxygen module
# Copyright (C) 2018  <hugues.casse@laposte.net>
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

"""Module providing linking with Doxygen documentation."""

import os.path
import xml.etree.ElementTree as ET

from thot import common, doc


def read_tags(name, map, sep, ref):
	"""Read the tags contained in the named file and fill the map.
	If the file cannont be opened or is badly formatted, display a
	warning and return."""

	try:

		# open the file
		tree = ET.parse(name)
		root = tree.getroot()
		if root.tag != "tagfile":
			common.onWarning(f"{name} does not contains doxygen tags")

		# read the compound
		for comp in root.iter("compound"):

			# read compound information
			name = comp.find("name")
			filename = comp.find("filename")
			if name is None or filename is None:
				continue

			# create the compond
			map[name.text] = os.path.join(ref, filename.text)

			# read the members
			for member in comp.iter("member"):

				# read the information
				memname = member.find("name")
				anchorfile = member.find("anchorfile")
				anchor = member.find("anchor")
				if memname is None or anchorfile is None or anchor is None:
					continue

				# create the entry
				map[name.text + sep + memname.text] = os.path.join(ref,
					f"{anchorfile.text}#{anchor.text}")

	except IOError as e:
		common.onWarning(f"cannot read {name}: {e}")


class Source:
	"""Term source to retrieve the code sumbols."""

	def __init__(self, man):
		self.man = man
		self.prefixes = [""]
		self.map = { }
		self.ref = None

	def add_use(self, path, sep, ref):
		"""Add a code documentation entry."""
		if ref is None:
			self.ref = os.path.dirname(ref)
		read_tags(path, self.map, sep, ref)

	def resolve(self, word):
		"""Lookup for an unresolved word."""
		found = []
		for p in self.prefixes:
			try:
				found.append(self.map[p + word])
			except KeyError:
				pass
		if not found:
			return None
		if len(found) > 1:
			self.man.warn(f"'#{word}' is ambiguous!")
		link = doc.Link(found[0])
		link.append(doc.Word(word))
		return link

	def add_prefix(self, prefix):
		"""Add a lookup prefix."""
		self.prefixes.append(prefix)

	def remove_prefix(self, prefix):
		"""Remove a lookup prefix."""
		self.prefixes.remove(prefix)


def handle_use(man, match):
	options = common.parse_options(man, match.group("options"),
		[("sep", "."), ("ref", None)])
	man.doxygen.add_use(match.group("path"), options["sep"], options["ref"])

def handle_prefix(man, match):
	man.doxygen.add_prefix(match.group("prefix"))

def handle_remove(man, match):
	man.doxygen.remove_prefix(match.groupe("prefix"))


def init(man):
	man.doxygen = Source(man)
	man.doc.add_hash_source(man.doxygen)

__short__ = """Include Doxygen references in the documentation"""

__lines__ = [
	(handle_use,
		r"^@doxy-use(\((?P<options>[^)]*)\))?\s*(?P<path>.*)$",
		"""Specify a Doxygen tag file to provide referenced program items.
		Options includes sep to define a namespace / item separator
		and ref to specify path/URL of the Doxygen documentation"""),
	(handle_prefix,
		r"^@doxy-prefix\s+(?P<prefix>\S+)\s*$",
		"""Specify a prefix that will be prepended to hashed word to resolve
		them. Several prefixes may be specified."""),
	(handle_remove,
		r"^@doxy-remove\s+(?P<prefix>\S+)\s*$",
		"""Remove a prefix previously added with @doxy-prefix."""),
]

