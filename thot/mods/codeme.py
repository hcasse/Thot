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
	<codeme OPTIONS>...</codeme>
that displays a box where the user can type a program and launch it."""

import os
import re
import signal
import subprocess
from thot import doc, block, communicate, view

SPACE_RE = re.compile(r"\s{2,}")

# Maps of used blocks
MAP = {}

class Resource(view.Resource):

	def __init__(self):
		view.Resource.__init__(self, "/codeme/run")
		self.msg = None
		self.source = None
		self.block = None
		self.test = None

	def get_mime(self):
		return "text/plain"

	def post(self, size, input):
		self.msg = communicate.Message(size, input)
		self.source = self.msg.get_attr('source')
		self.block = MAP[self.msg.get_attr("id")]
		self.test = self.msg.get_attr('test')

	def run(self, sources):

		# launch the process
		try:
			proc = subprocess.Popen(
					self.block.interpreter,
					stdin = subprocess.PIPE,
					stdout = subprocess.PIPE,
					stderr = subprocess.STDOUT,
					shell = True,
					preexec_fn=os.setsid
				)
		except FileNotFoundError:
			return "Bad interpreter!"

		# perform communication
		try:
			outs, _ = proc.communicate(
				input = bytes("\n".join(sources), 'utf8'),
				timeout = self.block.timeout)
			out = outs.decode('utf8')
		except subprocess.TimeoutExpired:
			os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
			return "Timeout expired!"

		# prepare text
		lines = out.split('\n')
		if lines[-1] == '':
			lines = lines[:-1]
		if self.block.skip > 0:
			lines = lines[self.block.skip:]
		if self.block.skiplast > 0:
			lines = lines[:-self.block.skiplast]
		if self.block.norm_spaces:
			lines = [line.strip() for line in lines]
		out = "\n".join(lines)
		return out

	def output(self, msg, test = None):
		if test is None:
			id = f"codeme-output-{self.block.num}"
		else:
			id = f"codeme-output-{self.block.num}-{test}"
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
				if self.block.find:
					success = test.expected.strip() in result.strip()
				else:
					success = test.expected.strip() == result.strip()
				if success:
					lab = "success!"
				else:
					lab = "failed."
					add_cls, rem_cls = rem_cls, add_cls
				id = f"codeme-lab-{self.block.num}-{test.num}"
				self.msg.set_content(id, lab)
				self.msg.add_class(id, add_cls)
				self.msg.remove_class(id, rem_cls)
				id = f"codeme-output-{self.block.num}-{test.num}"
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
	var out_id = "codeme-output-" + id;
	if(test != 0)
		out_id += "-" + test;
	const result_comp = document.getElementById(out_id);
	result_comp.value = "Running test...";
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

function codeme_onkeydown(text, event) {
	if(event.key == 'Tab') {
		event.preventDefault();
		const start = text.selectionStart;
		const end = text.selectionEnd;
		text.value = text.value.substring(0, start) + "\t" + text.value.substring(end);
		text.selectionStart = text.selectionEnd = start + 1;
	}
}
"""
		gen.get_manager().link_resource(RESOURCE)

	def gen_header(self, gen):
		gen.gen_style("""

div.codeme {
	width: max-content;
}

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

div.codeme-test {
	display: flex;
}

div.codeme-test span {
	flex-grow: 1;
	padding-left: 1em;
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
		self.interpreter = None
		self.language = None
		self.timeout = None
		self.skip = None
		self.skiplast = None
		self.cols = None
		self.rows = None
		self.testrows = None
		self.norm_spaces = None
		self.find = None

	def check_args(self, man):
		self.interpreter = self.get_option("interpreter")
		if self.interpreter is None:
			man.error("No interpeter defined!")
		self.language = self.get_option("language")
		self.timeout = self.get_option("timeout")
		self.skip = self.get_option("skip")
		self.skiplast = self.get_option("skiplast")
		self.cols = self.get_option("cols")
		self.rows = self.get_option("rows")
		self.testrows = self.get_option("testrows")
		self.norm_spaces = self.get_option("norm-spaces")
		self.find = self.get_option("find")

	def add_content(self, content, line):
		if content == "":
			if line == "":
				return "\n"
			else:
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
		if not self.tests:
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
		if not gen.get_manager().is_interactive() or self.interpreter is None:
			if self.init != "":
				gen.genQuoteBegin(1)
				gen.genStyleBegin(doc.STYLE_CODE)
				gen.genText(self.init)
				gen.genStyleEnd(doc.STYLE_CODE)
				gen.genQuoteEnd(1)
			return

		# interactive
		MAP[self.num] = self
		map = {
			"num": self.num,
			"cols": self.cols,
			"tcols": self.cols/2,
			"rows": self.rows,
			"trows": self.testrows,
			"init": self.init
		}

		# interactive
		gen.genVerbatim("""
<div class="codeme">
	<div class="codeme-source">
		<textarea id="codeme-source-{num}" cols="{cols}" rows="{rows}"
			placeholder="Type your source here."
			onkeydown="codeme_onkeydown(this, event)"
		>{init}</textarea>
	</div>""".format(**map))

		if not self.tests:
			gen.genVerbatim("""
	<div class="output">
		<button onclick="codeme_run({num}, 0)">Run!</button>
		<br/>
		<textarea id="codeme-output-{num}" cols="{cols}" rows="{trows}" readonly placeholder="Output of the program."></textarea>
	</div>""".format(**map))

		else:

			for test in self.tests:
				map["tnum"] = test.num
				map["code"] = test.code
				map["expected"] = test.expected
				gen.genVerbatim("""
	<div class="codeme-test">
		<button onclick="codeme_run({num}, {tnum})">Run test {tnum}</button>
		<span id="codeme-lab-{num}-{tnum}"></span>""".format(**map))

				if test.expected != "":
					gen.genVerbatim("""
		<input onchange="codeme_show_result(this.checked, {num}, {tnum});"
			type="checkbox">show expected</input>""".format(**map))

				gen.genVerbatim("""
	</div>
	<div>
		<textarea id="codeme-test-{num}-{tnum}" cols="{tcols}" rows="{trows}"
			readonly>{code}</textarea>""".format(**map))

				if test.expected != "":
					gen.genVerbatim("""
		<textarea id="codeme-result-{num}-{tnum}" class="result" style="display: none;"
			cols="{tcols}" rows="{trows}" readonly>{expected}</textarea>""".format(**map))

				gen.genVerbatim("""
		<textarea id="codeme-output-{num}-{tnum}" cols="{tcols}" rows="{trows}"
			readonly placeholder="Result of test {tnum}."></textarea>
	</div>""".format(**map))

		gen.genVerbatim("</div>")


__short__ = """Interactive documentation and conding."""
__description__ = \
"""This modules allows to insert code typing in a document and executing and testing of it."""

__syntaxes__ = [
	block.Syntax(
		name = "codeme",
		maker = Block,
		set = True,
		options=[
			block.Option("language", doc="used programming language"),
			block.Option("interpreter", doc="interpreter command to run"),
			block.SwitchOption("norm-spaces", doc="remove leading and trailing spaces"),
			block.IntOption("timeout", 4, doc="timeout in s before the command is aborted"),
			block.IntOption("skip", 0, doc="number of lines to skip at the start"),
			block.IntOption("skiplast", 0, doc="number of lines to skip at end"),
			block.IntOption("cols", 80, doc="number of columns for the editor area"),
			block.IntOption("rows", 10, doc="number of rows for the editor area"),
			block.IntOption("testrows", 4, doc="number of rows in the result area"),
			block.SwitchOption("find", doc="find the result in output instead of perfect match")
		])
]

