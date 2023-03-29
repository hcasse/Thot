"""Implements the command thot-view."""

import argparse
import http.server
import mimetypes
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


class FileResource(Resource):
	"""Resource for the content of a file."""

	def __init__(self, path, loc):
		Resource.__init__(self, loc)
		self.path = path

	def get_mime(self):
		return mimetypes.guess_type(self.path)[0]		

	def generate(self, out):

		# send text file
		if self.get_mime() in TEXT_MIMES:
			file = open(self.path, encoding="utf-8")
			for l in file:
				out.write(bytes(l, "utf-8"))
			file.close()

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
		
		

class DocResource(Resource, ahtml.PageHandler):
	"""Generator for Thot document."""

	def __init__(self, document, man, loc):
		Resource.__init__(self, loc)
		self.document = document
		self.node = None
		self.man = man

	def get_mime(self):
		return "text/html"

	def prepare(self):
		"""Read the document."""

		# prepare the environment
		env = command.make_env()
		env['THOT_OUT_TYPE'] = 'html'
		env["THOT_FILE"] = self.document
		env["THOT_DOC_DIR"] = os.path.dirname(self.document)

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

	def generate(self, out):
		if self.node == None:
			self.prepare()
		gen = ahtml.Generator(self.node, self.man)
		self.node.pregen(gen)
		gen.out = out
		gen.getTemplate().apply(self, gen)

	def gen_header(self, gen):
		gen.gen_header()

	def gen_title(self, gen):
		self.title.gen(gen)
		
	def gen_content(self, gen):
		#self.node.dump('')
		self.node.gen(gen)
		gen.genRaw("""
<script>
	

	function quit(e) {
		const xhttp = new XMLHttpRequest();
		xhttp.onreaddystatechange = function() {
			if(this.readyState == 4) {
				if(this.status == 200) {
					window.close();
				}
			}
		}
		xhttp.open("GET", "quit", true);
		xhttp.send();
		now = (new Date()).getTime();
		while(((new Date()).getTime() - now) < 250);
	}

	function link_to(url) {
		window.onunload = null;
		window.location = url;
	}

	var body = document.getElementsByTagName("BODY")[0];
	body.onunload = quit;

</script>
""")


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

	def release(self):
		"""Called to release resources used by the manager."""
		pass

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
			print("DEBUG: add", path, "loc=", loc)
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
			print("DEBUG: link for", path, loc)
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
		print("DEBUG: path=", self.path)
		if self.path == "/quit":
			self.log_message("Exiting...")
			self.send_response(200)
			self.end_headers()
			assassin = threading.Thread(target=server.shutdown)
			assassin.daemon = True
			assassin.start()
			return
		try:
			file = self.server.manager.map[self.path]
			file.prepare()
		except KeyError:
			self.send_error(404)
			return
		except (IOError, OSError) as e:
			self.send_error(500)
			self.log_error(str(e))
			return
			
		self.send_response(200)
		self.send_header("Content-type",  file.get_mime())
		self.end_headers()
		file.generate(self)

def run_browser(addr):
	time.sleep(.5)
	webbrowser.open_new_tab("http://%s:%d" % addr)


if __name__ == "__main__":

	# entry point
	parser = argparse.ArgumentParser(
			prog = "thow-view",
			description = "Fast viewer for wiki-like documentation."
		)
	parser.add_argument('document', nargs=1)
	args = parser.parse_args()

	# build the environment
	manager = Manager(args.document[0])
	try:
		server = http.server.HTTPServer(('localhost', 0), RequestHandler)
		server.manager = manager
		addr = server.socket.getsockname()
		print("Listing to", addr)
		threading.Thread(target = run_browser, args=(addr,)).start()
		server.serve_forever()
	except KeyboardInterrupt:
		server.shutdown()

	
