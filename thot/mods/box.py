# lexicon -- lexicon support for Thot
# Copyright (C) 2018  <hugues.casse@laposte.net>
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

# Provides the following syntax:
# <box options (| title)?> ... </box>
#
# Options encompasses:
#	* type -- info, help, alert, important, tip, download, todo, content.
#	* rounded -- rounded box
#	* color=COLOR -- box color
#	* text=COLOR -- text color
#	* icon=IMAGE-PATH -- box icon
#
# Basically, in HTML, this plug-in provides its own styles but they
# can be overriden by additional theme. The box is colored with
# CSS class corresponding to the "box-TYPE" and "box-rounded"
# for rounded boxes.
#

from os import path
import thot.doc as doc

ID = "box"

TYPES = {
	"info": "Info",
	"help": "Help",
	"alert": "Alert",
	"important": "Important",
	"tip": "Tip",
	"download": "Download",
	"todo": "Todo",
	"content": "Content"
}


class BoxFeature(doc.Feature):

	def prepare(self, gen):
		if gen.getType() == "html":
			base = gen.doc.getVar("THOT_BASE")
			css = path.join(base, "box", "style.css")
			gen.doc.setVar("HTML_STYLES",
				"%s:%s" % (gen.doc.getVar("HTML_STYLES"), css))

FEATURE = BoxFeature()

class BoxBlock(doc.Container):

	def __init__(self, options, title):
		doc.Container.__init__(self)

		self.title = title
		self.type = "content"
		self.rounded = False
		self.color = None
		self.text = None
		self.icon = None
		
		for opt in options.split():
			if opt in TYPES:
				self.type = opt
			elif opt == "rounded":
				self.rounded = True
			elif opt.startswith("color="):
				self.color = opt[6:]
			elif opt.startswith("text="):
				self.text = opt[5:]
			elif opt.startswith("icon="):
				self.icon = opt[5:]

	def onEvent(self, man, event):
		if event.level < doc.L_PAR:
			man.forward(event)
		elif event.id == ID:
			man.pop()
		else:
			self.add(man, event.make())

	def gen_html(self, gen):

		# generate open tag
		atts = []

		cls = ["box", "box-%s" % self.type]
		if self.rounded:
			cls.append("box-rounded")
		atts.append(("class", " ".join(cls)))

		styles = []
		if self.color != None:
			styles.append("background-color: %s;" % self.color)
		if self.icon != None:
			styles.append("background-image: url(%s);"
				% gen.use_friend(self.icon))
		if styles != []:
			atts.append(("style", " ".join(styles)))
		gen.genOpenTag("div", self, atts)

		# generate the title
		gen.genOpenTag("div", self, [("class", "title")])
		if self.title:
			gen.genText(self.title[1:])
		else:
			gen.genText(TYPES[self.type])
		gen.genCloseTag("div")

		# generate the body
		atts = [("class", "body")]
		if self.text != None:
			atts.append(("style", "color: %s;" % self.text))
		gen.genOpenTag("div", self, atts)
		doc.Container.gen(self, gen)
		gen.genCloseTag("div")
			
		gen.genCloseTag("div")

	def gen(self, gen):
		if gen.getType() == "html":
			self.gen_html(gen)
		else:
			common.onWarning("boxes cannot be generated for %s" % gen.getType())
		
	
def handleBoxBegin(man, match):
	man.get_doc().addFeature(FEATURE)
	man.send(doc.ObjectEvent(doc.L_PAR, ID,
		BoxBlock(match.group('box_options'), match.group('box_title'))))


def handleBoxEnd(man, match):
	man.send(doc.CloseEvent(doc.L_PAR, ID, "box"))

__short__ = """Generation of beautiful boxes."""
__description__ = __short__
__version__ = "1.0"


# module descriptors

__lines__ = [
	(handleBoxBegin,
		"^<box\s(?P<box_options>[^|]*)(?P<box_title>\|[^>]*)?>$",
		""""Make a new box with options info, help, alert, important,
		tip, download, todo, content, rounded, color=COLOR, text=COLOR,
		icon=IMAGE."""),
	(handleBoxEnd, "^</box>.*", "Box end.")
]

__html__ = [
	(
"""<div class=\"box-TYPE, (box-rounded)\">
	<div class=\"title\">...</div>
	<div class="\"body\">...</div>
</div>
""",
		"Generated box."),
	("<div class=\"box-rounded, box-TYPE\"> ... </a>",
		"Generated rounded box."),
]
