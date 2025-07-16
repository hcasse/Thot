# doc -- commodity module for use of external fext format commands.
# Copyright (C) 2015  <hugues.casse@laposte.net>
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

"""Thot module proviuding generic classes to embed external content producer."""

import re
import subprocess
import sys
import tempfile

from thot import common
from thot import doc
from thot import tparser

ARG_RE = re.compile(r"[\s]*([\S]+)[\s]*=(.*)")

class ExternalException(Exception):

	def __init__(self, msg = None):
		self.msg = msg

	def __str__(self):
		return self.msg

class OptionException(ExternalException):
	option = None
	msg = None
	value = None

	def __init__(self, option, msg, value):
		ExternalException.__init__(self, msg)
		self.option = option
		self.value = value

	def __str__(self):
		return f"{self.msg} for option \"{self.option.name}\" in \"{self.value}\""


class Option:
	name = None
	default = None
	opt = None

	def __init__(self, name, opt, default=None):
		self.name = name
		self.opt = opt
		self.default = default

	def parse(self, value):
		"""Called when the option is found in text to build it
		and check it. If there is an error, an OptionException must be thrown."""
		return value

	def make(self, opts, input, value):
		"""Called when the option must be built.
		Return the option text."""
		if isinstance(value, bool):
			if value:
				opts.append(self.opt)
			else:
				pass
		else:
			opts.append(f"{self.opt} \"{value}\"")


class SwitchOption(Option):
	"""Option accepting on/off, true/false, yes, no, etc."""

	def __init__(self, name, opt, default=None):
		Option.__init__(self, name, opt, default)

	def parse(self, value):
		value = value.lower()
		if value in ["yes", "on", "true"]:
			return True
		elif value in ["no", "off", "false"]:
			return False
		else:
			raise OptionException(self,
				"accepted values includes yes/no, on/off, true/false.", value)

	def make(self, opts, input, value):
		if (self.default and value) or (not self.default and value != self.default):
			opts.append(self.opt)


class ExternalBlock(doc.Block):
	"""Abstract class for external block providing facilities to call
	an external command and get back result."""
	meta = None
	args = None
	path = None
	temps = None

	def __init__(self, meta):
		"""Build an external block. meta is an ExternalModule meta-descriptor."""
		doc.Block.__init__(self, meta.name)
		self.meta = meta
		self.args = []
		self.temps = []

	def is_ready(self):
		"""Test if the module is ready for generation."""
		return self.meta.command_found()

	def new_num(self):
		"""Return a unique number."""
		return self.meta.new_num()

	def get_path(self, gen):
		"""Declare the given block file as friend and generate a valid path."""
		if not self.path:
			self.path = gen.new_resource(f'extern/{self.meta.name}-{self.new_num()}{self.meta.ext}')
		return self.path

	def dumpHead(self, out, tab):
		out.write(f"{tab}block.{self.meta.name}(\n")

	def make_options(self, opts, input):
		"""Prepare the options: must return a string sequence."""
		done = []
		for (opt, val) in self.args:
			opt.make(opts, input, val)
			done.append(opt)
		for opt in self.meta.options.values():
			if opt not in done and opt.default:
				opt.make(opts, input, opt.default)

	def gen_output(self, gen):
		"""Called to generate the output document itself."""
		gen.genEmbeddedBegin(self)
		gen.genImage(self.get_path(gen), self, self.caption)
		gen.genEmbeddedEnd(self)

	def cleanup(self):
		for t in self.temps:
			t.file.close()

	def get_temporary(self):
		"""Open a temporary file and return an object whose name is the pah and
		file the file handle. The created file will be cleaned automatically."""
		tmp = tempfile.NamedTemporaryFile(suffix = ".txt")
		self.temps.append(tmp)
		return tmp

	def dump_temporary(self, text):
		"""Dump given text to temporary and return its path."""
		tmp = self.get_temporary()
		tmp.file.write(text.encode('utf-8'))
		tmp.file.flush()
		return tmp.name

	def prepare_input(self, gen, opts, input):
		"""Prepare the input of the external command, modifying either options
		or the input. Do nothing as a default."""
		pass

	def finalize_output(self, gen):
		"""Called once the command has been launched and if it is successful.
		Enable the execution of post-pass commands. As a default, do nothgin."""
		pass

	def run(self, cmd, opts, input):
		"""Run the command. Return True for success, False else."""
		try:
			cmd = f"{cmd} {' '.join(opts)}"
			common.onVerbose(lambda _: f"CMD: {cmd}")
			with subprocess.Popen(
				cmd,
				stdin = subprocess.PIPE,
				stdout = subprocess.PIPE,
				stderr = subprocess.PIPE,
				close_fds = True,
				shell = True
			) as process:
				(_, err) = process.communicate("".join(input).encode('utf-8'))
				if process.returncode == 127:
					return False
				if not self.meta.cmd:
					self.meta.cmd = cmd
				if process.returncode:
					sys.stderr.write(err.decode('utf-8'))
					self.onWarning(f"error during \"{cmd}\" call (return code = {process.returncode})")
					return False
				else:
					return True
		except OSError as e:
			self.onError(f'can not process {self.meta.name}: {e}')
			return False

	def run_command(self, opts, input):
		"""Run the command to generate the block."""
		if self.meta.cmd:
			return self.run(self.meta.cmd, opts, input)
		else:
			i = 0
			while i < len(self.meta.cmds):
				res = self.run(self.meta.cmds[i], opts, input)
				if res:
					break
				else:
					i = i + 1
			if self.meta.cmd:
				return res
			else:
				self.meta.cmd = ""
				self.onWarning(f"cannot generate {self.meta.name} block: " +
					f"none of commands {', '.join(self.meta.cmds)} is available.")
				return False

	def make_input(self, input):
		"""Prepare input. As a default, do nothing."""
		pass

	def gen(self, gen):
		if not self.is_ready():
			return
		opts = []
		input = []
		self.prepare_input(gen, opts, input)
		self.make_input(input)
		self.make_options(opts, input)
		if self.run_command(opts, input):
			self.finalize_output(gen)
			self.gen_output(gen)

	def numbering(self):
		return "figure"

	def parse_free(self, arg):
		"""Called to parse a free argument (not formatetd as id=value).
		As a default, return an error."""
		raise ExternalException(f"unsupported free argument: \"{arg}\"")

	def parse_args(self, argl):
		"""Called to parse argument of the block."""
		args = argl.split(",")
		for arg in args:
			match = ARG_RE.match(arg)
			if not match:
				arg = arg.strip()
				if arg:
					self.parse_free(arg.strip())
			else:
				key = match.group(1)
				if key in self.meta.options:
					option = self.meta.options[key]
					self.args.append((option, option.parse(match.group(2))))
				else:
					raise ExternalException(f"unknown option \"{key}\"")


class ExternalModule(tparser.Syntax):
	"""Descriptor of an external module. Supports different aspects of external modules:
		* option support,
		* command building, call and existence check."""
	name = None
	options = None
	cmds = None
	cmd = None		# None=not tested, ""=tested but not found, "..."=tested and found
	count = 0
	close = None
	ext = None
	maker = None
	doc = None

	def __init__(self, name, ext="", options=None, cmds=None,
		maker = ExternalBlock, doc = ""):
		"""Build an external module with the given name
		and given options.
		* man: Thot manager.
		* name: name of the module, used to generate file, identity the block and
		the tags in Thot.
		* out: used to generate the option to get back result (it must contain
		%s to be replaced by the actual path.
		* ext: output file extension."""

		if options is None:
			options = []
		if cmds is None:
			cmds = []

		# initialize attributes
		self.name = name
		self.ext = ext
		self.cmds = cmds
		self.maker = maker
		self.options = { }
		for option in options:
			self.options[option.name] = option
		self.doc = doc

		# prepare syntax
		self.close = re.compile(f"^</{name}>")
		self.re = f"^<{name}[\\s]*([^>]*)>"

	def get_doc(self):
		return [(
			f"<{self.name} [options]>...</{self.name}>",
			f"{self.doc}\nOptions includes: {', '.join(self.options)}"
		)]

	def get_lines(self):
		return [(self.handle, self.re)]

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

	def test_command(self):
		"""Look for a command for the block."""
		pass

	def command_found(self):
		"""Test if the command has been found."""
		return self.cmd != ""

	def new_num(self):
		"""Return a new unique number."""
		r = self.count
		self.count = self.count + 1
		return r
