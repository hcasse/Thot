#
# block -- THOT module.
# Copyright (C) 2023  <hugues.casse@laposte.net>
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
#

"""commodity module to insert blocks of document in a different syntax.

This block are enclosed between tags <ID OPTIONS>...</ID> and supports
a comma-separated list of options.
"""

import re

from thot import common, doc, tparser
from thot.common import ParseException

ARG_RE = re.compile(r"[\s]*([\S]+)[\s]*=(.*)")

class OptionException(Exception):
	option = None
	msg = None
	value = None

	def __init__(self, option, msg, value):
		self.option = option
		self.msg = msg
		self.value = value

	def __str__(self):
		return f"{self.msg} for option \"{self.option.name}\" in \"{self.value}\""


class Option:
	"""An option for the block. The option are stored in a dictionary in a
	dictionary inside the block. If the option decoding fails, an OptionException
	has to be raised."""
	name = None
	default = None
	opt = None

	def __init__(self, name, default = None):
		self.name = name
		self.default = default

	def parse(self, value):
		"""Called when the option is found in text to build it
		and check it. If there is an error, an OptionException must be thrown."""
		return value


class SwitchOption(Option):
	"""Option accepting on/off, true/false, yes, no, etc or no argument"""

	def __init__(self, name, default = False):
		Option.__init__(self, name, default)

	def parse(self, value):
		value = value.lower()
		if value in ["yes", "on", "true"]:
			return True
		elif value in ["no", "off", "false"]:
			return False
		else:
			raise OptionException(self, "accepted values includes yes/no, on/off, true/false.", value)


class IntOption(Option):
	"""Option returning an integer."""

	def __init__(self, name, default = 10):
		Option.__init__(self, name, default)

	def parse(self, value):
		try:
			return int(value)
		except ValueError:
			raise OptionException(self, "bad integer value", value)


class Block(doc.Block):
	"""Abstract class for block providing custom syntax."""

	def __init__(self, syntax, man):
		"""Build an external block. syntax is a block.Syntax instance."""
		doc.Block.__init__(self, syntax.name)
		self.syntax = syntax
		self.options = man.get_info(syntax.name)
		if self.options is None:
			self.options = {}
		else:
			self.options = dict(self.options)
		self.man = man

	def new_num(self):
		"""Return a unique number."""
		return self.syntax.new_num()

	def get_options(self):
		"""Get the option dictionary."""
		return self.options

	def get_option(self, option):
		"""Get an option value."""
		try:
			return self.options[option]
		except KeyError:
			try:
				option = self.syntax.options[option]
				return option.default
			except KeyError:
				raise common.ThotException(f"no option {option}")

	def gen(self, gen):
		"""Must be implemenetd to generate the content.
		Default implementation does nothing."""
		pass

	def numbering(self):
		return "figure"

	def parse_free(self, arg):
		"""Called to parse a free argument (not formatetd as id=value).
		As a default, return an error."""
		raise ParseException(f"unsupported free argument: \"{arg}\"")

	def parse_args(self, argl):
		"""Called to parse argument of the block."""
		args = argl.split(",")
		for arg in args:
			match = ARG_RE.match(arg)

			# free argument
			if not match:
				arg = arg.strip()
				if arg:
					try:
						option = self.syntax.options[arg]
						if isinstance(option, SwitchOption):
							self.options[option.name] = option.parse("yes")
						else:
							raise ParseException(f"argument missing for \"{arg}\"")
					except KeyError:
						self.parse_free(arg)

			# option
			else:
				try:
					option = self.syntax.options[match.group(1)]
					self.options[option.name] = option.parse(match.group(2))
				except KeyError:
					raise ParseException(f"unknown option \"{arg}\"")

	def check_args(self, man):
		"""Called to parse arguments. Manager parameter allows to display error messages."""
		pass


class Syntax(tparser.Syntax):
	"""Provides syntax to build blocks with different syntax."""

	def __init__(self,
		name,
		options=None,
		maker = Block,
		doc = "",
		set = False):
		"""Build a custom syntax block of the form:
			<name OPTIONS> content </name>

		* name: name of the block,
		* options: options supported by the block,
		* maker: block class or callable maker for the block,
		* doc: block documentation.
		* set: generate a command <name-set OPTIONS> to record default option values.
		"""
		if options is None:
			options = []

		# initialize attributes
		self.name = name
		self.options = { }
		for option in options:
			self.options[option.name] = option
		self.maker = maker
		self.doc = doc

		# prepare internals
		self.close = re.compile(f"^</{name}>")
		self.re = f"^<{name}([\\s]+([^>]*))?>"
		if set:
			self.set_re = f"^<{name}-set[\\s]*([^>]*)>"
		else:
			self.set_re = None
		self.count = 0

	def get_doc(self):
		return [(
			f"<{self.name} [options]>...</{self.name}>",
			f"{self.doc}\nOptions includes: {', '.join(self.options)}"
		)]

	def get_lines(self):
		lines = []
		if self.set_re:
			lines.append((self.handle_set, self.set_re))
		lines.append((self.handle, self.re))
		return lines

	def handle_set(self, man, match):
		block = self.make(man)
		options = man.get_info(self.name, None)
		if options is None:
			options = block.options
			man.set_info(self.name, options)
		else:
			block.options = options
		try:
			block.parse_args(match.group(1))
		except ParseException as exn:
			man.error(str(exn))

	def handle(self, man, match):
		block = self.make(man)
		try:
			args = match.group(2)
			if args is not None:
				block.parse_args(args)
		except ParseException as exn:
			man.error(str(exn))
		block.check_args(man)
		try:
			tparser.BlockParser(man, block, self.close)
		except ParseException as exn:
			man.error(str(exn))

	def make(self, man):
		"""Build a block for the module."""
		return self.maker(self, man)

	def new_num(self):
		"""Return a new unique number."""
		r = self.count
		self.count = self.count + 1
		return r
