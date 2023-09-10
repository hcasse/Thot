# thot.tparser -- Thot document parser
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

"""Module dedicated to javascript communication with a dynamic HTML page.

To use it, one has to declare the feature named FEATURE and to create and send messages using class Message."""

import json
import os.path

from thot import common, doc

class Feature(doc.Feature):

	def prepare(self, gen):
		script = gen.newScript()
		script.src = gen.use_resource(os.path.join(common.get_data(), "js/communicate.js"))

FEATURE = Feature()

class Message:
	"""Class to manage messages generated by the communicate module."""

	def __init__(self, size, input, debug = False):
		self.debug = debug
		data = input.read(size)
		self.message = json.loads(data)
		if debug:
			print("DEBUG: received", self.message)
		self.answer = []

	def get_message(self):
		"""Return the JSON dictionary of the message."""
		return self.message

	def get_attr(self, name):
		"""Get an attribute of the message (if it is a dictionary)."""
		return self.message[name]

	def call(self, fun, args = ""):
		"""Call a custom function the user."""
		self.answer.append({"type": "call", "fun": fun, "args": args})

	def set_style(self, id, attr, val):
		"""Set the style attribute of a node."""
		self.answer.append({"type": "set-style", "id": id, "attr": attr, "val": val})

	def add_class(self, id, cls):
		"""Add a class to a node."""
		self.answer.append({"type": "add-class", "id": id, "class": cls})

	def set_attr(self, id, attr, val):
		"""Set the attribute of a node."""
		self.answer.append({"type": "set-attr", "id": id, "attr": attr, "val": val})

	def set_value(self, id, val):
		"""Set the value of a node."""
		self.answer.append({"type": "set-value", "id": id, "val": val})

	def remove_class(self, id, cls):
		"""Remove a class from the identified node."""
		self.answer.append({"type": "remove-class", "id": id, "class": cls})

	def remove_attr(self, id, attr):
		"""Remove an attribute from the node."""
		self.answer.append({"type": "remove-attr", "id": id, "attr": attr})

	def set_content(self, id, content):
		"""Change the content of a node."""
		self.answer.append({"type": "set-content", "id": id, "content": content})

	def reply(self, out):
		if self.debug:
			print("DEBUG: replied", self.answer)
		res = json.dumps(self.answer)
		out.write(bytes(res, "utf8"))
		

