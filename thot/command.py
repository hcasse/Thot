#!/usr/bin/python3
# -*- coding: utf-8 -*-

# thot -- Thot command
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

"""Main command for Thot."""

import argparse
import os
import os.path
import sys

from thot import common
from thot import doc
from thot import tparser


def list_avail_modules(document):
	"""List available modules."""
	print("Available modules:")
	paths = document.getVar("THOT_USE_PATH")
	names = set({os.path.splitext(file)[0]
		for path in paths.split(":") for file in os.listdir(path)
			if os.path.splitext(file)[1] in { ".py" } and not file.startswith("__")})
	for name in names:
		mod = common.loadModule(name, paths)
		desc = ""
		if "__short__" in mod.__dict__:
			desc = f" ({mod.__short__})"
		print(f"- {name}{desc}")

	print("\nAvailable back-ends:")
	path = os.path.join(document.env["THOT_LIB"], "backs")
	names = set({os.path.splitext(file)[0]
		for file in os.listdir(path)
			if os.path.splitext(file)[1] in { ".py" }
			and not file.startswith("__")})
	for name in names:
		mod = common.loadModule(name, path)
		desc = ""
		if "__short__" in mod.__dict__:
			desc = f" ({mod.__short__})"
		print(f"- {name}{desc}")


def list_module(document, name, mon = common.DEFAULT_MONITOR):
	""""List the content of a particular module."""
	paths = document.getVar("THOT_USE_PATH") + ":" + os.path.join(document.env["THOT_LIB"], "backs")
	mod = common.loadModule(name, paths)
	if not mod:
		mon.fatal(f"no module named {name}")
	short = ""
	if "__short__" in mod.__dict__:
		short = f" ({mod.__short__})"
	print(f"Module: {name}{short}")
	if "__description__" in mod.__dict__:
		print(f"\n{mod.__description__}")
	syn = []
	if "__words__" in mod.__dict__:
		for (_, word, desc) in mod.__words__:
			syn.append((common.prepare_syntax(word), desc))
	if "__lines__" in mod.__dict__:
		for (_, line, desc) in mod.__lines__:
			syn.append((common.prepare_syntax(line), desc))
	if "__syntaxes__" in mod.__dict__:
		for m in mod.__syntaxes__:
			syn = syn + m.get_doc()
	if syn != []:
		print("Syntax:")
		common.display_syntax(syn)
	has_output = False
	for out in ["html", "latex", "docbook"]:
		name = f"__{out}__"
		if name in mod.__dict__:
			if not has_output:
				has_output = True
				print("\nOutput:")
			print(f"\t{out}:")
			for (form, desc) in mod.__dict__[name]:
				print(f"\t{form}\n\t\t{desc}" % (form, desc))


def list_syntax(man):
	"""List the syntax used in the current document."""
	syn = []
	for mod in man.used_mods + [tparser]:
		#print("- %s" % ("thot" if mod == tparser else mod.__name__))
		if "__words__" in mod.__dict__:
			syn = syn + [(common.prepare_syntax(w), d) for (_, w, d) in mod.__words__]
		if "__lines__" in mod.__dict__:
			syn = syn + [(common.prepare_syntax(l), d) for (_, l, d) in mod.__words__]
		if "__syntaxes__" in mod.__dict__:
			for s in mod.__syntaxes__:
				syn = syn + s.get_doc()
	if syn != []:
		common.display_syntax(syn)


def list_output(man, output):
	"""List possible outputs."""
	print("Available outputs:")
	for mod in man.used_mods:
		print(f"- {mod.__name__}")
		name = f"__{output}__"
		if name in mod.__dict__:
			for (form, desc) in mod.__dict__[name]:
				print(f"\t{form}\n\t\t{desc}")


def list_used_modules(man):
	"""Print used modules."""
	print("Used modules:")
	for mod in man.used_mods:
		desc = ""
		if "__short__" in mod.__dict__:
			desc = f" ({mod.__short__})"
		print(f"- {mod.__name__}{desc}")


def main():
	"""Command line entry point."""
	env = common.Env()
	mon = common.Monitor()

	# Prepare arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--type", action="store", dest="out_type",
		default="html", help="output type (xml, html, latex, ...)")
	parser.add_argument("-o", "--out", action="store", dest="out_path",
		help="output path")
	parser.add_argument("-D", "--define", action="append", dest="defines",
		help="add the given definition to the document environment.")
	parser.add_argument("--dump", dest = "dump", action="store_true", default=False,
		help="only for debugging purpose, dump the database of Thot")
	parser.add_argument("-u", "--use", action="append", dest="uses",
		help="given module is loaded before the generation.")
	parser.add_argument("--verbose", "-v", dest = "verbose", action="store_true", default=False,
		help="display verbose messages about the processing")
	parser.add_argument("--encoding", "-e", dest="encoding", action="store",
		help="select the encoding of the input files (default UTF-8)")
	parser.add_argument("--list-mods", dest = "list_mods", action="store_true", default=False,
		help="list used modules")
	parser.add_argument("--list-syntax", dest = "list_syntax", action="store_true", default=False,
		help="list available syntax in the document")
	parser.add_argument("--list-output", action="store", dest="list_output",
		help="list all generation output for the current modules")
	parser.add_argument("--list-mod", action="store", dest="list_mod",
		help="list the content of a module")
	parser.add_argument("--list-avail", dest = "list_avail", action="store_true", default=False,
		help="list available modules")
	parser.add_argument("--version", action="store_true", default=False,
		help="print version")
	parser.add_argument("file", nargs="?", help="File to convert.")

	# Parse arguments
	args = parser.parse_args()
	# TO REMOVE when monitors will be used throughout the application
	common.IS_VERBOSE = args.verbose
	mon.set_verbosity(args.verbose)
	if args.version:
		common.print_version()
		sys.exit()
	if args.encoding:
		common.ENCODING = args.encoding
	env["THOT_OUT_TYPE"] = args.out_type
	if not args.out_path:
		env["THOT_OUT_PATH"] = ""
	else:
		env["THOT_OUT_PATH"] = args.out_path
	file = args.file
	if file is None:
		input = sys.__stdin__
		env["THOT_FILE"] = "<stdin>"
		env["THOT_DOC_DIR"] = "."
	else:
		try:
			input = open(file, encoding=common.ENCODING)
		except FileNotFoundError:
			mon.fatal(f"cannot open file '{file}'")
		env["THOT_FILE"] = file
		env["THOT_DOC_DIR"] = os.path.dirname(file)
		if not env["THOT_DOC_DIR"]:
			env["THOT_DOC_DIR"] = "."
	if args.defines:
		for d in args.defines:
			p = d.find('=')
			if p == -1:
				mon.fatal('-D' + d + ' must follow syntax -Didentifier=value')
			else:
				env[d[:p]] = d[p+1:]

	# open the output
	document = doc.Document(env)
	out_name = env["THOT_OUT_TYPE"]
	out_path = os.path.join(document.env["THOT_LIB"], "backs")
	out_driver = common.loadModule(out_name,  out_path)
	if not out_driver:
		mon.fatal(f'cannot find {out_name} back-end')

	# list available modules
	if args.list_avail:
		list_avail_modules(document)
		sys.exit(0)

	# list a module
	elif args.list_mod:
		list_module(document, args.list_mod)
		sys.exit(0)

	# Parse the file
	man = tparser.Manager(document, mon=mon)
	if "init" in out_driver.__dict__:
		out_driver.init(man)
	if args.uses:
		for u in args.uses:
			man.use(u)
	man.parse(input, env['THOT_FILE'])

	# dump the parsed document
	if args.dump:
		document.dump()

	# list the syntax
	elif args.list_syntax:
		print("Available syntax:")
		list_syntax(man)

	# list outputs
	elif args.list_output:
		list_output(man, args.list_output)

	# list the involved modules
	elif args.list_mods:
		list_used_modules(man)

	# Output the result
	else:
		try:
			try:
				out_driver.output(document)
			except AttributeError:
				out_driver.output_ext(document, mon)
		except common.BackException as e:
			mon.fatal(str(e))

if __name__ == "__main__":
	main()
