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

import datetime
import glob
import locale
import optparse
import os
import os.path
import re
import sys

import thot
import thot.common as common
import thot.doc as doc
import thot.tparser as tparser


def list_avail_modules(document):
	"""List available modules."""
	print("Available modules:")
	paths = document.getVar("THOT_USE_PATH")
	names = set([os.path.splitext(file)[0]
		for path in paths.split(":") for file in os.listdir(path)
			if os.path.splitext(file)[1] in { ".py" } and not file.startswith("__")])
	for name in names:
		mod = common.loadModule(name, paths)
		desc = ""
		if "__short__" in mod.__dict__:
			desc = " (%s)" % mod.__short__
		print("- %s%s" % (name, desc))

	print("\nAvailable back-ends:")
	path = os.path.join(document.env["THOT_LIB"], "backs")
	names = set([os.path.splitext(file)[0]
		for file in os.listdir(path)
			if os.path.splitext(file)[1] in { ".py" }
			and not file.startswith("__")])
	for name in names:
		mod = common.loadModule(name, path)
		desc = ""
		if "__short__" in mod.__dict__:
			desc = " (%s)" % mod.__short__
		print("- %s%s" % (name, desc))


def list_module(document, name):
	""""List the content of a particular module."""
	paths = document.getVar("THOT_USE_PATH") + ":" + os.path.join(document.env["THOT_LIB"], "backs")
	mod = common.loadModule(name, paths)
	if not mod:
		common.fatal("no module named %s" % options.list_mod)
	short = ""
	if "__short__" in mod.__dict__:
		short = " (%s)" % mod.__short__
	print("Module: %s%s" % (name, short))
	if "__description__" in mod.__dict__:
		print("\n%s" % mod.__description__)
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
		name = "__%s__" % out
		if name in mod.__dict__:
			if not has_output:
				has_output = True
				print("\nOutput:")
			print("\t%s:" % out)
			for (form, desc) in mod.__dict__[name]:
				print("\t%s\n\t\t%s" % (form, desc))


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
		print("- %s" % mod.__name__)
		name = "__%s__" % output
		if name in mod.__dict__:
			for (form, desc) in mod.__dict__[name]:
				print("\t%s\n\t\t%s" % (form, desc))


def list_used_modules(man):
	"""Print used modules."""
	print("Used modules:")
	for mod in man.used_mods:
		desc = ""
		if "__short__" in mod.__dict__:
			desc = " (%s)" % mod.__short__
		print("- %s%s" % (mod.__name__, desc))


def main():
	"""Command line entry point."""
	env = common.Env()
	mon = common.Monitor()

	# Prepare arguments
	oparser = optparse.OptionParser()
	oparser.add_option("-t", "--type", action="store", dest="out_type",
		default="html", help="output type (xml, html, latex, ...)")
	oparser.add_option("-o", "--out", action="store", dest="out_path",
		help="output path")
	oparser.add_option("-D", "--define", action="append", dest="defines",
		help="add the given definition to the document environment.")
	oparser.add_option("--dump", dest = "dump", action="store_true", default=False,
		help="only for debugging purpose, dump the database of Thot")
	oparser.add_option("-u", "--use", action="append", dest="uses",
		help="given module is loaded before the generation.")
	oparser.add_option("--verbose", "-v", dest = "verbose", action="store_true", default=False,
		help="display verbose messages about the processing")
	oparser.add_option("--encoding", "-e", dest="encoding", action="store",
		type="string", help="select the encoding of the input files (default UTF-8)")
	oparser.add_option("--list-mods", dest = "list_mods", action="store_true", default=False,
		help="list used modules")
	oparser.add_option("--list-syntax", dest = "list_syntax", action="store_true", default=False,
		help="list available syntax in the document")
	oparser.add_option("--list-output", action="store", dest="list_output",
		help="list all generation output for the current modules")
	oparser.add_option("--list-mod", action="store", dest="list_mod",
		help="list the content of a module")
	oparser.add_option("--list-avail", dest = "list_avail", action="store_true", default=False,
		help="list available modules")

	# Parse arguments
	(options, args) = oparser.parse_args()
	common.IS_VERBOSE = options.verbose		# TO REMOVE when monitors will be used throughout the application
	mon.set_verbosity(options.verbose)
	if options.encoding:
		common.ENCODING = options.encoding
	env["THOT_OUT_TYPE"] = options.out_type
	if not options.out_path:
		env["THOT_OUT_PATH"] = ""
	else:
		env["THOT_OUT_PATH"] = options.out_path
	if args == []:
		input = sys.__stdin__
		env["THOT_FILE"] = "<stdin>"
		env["THOT_DOC_DIR"] = "."
	else:
		try:
			input = open(args[0])
		except FileNotFoundError:
			mon.fatal("cannot open file '%s'" % args[0]) 
		env["THOT_FILE"] = args[0]
		env["THOT_DOC_DIR"] = os.path.dirname(args[0])
		if not env["THOT_DOC_DIR"]:
			env["THOT_DOC_DIR"] = "."
	if options.defines:
		for d in options.defines:
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
		mon.fatal('cannot find %s back-end' % out_name)

	# list available modules
	if options.list_avail:
		list_avail_modules(document)
		sys.exit(0)

	# list a module
	elif options.list_mod:
		list_module(document, options.list_mod)
		sys.exit(0)

	# Parse the file
	man = tparser.Manager(document, mon=mon)
	if "init" in out_driver.__dict__:
		out_driver.init(man)
	if options.uses:
		for u in options.uses:
			man.use(u)
	man.parse(input, env['THOT_FILE'])

	# dump the parsed document
	if options.dump:
		document.dump("")

	# list the syntax
	elif options.list_syntax:
		print("Available syntax:")
		list_syntax(man)

	# list outputs
	elif options.list_output:
		list_output(man, options.list_output)

	# list the involved modules
	elif options.list_mods:
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
