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

This block are enclosed between tags <ID OPTIONS>...</ID> and supports a comma-separated list of options.
"""

from thot import common, doc, tparser

class OptionException(Exception):
	option = None
	msg = None
	value = None
	
	def __init__(self, option, msg, value):
		self.option = option
		self.msg = msg
		self.value = value

	def __str__(self):
		return "%s for option \"%s\" in \"%s\"" % (self.msg, self.option.name, value)


class Option:
	"""An option for the block. The option are stored in a dictionary in a dictionary inside the block. If the option decoding fails, an OptionException has to be raised."""
	name = None
	default = None
	opt = None
	
	def __init__(self, name, opt, default = None):
		self.name = name
		self.opt = opt
		self.default = default
	
	def parse(self, value):
		"""Called when the option is found in text to build it
		and check it. If there is an error, an OptionException must be thrown."""
		return value


class SwitchOption(Option):
	"""Option accepting on/off, true/false, yes, no, etc or no argument"""
	
	def __init__(self, name, opt, default = False):
		Option.__init__(self, name, opt, default)
	
	def parse(self, value):
		value = value.lower()
		if value in ["yes", "on", "true"]:
			return True
		elif value in ["no", "off", "false"]:
			return False
		else:
			raise OptionException(self, "accepted values includes yes/no, on/off, true/false.")
		

class Block(doc.Block):
	"""Abstract class for block providing custom syntax."""
	
	def __init__(self, syntax):
		"""Build an external block. meta is an ExternalModule meta-descriptor."""
		doc.Block.__init__(self, syntax.name)
		self.syntax = syntax
		self.options = {}

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
				option = options[option]
				return option.default
			except KeyError:
				raise common.ThotException("no option %s" % option)
	
	def gen(self, gen):
		"""Must be implemenetd to generate the content.
		Default implementation does nothing."""

	def numbering(self):
		return "figure"
	
	def parse_free(self, arg):
		"""Called to parse a free argument (not formatetd as id=value).
		As a default, return an error."""
		raise Common.ParseException("unsupported free argument: \"%s\"" % arg)

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
						option = self.meta.options[arg]
						if isinstance(option, SwitchOption):
							option.parse("yes")
						else:
							raise common.parseException("argument missing for \"%s\"" % arg)
					except KeyError:
						self.parse_free(arg)

			# option
			else:
				try:
					option = self.meta.options[match.group(1)]
					self.options[option.name] = option.parse(match.group(2))
				except KeyError:
					raise common.parseException("unknown option \"%s\"" % arg)


class Syntax(tparser.Syntax):
	"""Provides syntax to build blocks with different syntax."""
	
	def __init__(self,
		name,*
		options=[], 
		maker = Block,
		doc = ""):
		"""Build a custom syntax block of the form:
			<name OPTIONS> content </name>
		
		* name: name of the block,
		* options: options supported by the block,
		* maker: block class or callable maker for the block,
		* doc: block documentation.
		"""

		# initialize attributes
		self.name = name
		self.options = { }
		for option in options:
			self.options[option.name] = option
		self.maker = maker
		self.doc = doc

		# prepare internals
		self.close = re.compile("^</%s>" % name)
		self.re = "^<%s[\s]*([^>]*)>" % name
		self.count = 0

	def get_doc(self):
		return [(
			"<%s [options]>...</%s>" % (self.name, self.name),
			"%s\nOptions includes: %s" % (self.doc, ", ".join(self.options))
		)]

	def get_lines(self):
		return [self.handle, self.re)]

	def handle(self, man, match):
		try:
			block = self.make()
			block.parse_args(match.group(1))
			tparser.BlockParser(man, block, self.close)
		except ExternalException as exn:
			man.error(exn)
	
	def make(self):
		"""Build a block for the module."""
		return self.maker(self)
	
	def new_num(self):
		"""Return a new unique number."""
		r = self.count
		self.count = self.count + 1
		return r
