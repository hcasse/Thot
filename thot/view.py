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
import tempfile
import threading
import time
import webbrowser

import thot.command as command
import thot.common as common
import thot.doc as doc
import thot.htmlman as htmlman
import thot.tparser as tparser
import thot.backs.abstract_html as ahtml


"""Heartbeat time-out in seconds."""
HEARTBEAT_TIMEOUT = 1.1		

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

	def __init__(self, loc):
		self.loc = loc

	def get_mime(self):
		"""Called to get MIME type."""

	def prepare(self):
		"""Prepare the generation."""
		pass

	def generate(self, out):
		"""Called to generate on the given output."""
		pass


class HeartBeatResource(Resource):

	def __init__(self, loc, fun = lambda: None):
			Resource.__init__(self, loc)
			self.fun = fun

	def get_mime(self):
		return "text/plain"

	def generate(self, out):
		self.fun()
		out.write("\n")


class ActionResource(Resource):

	def __init__(self, loc, fun = lambda: None):
			Resource.__init__(self, loc)
			self.fun = fun

	def get_mime(self):
		return "text/plain"

	def generate(self, out):
		self.fun()
		out.write("\n")


class FileResource(Resource):
	"""Resource for the content of a file."""

	def __init__(self, path, loc):
		Resource.__init__(self, loc)
		self.path = path

	def get_mime(self):
		return mimetypes.guess_type(self.path)[0]		

	def prepare(self):
		if not os.access(self.path, os.R_OK):
			raise common.ThotException("cannot access %s" % self.path)

	def generate(self, out):

		# send text file
		if self.get_mime() in TEXT_MIMES:
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


class Generator(ahtml.Generator):
	"""Specialized generator."""

	def __init__(self, doc, man, template, base_level):
		ahtml.Generator.__init__(self, doc, man, template)
		self.base_level = base_level

	def genHeader(self, header):
		header.header_level -= self.base_level
		ahtml.Generator.genHeader(self, header)
		header.header_level += self.base_level
		return True


class DocResource(Resource, ahtml.PageHandler):
	"""Generator for Thot document."""

	def __init__(self, document, man, loc):
		Resource.__init__(self, loc)
		self.document = document
		self.node = None
		self.man = man
		self.style = "@(THOT_BASE)/view/blue-penguin.css"
		self.style_author = None

	def get_mime(self):
		return "text/html"

	def prepare(self):
		"""Read the document."""

		# prepare the environment
		env = command.make_env()
		env['THOT_OUT_TYPE'] = 'html'
		env["THOT_FILE"] = self.document
		env["THOT_DOC_DIR"] = os.path.dirname(self.document)
		env["HTML_STYLES"] = env.reduce(self.style)

		# build the document
		self.node = doc.Document(env)
		parser = tparser.Manager(self.node)
		ext = os.path.splitext(self.document)[1]
		mod = PARSERS[ext]
		if mod != None:
			parser.use(mod)
		with open(self.document) as input:
			parser.parse(input, self.document)

		# look for the structure
		if len(self.node.content) == 1 \
		and isinstance(self.node.content[0], doc.Header):
			self.title = self.node.content[0].title
			self.node.content = self.node.content[0].content
		else:
			title = os.path.splitext(os.path.basename(self.document))[0]
			self.title = doc.Par([doc.Word(title)])

		# find base level
		#self.node.dump('')
		self.base_level = 10;
		for c in self.node.content:
			if isinstance(c, doc.Header):
				self.base_level = min(self.base_level, c.header_level)

	def gen_style_authoring(self, gen):
		if self.style_author == None:
			name = os.path.splitext(os.path.basename(self.style))[0]
			self.style_author = name
			try:
				with open(self.node.env.reduce(self.style)) as input:
					l = input.readline()
					if l.startswith("/*") and l.endswith("*/\n"):
						self.style_author = '<a href="%s">%s</a>' \
							% (l[2:-3].strip(), name)
			except OSError:
				pass
		gen.out.write(self.style_author)

	def generate(self, out):
		if self.node == None:
			self.prepare()
		template = ahtml.TemplatePage(
			os.path.join(self.node.env["THOT_BASE"], "view/template.html"),
			self.node.env,
			style_authoring = self.gen_style_authoring)
		gen = Generator(self.node, self.man, template, self.base_level, )
		self.node.pregen(gen)
		gen.out = out
		gen.getTemplate().apply(self, gen)

	def gen_header(self, gen):
		gen.gen_header()

	def gen_title(self, gen):
		doc.Container.gen(self.title, gen)

	def gen_content(self, gen):
		self.node.gen(gen)


class Manager(htmlman.Manager):

	def __init__(self, document):
		self.dir = os.path.abspath(os.path.dirname(document))
		gen = DocResource(document, self, "/index.html")
		self.map = {}
		self.map['/'] = gen
		self.map['/index.html'] = gen
		self.map['/index.htm'] = gen
		self.map['/%s' % os.path.basename(document)] = gen
		self.fsmap = {}
		self.counter = 0
		self.tmpdir = None

	def link_resource(self, res):
		"""Add a resource."""
		self.map[res.loc] = res

	def make_gen(self, path, loc):
		"""Build a generator for the given path."""
		ext = os.path.splitext(path)[1]
		if ext in PARSERS:
			return DocResource(path, self, loc)
		else:
			return FileResource(path, loc)

	def canonize(self, path, doc):
		if not os.path.isabs(path):
			if doc != None:
				path = os.path.join(os.path.dirname(doc.getVar("THOT_FILE")), path)
			path = os.path.abspath(path)
		return os.path.normpath(path)

	def add_resource(self, path, doc = None):
		path = self.canonize(path, doc)
		if path not in self.fsmap:
			if path.startswith(self.dir):
				loc = path[len(self.dir):]
				res = self.make_gen(path, loc)
			else:
				ext = os.path.splitext(path)[1]
				loc = "/static/file-%d%s" % (self.counter, ext)
				self.counter += 1
				res = self.make_gen(path, loc)
			self.fsmap[path] = res
			self.map[loc] = res
		return path

	def create_resource(self, ext, id = None):
		if self.tmpdir == None:
			self.tmpdir = tempfile.TemporaryDirectory(prefix = "thot")
		name = "file-%d%s" % (self.counnter, ext)
		self.counter += 1
		loc = "/static/%s" % name
		path = os.path.join(self.tmpdir.name, name)
		res = make_gen(path)
		self.map[loc] = res
		self.fsmap[path] = res
		return path

	def get_resource_loc(self, path, doc = None):
		path = self.canonize(path, doc)
		try:
			loc = self.fsmap[path].loc
			return loc
		except KeyError:
			return "broken link"

	def get_number(self, node):
		return None

	def get_anchor(self, node):
		return None

	def get_link(self, node):
		return None


class RequestHandler(http.server.SimpleHTTPRequestHandler):

	def write(self, text):
		self.wfile.write(bytes(text, "UTF8"))

	def write_bin(self, text):
		self.wfile.write(text)

	def do_GET(self):
		#print("DEBUG: path=", self.path)
		try:
			file = self.server.manager.map[self.path]
			file.prepare()
		except KeyError:
			msg = "%s not found" % self.path
			self.send_error(404, msg)
			return
		except common.ThotException as e:
			self.send_error(500)
			self.error("error for %s: %s" % (self.path, e))
			return
			
		self.send_response(200)
		self.send_header("Content-type",  file.get_mime())
		self.end_headers()
		file.generate(self)

	def error(self, msg):
		self.log_error("%s %s", self.log_date_time_string(), msg)

	def log_error(self, fmt, *args):
		http.server.SimpleHTTPRequestHandler.log_message(self, fmt % args)

	def log_message(self, fmt, *args):
		pass


class MyServer(http.server.HTTPServer):

	def __init__(self, doc):
		http.server.HTTPServer.__init__(self,
			('localhost', 0),
			RequestHandler)
		self.manager = Manager(doc)
		self.manager.link_resource(ActionResource("/quit",
			self.quit))

	def get_address(self):
		return self.socket.getsockname()

	def run_browser(self):
		time.sleep(.5)
		webbrowser.open_new_tab("http://%s:%d" % self.get_address())

	def quit(self):
		threading.Thread(target = self.shutdown).start()

	def serve_forever(self):
		print("Listening to", self.get_address())
		threading.Thread(target = self.run_browser).start()
		try:
			http.server.HTTPServer.serve_forever(self)
		except KeyboardInterrupt:
			self.shutdown()


if __name__ == "__main__":

	# entry point
	parser = argparse.ArgumentParser(
			prog = "thow-view",
			description = "Fast viewer for wiki-like documentation."
		)
	parser.add_argument('document', nargs=1)
	args = parser.parse_args()

	# run the server
	MyServer(args.document[0]).serve_forever()

	
