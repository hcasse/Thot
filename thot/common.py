# doc -- Thot document escription module
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

import datetime
import html
import imp
import locale
import os
import os.path
import re
import shutil
import subprocess
import sys
import traceback

from html import escape

class ThotException(Exception):
	"""Exception of the Thot system.
	Any back-passed to the Thot system must inherit this exception.
	Other exceptions will not be caught."""
	
	def __init__(self, msg):
		self.msg = msg
	
	def __str__(self):
		return self.msg
	
	def __repr__(self):
		return self.msg


class ParseException(ThotException):
	"""This exception may be thrown by any parser encountering an error.
	File and line information will be added by the parser."""
	
	def __init__(self, msg):
		ThotException.__init__(self, msg)


class BackException(ThotException):
	"""Exception thrown by a back-end."""
	
	def __init__(self, msg):
		ThotException.__init__(self, msg)


class CommandException(ThotException):
	"""Thrown if there is an error during a command call."""
	
	def __init__(self, msg):
		ThotException.__init__(self, msg)


IS_VERBOSE = False
ENCODING = "UTF-8"


def onVerbose(f):
	"""Invoke and display the result of the given function if verbose
	mode is activated."""
	if IS_VERBOSE:
		sys.stderr.write(f(()))
		sys.stderr.write("\n")


def show_stack():
	"""Show the stack (for debugging purpose)."""
	traceback.print_exc()
	return ""


def onParseError(msg):
	raise ParseException(msg)

def onError(text):
	"""Display the given error and stop the application."""
	onVerbose(lambda _: show_stack())
	sys.stderr.write("ERROR: %s\n" % text)
	sys.exit(1)


def onWarning(message):
	"""Display a warning message."""
	sys.stderr.write("WARNING: %s\n" % message)


def onInfo(message):
	"""Display an information message."""
	sys.stderr.write("INFO: %s\n" % message)


DEPRECATED = []
def onDeprecated(msg):
	"""Display a deprecated message with the given message."""
	if msg not in DEPRECATED:
		sys.stderr.write("DEPRECATED: %s\n" % msg)
		DEPRECATED.append(msg)


def loadModule(name, paths):
	"""Load a module by its name and a collection of paths to look in
	and return its object."""
	try:
		for path in paths.split(":"):
			path = os.path.join(path, name + ".py")
			if os.path.exists(path):
				return imp.load_source(name, path)
			else:
				path = path + "c"
				if os.path.exists(path):
					return imp.load_compiled(name, path)
		return None
	except Exception as e:
		tb = sys.exc_info()[2]
		traceback.print_tb(tb)
		onError("cannot open module '%s': %s" % (path, str(e)))

AUTHOR_RE = re.compile('(.*)\<([^>]*)\>\s*')
def scanAuthors(text):
	"""Scan the author text to get structured representation of authors.
	text -- text containing author declaration separated by ','
	and with format "NAME <EMAIL>"
	Return a list of authors where each author dictionary
	containing 'name' and 'email' keys."""

	authors = []
	words = text.split(',')
	for word in words:
		author = {}
		match = AUTHOR_RE.match(word)
		if not match:
			author['name'] = word
		else:
			author['name'] = match.group(1)
			author['email'] = match.group(2)
		authors.append(author)
	return authors


def is_exe(fpath):
	"""Test if a path is executable."""
	return os.path.exists(fpath) and os.access(fpath, os.X_OK)


def which(program):
	"""Function to test if an executable is available.
	program: program to look for
	return: the found path of None."""
	
	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file
	return None


def getLinuxDistrib():
	"""Look for the current linux distribution.
	Return (distribution, release) or None if version cannot be found."""
	try:
		id = ""
		release = 0
		for line in open("/etc/lsb-release"):
			if line.startswith("DISTRIB_ID="):
				id = line[11:-1]
			elif line.startswith("DISTRIB_RELEASE="):
				release = line[16:-1]
		return (id, release)
	except IOError as e:
		return ("", 0)


def onRaise(msg):
	"""Raise a command error with the given message."""
	raise CommandError(msg)

def onIgnore(msg):
	"""Ignore the error."""
	pass

ERROR_FAIL = onError
ERROR_RAISE = onRaise
ERROR_WARN = onWarning
ERROR_IGNORE = onIgnore


class CommandRequirement:
	"""Implements facilities for test for the existence of a command."""
	checked = False
	path = None
	cmd = None
	msg = None
	error = False
	
	def __init__(self, cmd, msg = None, error = ERROR_WARN):
		self.cmd = cmd
		self.msg = msg
		self.error = error
	
	def get(self):
		if not self.checked:
			self.checked = True
			self.path = which(self.cmd)
			if not self.path:
				self.error(self.msg)
		return self.path 


class Command(CommandRequirement):
	"""Handle the operation of an external command."""
	
	def __init__(self, cmd, msg = None, error = False):
		CommandRequirement.__init__(self, cmd, msg, error)
	
	def call(self, args = [], input = None, quiet = False):
		"""Call the command. Throw CommandException if there is an error.
		args -- list of arguments.
		input -- input to pass to the called command.
		quiet -- do not produce any output."""
		cmd = self.get()
		if not cmd:
			return
		out = None
		if quiet:
			out = open(os.devnull, "w")
		cmd = " ".join([ cmd ] + args)
		try:
			code = subprocess.check_call( cmd, close_fds = True, shell = True, stdout = out, stderr = out, stdin = input )
		except (OSError, subprocess.CalledProcessError) as e:
			self.error("command %s failed: %s" % (self.cmd, e))

	def scan(self, args = [], input = None, err = False):
		"""Launch a command and return the output if successful, a CommandException is raise else.
		input -- optional input stream.
		err -- if True, redirect also the standard error."""
		cmd = self.get()
		if not cmd:
			return
		errs = None
		if err:
			errs = subprocess.PIPE
		cmd = " ".join([ cmd ] + args)
		try:
			out = subprocess.check_output( cmd, close_fds = True, shell = True, stdout = subprocess.PIPE, stderr = errs, stdin = input )
			return out
		except (OSError, subprocess.CalledProcessError) as e:
			self.error("command %s failed: %s" % (self.cmd, e))


ESCAPES = [ '(', ')', '+', '.', '*', '/', '?', '^', '$', '\\', '|' ]
def escape_re(str):
	res = ""
	for c in str:
		if c in ESCAPES:
			res = res + "\\" + c
		else:
			res = res + c
	return res

class Options:
	"""Contains a collection of options and behaves as a dictionary,
	except that, if some symbol is not defined, returns an empty string.
	It may also defined with accepted identifier s and default values.
	Any value that is not in the original definition list is warned."""
	
	def __init__(self, man, defs):
		self.man = man
		self.map = { }
		for (id, val) in defs:
			self.map[id] = val

	def parse(self, options):
		"""Parse the given set of options."""
		if options:
			for opt in options.split(","):
				p = opt.find("=")
				if p < 0:
					self.man.warn("bad option: '%s" % opt)
					continue
				id = opt[:p]
				val = opt[p+1:]
				if id not in self.map:
					self.man.warn("unknown option '%s'" % opt)
				else:
					self.map[id] = val

	def __getitem__(self, key):
		return self.map[key]

def parse_options(man, text, defs):
	"""Parse the given text for options given un defs and return
	an Options object containing the result."""
	opts = Options(man, defs)
	opts.parse(text)
	return opts
	

STANDARD_VARS = [
	("AUTHORS",			"authors of the document (',' separated, name <email>)"),
	("LANG",			"lang of the document"),
	("LOGO",			"logos of the supporting organization"),
	("ORGANIZATION",	"organization producing the document"),
	("SUBTITLE",		"sub-title of the document"),
	("THOT_FILE",		"used to derivate the THOT_OUT_PATH if not set"),
	("THOT_OUT_PATH",	"output directory path"),
	("TITLE",			"title of the document"),
]

def make_var_doc(custom):
	"""Generate documentation text for variables (for __description__
	building). The documented variables includes standard variables
	and custom variables."""
	vars = STANDARD_VARS + custom
	vars.sort()
	imax = max([len(i) for (i, _) in vars])
	d = ""
	for (i, id) in vars:
		d += "%s:%s %s\n" % (i, " " * (imax - len(i)), id)
	return d


arg_re = re.compile("\(\?P<([a-zA-Z0-9]+)(_[a-zA-Z0-9_]*)?>(%s|%s)*\)" %
	("[^)[]", "\[[^\]]*\]"))
REPS = [
	(" ", 		u"␣"	),
	("\t", 		u"⭾"	),	
	("\\s+",	" "		),
	("\\s*", 	" "		),
	("\\s", 	" "		),
	("\(", 		"("		),
	("\)", 		")"		),
	("^", 		""		),
	("$", 		""		)
]
def prepare_syntax(t):
	"""Prepare a regular expression to be displayed to human user."""
	if t == "^$" or t == "^\s+$":
		return "\\n"
	t = arg_re.sub('/\\1/', t)
	for (p, r) in REPS:
		t = t.replace(p, r)
	return t.strip()


def supports_ansi():
	plat = sys.platform
	supported_platform = plat != 'Pocket PC' and \
		(plat != 'win32' or 'ANSICON' in os.environ)
	is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
	return supported_platform and is_a_tty

IS_ANSI = supports_ansi()
NORMAL = "\033[0m"
SLASH_COLOR = "\033[4m"
VAR_COLOR = "\033[3m"

slash_re = re.compile("\\\\(.)")
slash_rep = SLASH_COLOR + "\\1" + NORMAL
var_re = re.compile("\\/([a-zA-Z][a-zA-Z0-9]*)\\/")
var_rep = VAR_COLOR + "\\1" + NORMAL
def decorate_syntax(t):
	"""Colorize, if available, escaped special characters."""
	l = len(t)
	if not IS_ANSI:
		return (l, t)
	else:
		(t, cs) = slash_re.subn(slash_rep, t)
		(t, cv) = var_re.subn(var_rep, t)
		return (l - cs - 2 * cv, t)

def display_syntax(syn):
	"""Display list of syntax items. syn is a sequence of pairs (s, d)
	where s is the syntax and d is the documentation. The documentation
	may be split in several lines."""
	
	# find row size
	(w, _) = os.get_terminal_size()
	
	# prepare the strings
	syn = [(decorate_syntax(s), d) for (s, d) in syn]
	
	# display the strings
	m = min(16, 1 + max([l for ((l, _), _) in syn]))
	for ((l, r), d) in syn:
		ls = d.split("\n")
		if l > m:
			print("%s:" % r)
		else:
			print("%s:%s%s" % (r, " " * (m - l), ls[0][0:min(w, len(ls[0]))]))
			if len(ls[0]) > w:
				ls[0] = ls[0][w:]
			else:
				ls = ls[1:]
		for l in ls:
			while len(l) > w:
				print("%s %s" % (" " * m, l[:w]))
				l = l[w:]
			print("%s %s" % (" " * m, l))


class Env:
	"""Represents an environment, that is, a collection of defnitions
	name/value. It provides several facilties to handle definitions
	and [...] operator access."""

	VAR_RE = r"@\((?P<varid>[a-zA-Z_0-9]+)\)"
	VAR_REC = re.compile(VAR_RE)

	def __init__(self, map = None):
		if map != None:
			self.map = map
		else:
			self.map = os.environ.copy()
			thot_dir = os.path.abspath(os.path.dirname(__file__))
			self.map["THOT_VERSION"] = "2.0"
			self.map["ENCODING"] = locale.getpreferredencoding()
			self.map["THOT_LIB"] = thot_dir
			self.map["THOT_BASE"] = os.path.join(thot_dir, "data", "")
			self.map["THOT_USE_PATH"] = os.path.join(thot_dir, "mods", "")
			self.map["THOT_DATE"] = str(datetime.datetime.today())

	def set(self, name, val):
		"""Set a new definition or overwrite an existing one."""
		self.map[name] = val

	def get(self, name, default = ""):
		"""Get the value in an environment. If the value does not
		exist, return an empty string (or the default value)."""
		try:
			return self.map[name]
		except KeyError:
			return default

	def __getitem__(self, key):
		return self.get(key)

	def __setitem__(self, key, val):
		self.set(key, val)

	def reduce(self, text):
		"""Reduce variables in the given text.
		- doc -- current document
		- text -- text to replace in."""
		m = Env.VAR_REC.search(text)
		while m:
			val = str(self.get(m.group('varid')))
			text = text[:m.start()] + val + text[m.end():]
			m = Env.VAR_REC.search(text)
		return text

	def __iter__(self):
		return iter(self.map)

	def copy(self):
		"""Get a new environment copy of this one."""
		return Env(dict(self.map))


class Monitor:
	"""Interface of classes in charge of communicating with human user."""

	ANSI = supports_ansi()
	NORMAL = "\033[0m" if ANSI else ""
	ERROR_STYLE = "\033[31m" if ANSI else ""
	WARN_STYLE = "\033[32m" if ANSI else ""
	INFO_STYLE = "\033[36m" if ANSI else ""
	VERB_STYLE = "\033[3;37m" if ANSI else ""
	ERROR_FMT = ERROR_STYLE + "ERROR: " + NORMAL + "%s\n"
	WARN_FMT = WARN_STYLE + "WARNING: " + NORMAL + "%s\n"
	INFO_FMT = INFO_STYLE + "INFO: " + NORMAL + "%s\n"
	VERB_FMT = VERB_STYLE + "> %s" + NORMAL + "\n"

	def __init__(self):
		self.out = sys.stdout
		self.err = sys.stderr
		self.verbose = False

	def set_verbosity(self, verbose):
		"""Enable/disable verbose mode."""
		self.verbose = verbose

	def error(self, msg, *args):
		"""Print an error."""
		self.err.write(Monitor.ERROR_FMT % (msg % args))

	def warn(self, msg, *args):
		"""Print a warning."""
		self.err.write(Monitor.WARN_FMT % (msg % args))

	def info(self, msg, *args):
		"""Print an information."""
		self.err.write(Monitor.INFO_FMT % (msg % args))

	def say(self, msg, *args):
		"""Print a verbose message."""
		if self.verbose:
			self.err.write(Monitor.VERB_FMT % (msg % args))
