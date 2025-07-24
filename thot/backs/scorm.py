# scorm -- Scorm back-end
# Copyright (C) 2013  <hugues.casse@laposte.net>
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

"""SCORM extension for Thot."""

import html
import os
import os.path

from thot import common

ZIP = common.Command("zip", "unzip unavaible to build the final archive")

# get the html module
out_path = os.path.dirname(__file__)
html = common.loadModule("html",  out_path)
if not html:
	common.onError("cannot found html backend !")


# SCORM generator
class ScormGenerator(html.Generator):

	def __init__(self, doc):
		html.Generator.__init__(self, doc)

	def genTitle(self):
		"""No title."""
		pass

	def genContent(self, max = 7, out = False):
		"""No content."""
		pass


class Generator:
	doc = None
	html = None
	pack_files = None

	def __init__(self, doc, html):
		self.doc = doc
		self.html = html
		self.pack_files = []

	def genSequencing(self, item, indent, out):
		"""Generate sequencing content."""
		controlMode = item.getInfo("scorm:controlMode")
		conds = item.getInfo("scorm:conds")
		limits = item.getInfo("scorm:limits")
		if controlMode or conds or limits:
			out.write(f"{indent}<imsss:sequencing>\n")
			if controlMode:
				out.write(f"{indent}\t<imsss:controlMode {' '.join(controlMode)} />\n")
			if conds:
				for cond in conds:
					cond.gen(indent + "\t", out)
			if limits:
				out.write(f'{indent}\t<imsss:limitConditions {' '.join(limits)}/>\n')
			out.write(f"{indent}</imsss:sequencing>\n")

	def genItem(self, header, i, out):
		"""Generate an item of the organization for the given header."""
		out.write(f"\t\t<item identifier=\"item_{i}\" identifierref=\"resources_{i}\">\n")
		out.write(f"\t\t\t<title>{html.escape(header.getTitle().toText())}</title>\n")
		self.genSequencing(header, "\t\t\t", out)
		out.write("\t\t</item>\n")

	def genManifest(self):
		"""Generate the ismmanifest."""
		try:
			out = open("imsmanifest.xml", "w", encoding="utf8")
			self.pack_files.append("imsmanifest.xml")

			# write header
			out.write(
"""<?xml version="1.0" standalone="no" ?>
<manifest identifier="com.scorm.golfsamples.contentpackaging.multioscosinglefile.20043rd"
		version="1"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
          xmlns:adlseq="http://www.adlnet.org/xsd/adlseq_v1p3"
          xmlns:adlnav="http://www.adlnet.org/xsd/adlnav_v1p3"
          xmlns:imsss="http://www.imsglobal.org/xsd/imsss">

  <metadata>
	<schema>ADL SCORM</schema>
	<schemaversion>2004 3rd Edition</schemaversion>
  </metadata>

""")

			# write organization
			out.write("<organizations default=\"default\">\n")
			out.write("\t<organization identifier=\"default\">\n")
			out.write(f"\t\t<title>{html.escape(self.doc.getVar('TITLE'))}</title>\n")
			self.genSequencing(self.doc, "\t\t", out)
			cnt = 0
			for item in [i for i in self.doc.getContent() if i.getHeaderLevel() == 0 ]:
				self.genItem(item, cnt, out)
				cnt = cnt + 1
			out.write("\t</organization>\n")
			out.write("</organizations>\n\n")

			# write resources
			out.write("<resources>\n")
			cnt = 0
			for item in [i for i in self.doc.getContent() if i.getHeaderLevel() == 0]:
				out.write(f"\t<resource identifier=\"resources_{cnt}\" " +
					"type=\"webcontent\" adlcp:scormtype=\"asset\" " +
					"href=\"{self.html.root}-{cnt}.html\">\n")
				out.write(f"\t\t<file href=\"{self.html.root}-{cnt}.html\"/>\n")
				self.pack_files.append("{self.html.root}-{cnt}.html")
				out.write("\t\t<dependency identifierref=\"all_resources\"/>\n")
				out.write("\t</resource>\n")
				cnt = cnt + 1
			out.write("\t<resource identifier=\"all_resources\" " +
				"type=\"webcontent\" adlcp:scormtype=\"asset\">\n")
			ress = []
			for _, _, files in os.walk(self.html.getImportDir()):
				for file in files:
					if file not in ress:
						ress.append(file)
			for file in self.html.addedFiles():
				if file not in ress:
					ress.append(file)
			self.pack_files = self.pack_files + ress + self.doc.getVar("SCORM_FILES").split()
			#for res in ress:
			out.write(f"\t\t<file href=\"{file}\"/>\n")
			out.write("\t</resource>\n")
			out.write("</resources>\n\n")

			# close all
			out.write("</manifest>\n")
			out.close()
		except IOError as e:
			raise common.BackException(str(e))

	def run(self):
		self.doc.setVar("HTML_ONE_FILE_PER", "chapter")
		self.html.run()
		self.genManifest()
		arc = f"{self.html.root}.zip"
		ZIP.call([arc] + self.pack_files)
		print(f"SUCESS: SCORM archive in {arc}")


def output(doc):
	#gen = Generator(doc, html.Generator(doc))
	gen = Generator(doc, ScormGenerator(doc))
	gen.run()
