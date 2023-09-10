#
# code -- Thot codeme module
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

"""This module allows interactive coding from a viewed page. The initial syntax is:
	<codeme OPTIONS>...</codem>
that displays a box where the user can type a program and launch it."""

import subprocess
from thot import doc, block, communicate, view

# Maps of used blocks
MAP = {}

class Resource(view.Resource):

	def __init__(self):
		view.Resource.__init__(self, "/codeme/run")
		self.interpreter = None
		self.timeout = None
		self.skip = None

	def get_mime(self):
		return "text/plain"

	def post(self, size, input):
		self.msg = communicate.Message(size, input)
		self.source = self.msg.get_attr('source')
		self.block = MAP[self.msg.get_attr("id")]
		self.test = self.msg.get_attr('test')
		return None

	def run(self, sources):

		# launch the process
		proc = subprocess.Popen(self.block.interpreter,
				stdin = subprocess.PIPE,
				stdout = subprocess.PIPE,
				stderr = subprocess.STDOUT
			)

		# perform communication
		try:
			outs, errs = proc.communicate(
				input = bytes("\n".join(sources), 'utf8'),
				timeout = self.block.timeout)
			out = outs.decode('utf8')
		except subprocess.TimeoutExpired:
			proc.kill()
			return "Timeout expired!"

		# skip if needed
		skip = self.block.skip
		if skip > 0:
			p = 0
			while skip > 0:
				try:
					p = out.index('\n', p)
					p = p + 1
					skip = skip - 1
				except ValueError:
					out = ""
					break
			out = out[p:]

		# skip last if needed
		skip = self.block.skiplast
		if skip > 0:
			p = len(out)
			while skip > 0:
				try:
					p = out.index('\n', 0, p)
					p = p - 1
					skip = skip - 1
				except ValueError:
					out = ""
					break
			out = out[:p+1]

		return out

	def output(self, msg, test = None):
		if test == None:
			id = "codeme-output-%d" % self.block.num
		else:
			id = "codeme-output-%d-%d" % (self.block.num, test)
		self.msg.set_value(id, msg)
		
		
	def answer(self, output):

		# prepare execution
		sources = [self.block.prolog, self.source]

		# simple execution
		if self.test == 0:
			self.output(self.run(sources + [self.block.epilog]))

		# test execution
		else:
			test = self.block.tests[self.test - 1]
			sources = sources + [test.code, self.block.epilog]
			result = self.run(sources)
			self.output(result, self.test)
			if test.expected != "":
				add_cls = "success"
				rem_cls = "fail"
				if test.expected.strip() == result.strip():
					lab = "success!"
				else:
					lab = "failed."
					add_cls, rem_cls = rem_cls, add_cls
				id = "codeme-lab-%s-%s" % (self.block.num, test.num)
				self.msg.set_content(id, lab)
				self.msg.add_class(id, add_cls)
				self.msg.remove_class(id, rem_cls)
				id = "codeme-output-%s-%s" % (self.block.num, test.num)
				self.msg.add_class(id, add_cls)
				self.msg.remove_class(id, rem_cls)

		# reply in the end
		self.msg.reply(output)

	def __str__(self):
		return self.loc

RESOURCE = Resource()

class Feature(doc.Feature):

	def prepare(self, gen):
		script = gen.newScript()
		script.content = """
function codeme_run(id, test) {
	const source = document.getElementById("codeme-source-" + id);
	const xhr = new XMLHttpRequest();
	com_send("/codeme/run", {
		id: id,
		source: source.value,
		test: test
	});
}

function codeme_show_result(select, id, test) {
	console.log("select=" + select);
	const test_comp = document.getElementById("codeme-test-" + id + "-" + test);
	const result_comp = document.getElementById("codeme-result-" + id + "-" + test);
	if(select) {
		test_comp.style.display = "none";
		result_comp.style.display = "inline";
	}
	else {
		test_comp.style.display = "inline";
		result_comp.style.display = "none";
	}
}
"""
		gen.get_manager().link_resource(RESOURCE)

	def gen_header(self, gen):
		gen.gen_style("""
div.codeme span.success {
	color: green;
}
div.codeme span.fail {
	color: red;
}

div.codeme textarea.result {
	background: lightblue;
}

div.codeme textarea.success {
	background: lightgreen;
}

div.codeme textarea.fail {
	background: lightpink;
}

div.codeme-source {
	padding-top: 1em;
}
""")

FEATURE = Feature()


class Test:

	def __init__(self, num):
		self.num = num
		self.code = ""
		self.expected = ""


class Block(block.Block):

	STATES = {
		"@@prolog:":
			lambda self: self.add_prolog,
		"@@epilog:":
			lambda self: self.add_epilog,
		"@@test:":
			lambda self: self.add_test(),
		"@@expected:":
			lambda self: self.add_expected()
	}
	
	def __init__(self, syntax, man):
		block.Block.__init__(self, syntax, man)
		self.num = self.new_num()
		man.get_doc().addFeature(FEATURE)
		man.get_doc().addFeature(communicate.FEATURE)
		self.prolog = ""
		self.epilog = ""
		self.init = ""
		self.tests = []
		self.state = self.add_init

	def check_args(self, man):
		self.interpreter = self.get_option("interpreter")
		if self.interpreter == None:
			man.error("No interpeter defined!")
		self.language = self.get_option("language")
		self.timeout = self.get_option("timeout")
		self.skip = self.get_option("skip")
		self.skiplast = self.get_option("skiplast")
		self.cols = self.get_option("cols")
		self.rows = self.get_option("rows")
		self.testrows = self.get_option("testrows")

	def add_content(self, content, line):
		if content == "":
			return line
		else:
			return content + "\n" + line

	def add_init(self, line):
		self.init = self.add_content(self.init, line)

	def add_test_line(self, line):
		self.tests[-1].code = self.add_content(self.tests[-1].code, line)
	
	def add_test(self):
		self.tests.append(Test(len(self.tests) + 1))
		return self.add_test_line

	def add_expected_line(self, line):
		self.tests[-1].expected = self.add_content(self.tests[-1].expected, line)

	def add_expected(self):
		if self.tests == []:
			return lambda line: None
		else:
			return self.add_expected_line

	def add_prolog(self, line):
		self.prolog = self.add_content(self.prolog, line)
	
	def add_epilog(self, line):
		self.epilog = self.add_content(self.epilog, line)

	def add(self, line):
		if not line.startswith("@@"):
			self.state(line)
		else:
			try:
				self.state = Block.STATES[line.strip()](self)
			except KeyError:
				self.state(line)

	def gen(self, gen):
		if gen.getType() != "html":
			gen.warn("codeme: unsupported output!", node=self)
			return

		# non-interactive
		if not gen.get_manager().is_interactive() or self.interpreter == None:
			if init != "":
				gen.genQuoteBegin()
				gen.genStyleBegin(doc.STYLE_CODE)
				gen.genText(self.init)
				gen.genStyleEnd(doc.STYLE_CODE)
				gen.genQuoteEnd()
			return

		# interactive
		MAP[self.num] = self
		gen.genVerbatim("""
<div class="codeme">
	<div class="codeme-source">
		<textarea id="codeme-source-{num}" cols="80" rows="15">{init}</textarea>
	</div>
""".format(
	num = self.num,
	init = self.init
))
		if self.tests == []:
			gen.genVerbatim("""
	<div class="output">
		<button onclick="codeme_run({num}, 0)">Run!</button>
		<br/>
		<textarea id="codeme-output-{num}" cols="{cols}" rows="{rows}" readonly></textarea>
	</div>
""".format(
		num = self.num,
		cols = self.cols,
		rows = self.rows
	))

		else:
			
			for test in self.tests:
				syms = dict(
					num = self.num,
					tnum = test.num,
					code = test.code,
					expected = test.expected,
					cols = self.cols/2,
					rows = self.testrows					
				)
				gen.genVerbatim("""
	<div>
		<button onclick="codeme_run({num}, {tnum})">Run test {tnum}</button>
		<span id="codeme-lab-{num}-{tnum}"></span>""".format(**syms))
				if test.expected != "":
					gen.genVerbatim("""
		<input onchange="codeme_show_result(this.checked, {num}, {tnum});" type="checkbox">show expected</input>""".format(**syms))
				gen.genVerbatim("""
	</div>
	<div>
		<textarea id="codeme-test-{num}-{tnum}" cols="{cols}" rows="{rows}" readonly>{code}</textarea>""".format(**syms))
				if test.expected != "":
					gen.genVerbatim("""
		<textarea id="codeme-result-{num}-{tnum}" class="result" style="display: none;" cols="{cols}" rows="{rows}" readonly>{expected}</textarea>""".format(**syms))
				gen.genVerbatim("""
		<textarea id="codeme-output-{num}-{tnum}" cols="{cols}" rows="{rows}" readonly></textarea>
	</div>""".format(**syms))

		gen.genVerbatim("</div>")
			

__short__ = """Interactive documentation and conding."""
__description__ = \
"""This modules allows to insert code typing in a document and executing and testing of it."""

__syntaxes__ = [
	block.Syntax(
		name = "codeme",
		maker = Block, 
		options=[
			block.Option("language"),
			block.Option("interpreter"),
			block.IntOption("timeout", 4),
			block.IntOption("skip", 0),
			block.IntOption("skiplast", 0),
			block.IntOption("cols", 80),
			block.IntOption("rows", 10),
			block.IntOption("testrows", 4)
		])
]

