# view -- thot-view implementation
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

"""Implements the command thot-view."""

import argparse
import http.server
import mimetypes
import os
import os.path
import shutil
import sys
import tempfile
import threading
import time
from urllib.parse import unquote
import webbrowser

#from thot import command
from thot import common
from thot import doc
from thot import tparser
from thot.backs import abstract_html as ahtml


# Heartbeat time-out in seconds.
HEARTBEAT_TIMEOUT = 1.5

PARSERS = {
	".md": "markdown",
	".thot": None,
	".doku": "dokuwiki",
	".textile": "textile"
}

TEXT_MIMES = {
	"application/javascript",
	"text/css",
	"text/csv",
	"text/html",
	"text/javascript",
	"text/plain",
	"text/xml"
}

class Resource:
	"""Base class of ressources used by the server. They are identified
	by a relative location used by the server to provide them."""

	def __init__(self, loc, manager = None):
		self.loc = loc
		self.manager = manager

	def get_mime(self):
		"""Called to get MIME type."""

	def prepare(self):
		"""Prepare the generation."""
		pass

	def generate(self, out):
		"""Called to generate on the given output."""
		pass

	def post(self, size, input):
		"""Called to receive a post. input is a stream to read input
		from. Return None for successn, or a pair (HTTP error code, message)."""
		return None

	def answer(self, output):
		"""Called to generate the answer to the post. output is a stream to output answer to."""
		pass

	def get_location(self):
		"""Get the location of the resource."""
		return self.loc

	def get_manager(self):
		"""Get the manager of the resource."""
		return self.manager

	def __str__(self):
		return ""


class HeartBeatResource(Resource):

	def __init__(self, loc, fun = lambda: None):
		Resource.__init__(self, loc)
		self.fun = fun

	def get_mime(self):
		return "text/plain"

	def generate(self, out):
		self.fun()
		out.write("\n")

	def __str__(self):
		return "<heartbeat>"


class ActionResource(Resource):

	def __init__(self, loc, fun = lambda: None):
		Resource.__init__(self, loc)
		self.fun = fun

	def get_mime(self):
		return "text/plain"

	def generate(self, out):
		self.fun()
		out.write("\n")

	def __str__(self):
		return f"action:{self.fun}"


class FileResource(Resource):
	"""Resource for the content of a file."""

	def __init__(self, path, loc):
		Resource.__init__(self, loc)
		self.path = path

	def get_mime(self):
		return mimetypes.guess_type(self.path)[0]

	def prepare(self):
		if not os.access(self.path, os.R_OK):
			raise common.ThotException(f"cannot access {self.path}")

	def generate(self, out):
		ext = os.path.splitext(self.path)[1]

		# relocated file
		if ext in ahtml.RELOCATORS:
			reloc = ahtml.RELOCATORS[ext]
			reloc.move_to_stream(self.path, self.loc, out, self.manager)

		# send text file
		elif self.get_mime() in TEXT_MIMES:
			with open(self.path, encoding="utf-8") as file:
				for l in file:
					out.write(l)

		# send binary file
		else:
			file = open(self.path, "rb")
			while True:
				b = file.read(4096)
				if b == b'':
					break
				else:
					out.write_bin(b)
			file.close()

	def __str__(self):
		return self.path


VIEW_SCRIPT = """
	const thot_request = new XMLHttpRequest();

	function send(cmd) {
		thot_request.open("GET", cmd, true);
		thot_request.send();
	}

	function quit() {
		send("/quit");
		sleep(500);
	}

	function heartbeat() {
		send("/heartbeat");
	}
	setInterval(heartbeat, 1000);
"""


class Generator(ahtml.Generator):
	"""Specialized generator."""

	def __init__(self, doc):
		ahtml.Generator.__init__(
			self, doc.get_document(),
			manager = doc.get_manager(),
			template = doc.get_template())
		self.base_level = doc.get_base_level()
		self.out_path = doc.get_location()
		script = self.newScript()
		script.content = VIEW_SCRIPT

	def genHeader(self, header):
		header.header_level -= self.base_level
		ahtml.Generator.genHeader(self, header)
		header.header_level += self.base_level
		return True

	def genLinkBegin(self, url, title = None):
		if not self.is_distant_url(url):
			url = self.manager.use_resource(url)
		ahtml.Generator.genLinkBegin(self, url, title)


class ViewTemplate(ahtml.FileTemplate):

	def __init__(self, doc, path):
		ahtml.FileTemplate.__init__(self,
			path,
			env = doc.env,
			style_authoring = doc.gen_style_authoring,
			subtitle = doc.gen_subtitle,
			icon = doc.gen_icon
		)
		self.doc = doc

	def use_listing(self, type):
		styles = self.doc.env["HTML_STYLES"].split(":")
		if styles == []:
			return False
		base = os.path.splitext(os.path.basename(styles[0]))[0]
		path = self.doc.env.reduce(f"@(THOT_BASE)/css/{base}-{type}.css")
		res = os.path.exists(path)
		if res:
			styles.append(path)
			self.doc.env["HTML_STYLES"] = ":".join(styles)
		return res

	def apply(self, handler, gen):
		ahtml.FileTemplate.apply(self, handler, gen)


class DocResource(Resource, ahtml.TemplateHandler):
	"""Generator for Thot document."""

	def __init__(self, document, man, loc):
		Resource.__init__(self, loc, man)
		self.document = document
		self.node = None
		self.style = "blue-penguin"
		self.style_author = None
		self.template = None
		self.date = None
		self.env = None
		self.title = None
		self.base_level = None

	def get_mime(self):
		return "text/html"

	def prepare(self):
		"""Read the document."""
		if self.node is not None \
		and self.date >= os.stat(self.document).st_mtime:
			return
		self.env = self.manager.env.copy()
		parser = self.manager.parser

		# prepare the environment
		self.env["THOT_FILE"] = self.document
		dir = os.path.dirname(self.document)
		if dir == "":
			dir = "."
		self.env["THOT_DOC_DIR"] = dir
		css = [self.env.reduce(f"@(THOT_BASE)/view/{self.style}.css")]
		self.env["HTML_STYLES"] = ":".join(css)

		# build the document
		self.node = doc.Document(self.env)
		parser.clear(self.node)
		self.get_manager().mon.say("parsing %s", self.document)
		parser.parse(self.document)
		self.date = os.stat(self.document).st_mtime

		# look for the structure
		if self.get_manager().single:
			self.title = doc.Par([doc.Word(self.env["TITLE"])])
		elif len(self.node.content) == 1 \
		and isinstance(self.node.content[0], doc.Header):
			self.title = self.node.content[0].title
		else:
			title = os.path.splitext(os.path.basename(self.document))[0]
			self.title = doc.Par([doc.Word(title)])

		# find base level
		self.base_level = 10
		for c in self.node.content:
			if isinstance(c, doc.Header):
				self.base_level = min(self.base_level, c.header_level)

		# prepare links
		self.make_links()

	def get_document(self):
		"""Get the documenty itself for this resource."""
		return self.node

	def get_base_level(self):
		"""Get the base level for headers."""
		return self.base_level

	def gen_subtitle(self, gen):
		title = self.node.env['TITLE']
		if title != '':
			gen.out.write(f"<h2>{title}</h2>")

	def gen_style_authoring(self, gen):
		if self.style_author is None:
			name = os.path.splitext(os.path.basename(self.style))[0]
			self.style_author = name
			try:
				with open(self.node.env.reduce(self.style), encoding="utf8") as input:
					l = input.readline()
					if l.startswith("/*") and l.endswith("*/\n"):
						self.style_author = f'<a href="{l[2:-3].strip()}">{name}</a>'
			except OSError:
				pass
		gen.out.write(self.style_author)

	def gen_icon(self, gen):
		icon = self.node.env["ICON"]
		if icon != "":
			icon = self.node.env.reduce(icon)
			icon = self.manager.use_resource(icon)
			icon = self.manager.get_resource_link(icon, self.get_location())
			gen.out.write(f'<div class="icon"><img src="{icon}"/></div>')

	def generate(self, out):
		if self.node is None:
			self.prepare()
		path = os.path.join(self.node.env["THOT_BASE"], "view/template.html")
		ViewTemplate(self, path)
		gen = Generator(self)
		self.node.pregen(gen)
		gen.out = out
		gen.getTemplate().apply(self, gen)

	def get_template(self):
		"""Get the temlate of the document resource."""
		if self.template is None:
			if self.get_manager().single:
				path = os.path.join(self.node.env["THOT_BASE"], "themes/plain.html")
			else:
				path = os.path.join(self.node.env["THOT_BASE"], "view/template.html")
			self.template = ViewTemplate(self, path)
		return self.template

	def gen_header(self, gen):
		gen.gen_header()

	def gen_title(self, gen):
		doc.Container.gen(self.title, gen)

	def gen_content(self, gen):
		self.node.gen(gen)

	def gen_authors(self, gen):
		gen.genAuthors()

	def __str__(self):
		return f"doc:{self.document}"

	def make_links(self):
		"""Create links for all objects that support a link."""
		for node in self.node.get_labelled_nodes():
			self.get_manager().declare_link(node, self.document)


class Manager(ahtml.Manager):
	"""Manager for thot-view."""

	def __init__(self, document,
		verbose = False,
		mon = common.DEFAULT_MONITOR,
		single = False
	):
		ahtml.Manager.__init__(self, mon = mon)
		self.verbose = verbose
		self.mon = mon
		self.mon.set_verbosity(verbose)
		self.tmpdir = None
		self.single = single

		# prepare environment
		self.env = common.Env()
		config_path = None
		home = os.path.expanduser('~')
		dir = os.path.abspath(os.path.dirname(document))
		while True:
			path = os.path.join(dir, 'config.thot')
			if os.path.exists(path):
				config_path = path
				break
			if dir == home:
				dir = os.path.abspath(os.path.dirname(document))
				break
			ndir = os.path.dirname(dir)
			if ndir == dir:
				break
			dir = ndir

		# initialize environment
		self.base_dir = dir
		self.env["THOT_BASE_DIR"] = dir
		self.env['THOT_OUT_TYPE'] = 'html'

		# load the config
		self.base_doc = doc.Document(self.env)
		self.parser = tparser.Manager(self.base_doc)
		if config_path is not None:
			self.mon.say("readind configuration from %s", config_path)
			self.dir = dir
			try:
				self.parser.parse(config_path, self.base_doc)
			except common.ParseException as e:
				self.mon.error("error in parsing %s: %s (ignoring)",
					config_path, e)

		# prepare file system
		self.fsmap = {}
		self.counter = 0
		self.tmpdir = None
		self.map = {}

		# prepare initial document
		dpath = self.use_resource(document)
		gen = self.fsmap[dpath]
		self.alias_resource(gen, '/')
		self.alias_resource(gen, '/index.html')
		self.alias_resource(gen, '/index.htm')

	def __del__(self):
		if self.tmpdir is not None:
			shutil.rmtree(self.tmpdir)

	def is_interactive(self):
		return True

	def alias_resource(self, res, loc):
		"""Add an aliases to a resource."""
		self.mon.say("alias %s to %s", res, loc)
		self.map[loc] = res

	def link_resource(self, res):
		"""Add a resource."""
		self.map[res.loc] = res
		res.manager = self

	def make_gen(self, path, loc):
		"""Build a generator for the given path."""
		ext = os.path.splitext(path)[1]
		if ext in PARSERS:
			loc = os.path.splitext(loc)[0] + ".html"
			return DocResource(path, self, loc)
		else:
			return FileResource(path, loc)

	def use_resource(self, path):
		rpath = os.path.normpath(os.path.abspath(path))
		if rpath not in self.fsmap:
			if rpath.startswith(self.base_dir):
				loc = rpath[len(self.base_dir):]
			else:
				name = os.path.basename(rpath)
				base, ext = os.path.splitext(rpath)
				loc = f"/static/{name}"
				cnt = 0
				while loc in self.map:
					loc = f"{base}-{cnt}{ext}"
					cnt = cnt + 1
			res = self.make_gen(rpath, loc)
			self.fsmap[rpath] = res
			self.link_resource(res)
		return rpath

	def new_resource(self, path = None, ext = None):
		if self.tmpdir is None:
			self.tmpdir = os.path.abspath(tempfile.mkdtemp(prefix = "thot-"))
		if path is None:
			path = f"file-{self.counter}{ext}"
			self.counter += 1
		loc = f"/static/{path}"
		path = os.path.join(self.tmpdir, path)
		self.ensure_dir(os.path.dirname(path))
		res = self.make_gen(path, loc)
		self.fsmap[path] = res
		self.link_resource(res)
		return path

	def get_resource_link(self, path, ref):
		if ":" in path:
			return path
		else:
			path = os.path.normpath(path)
			res_loc = self.fsmap[path].loc
			link = os.path.relpath(res_loc, os.path.dirname(ref))
			return link

	def get_number(self, node):
		return None

	def get_anchor(self, node):
		return None


class RequestHandler(http.server.SimpleHTTPRequestHandler):

	def write(self, text):
		self.wfile.write(bytes(text, "UTF8"))

	def write_bin(self, text):
		self.wfile.write(text)

	def do_GET(self):
		self.server.record_heartbeat()
		path = unquote(self.path)
		try:
			file = self.server.manager.map[path]
			file.prepare()
		except KeyError:
			msg = f"{path} not found"
			self.send_error(404, msg)
			return
		except common.ThotException as e:
			self.send_error(500)
			self.error(f"error for {path}: {e}")
			return

		self.send_response(200)
		self.send_header("Content-type",  file.get_mime())
		self.end_headers()
		file.generate(self)

	def do_POST(self):
		self.server.record_heartbeat()
		path = unquote(self.path)

		# find the resource
		try:
			file = self.server.manager.map[path]
		except KeyError:
			msg = f"{path} not found"
			self.send_error(404, msg)
			return

		# process message
		try:

			# post the message
			res = file.post(int(self.headers['content-length']), self.rfile)
			if res is not None:
				self.send_error(res[0], res[1])
				return

			# build answer
			self.send_response(200)
			self.send_header("Content-type",  file.get_mime())
			self.end_headers()
			file.answer(self.wfile)

		except common.ThotException as e:
			self.send_error(500)
			self.error(f"error for {path}:  {e}")
			return

	def error(self, msg):
		self.server.mon.error(msg)

	def log_error(self, fmt, *args):
		self.error(fmt % args)

	def log_message(self, fmt, *args):
		pass


class MyServer(http.server.HTTPServer):

	def __init__(self, manager):
		http.server.HTTPServer.__init__(self,
			('localhost', 0),
			RequestHandler)
		self.manager = manager
		self.mon = manager.mon
		manager.link_resource(ActionResource("/quit", self.quit))
		manager.link_resource(ActionResource("/heartbeat", self.record_heartbeat))
		self.heartbeat_started = False
		self.last_heartbeat = None

	def get_address(self):
		return self.socket.getsockname()

	def run_browser(self):
		time.sleep(.5)
		webbrowser.open_new_tab(f"http://{self.get_address()}")

	def quit(self):
		self.mon.say("Quit.")
		threading.Thread(target = self.shutdown).start()

	def run(self):
		self.mon.say("Listening to %s", self.get_address())
		threading.Thread(target = self.run_browser).start()
		try:
			http.server.HTTPServer.serve_forever(self)
		except KeyboardInterrupt:
			self.shutdown()

	def check_heartbeat(self):
		while True:
			time.sleep(HEARTBEAT_TIMEOUT)
			delay = time.time() - self.last_heartbeat
			if delay > HEARTBEAT_TIMEOUT:
				self.quit()
				break

	def record_heartbeat(self):
		self.last_heartbeat = time.time()
		if not self.heartbeat_started:
			self.heartbeat_started = True
			threading.Thread(target = self.check_heartbeat).start()


def main():
	mon = common.DEFAULT_MONITOR

	# process arguments
	parser = argparse.ArgumentParser(
			prog = "thow-view",
			description = "Fast viewer for wiki-like documentation."
		)
	parser.add_argument('document', nargs='?')
	parser.add_argument('--single', action='store_true',
		help="Consider the passed document as single, not part of a wiki.")
	parser.add_argument('-v', '--verbose', action='store_true',
		help="Enable verbose mode.")
	parser.add_argument("--version", action="store_true",
		help="print version")

	args = parser.parse_args()

	# version support
	if args.version:
		common.print_version()
		sys.exit()

	# find the file to open
	path = args.document
	if path is None:
		path = os.getcwd()
	if os.path.isdir(path):
		found = False
		for ext in tparser.PARSERS.keys():
			fpath = os.path.join(path, "index" + ext)
			if os.path.isfile(fpath):
				path = fpath
				found = True
				break
		if not found:
			mon.fatal("no document to open")

	# run the server
	manager = Manager(path, args.verbose, mon=mon, single=args.single)
	MyServer(manager).run()


if __name__ == "__main__":
	main()
