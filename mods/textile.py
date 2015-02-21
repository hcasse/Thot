# textile -- textile front-end
# Copyright (C) 2015  <hugues.casse@laposte.net>
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

# Supported syntax
#
# Text Styling (TS)
#	[ ]	(class)		style class
#	[ ]	(#id)		identifier
#	[ ]	(class#id)
#	[ ]	{CSS}
#	[ ]	[L]			language
#
# Paragrah Styling (PS, includes TS)
#	[ ]	<			align left
#	[ ]	>			align right
#	[ ]	=			centered
#	[ ]	<>			justified
#	[ ]	-			align middle
#	[ ]	^			align top
#	[ ]	~			align bottom
#	[ ]	(+			indentation
#	[ ]	)+			indentation
#
# Text format (supports TS)
#	[x]	_xxx_		emphasize / italics
#	[x]	__xxx__		italics
#	[x]	*xxx*		strongly emphasized / bold
#	[x]	**xxx**		bold
#	[x]	-xxx-		strikethrough
#	[x]	+xxx+		underline
#	[x]	++xxx++		bigger
#	[x]	--smaller--	smaller
#	[x]	%...%		span
#	[x]	~xxx~		subscript
#	[x]	??xxx??		citation
#	[x]	^xxx^		supersript
#	[x]	==xxx==		escaping (multi-line)
#	[x]	@xxx@			inline code
#
# paragraphs
#	[ ]	IPS?.		switch to paragraph I (p default)
#	[ ]	IPS?..		multiline paragraph
#	[x]	p (default)
#	[x]	bq -- blockquote,
#	[ ]	bc -- block of code, 
#	[x]	hi -- header level i, 
#	[ ]	clear
#	[ ]	dl
#	[ ]	table -- table definition
#	[ ]	fn
#
# Lists
#	[x]	PS?*+		bulleted list
#	[x]	PS?#+		numbered list
#	[ ]	PS?#n		numbered list starting at n (HTML OL.START deprecated?)
#	[ ]	PS?#_		continued list (HTML OL.START deprecated; does it mean junction with previous list ?)
#	[x]	PS?(+|#)*	melted list
#	[x]	PS?; TERM \n; DEFINITION	definition list
#	[x]	PS?- TERM := DEFINITION	definition list
#
# Tables
#	table style (TaS) includes
#		PS
#		_	header
#		\i	column span
#		/i	row span
#	[ ]	tablePS?.
#	[ ]	TaS?|TaS?_. ... |TaS?_. ... |	header
#	[ ]	TaS?|TaS? ... |TaS? ... |		row
#
# Notes
#	[ ]	[i]			foot note reference
#	[ ]	fni. ...	foot note definition
#	[ ]	[#R]		foot note reference
#	[ ]	note#R. ...	foot note definition
#
# Links
#	[ ]	"(CSS)?...(tooltip)?":U		link to URL U
#	[ ]	'(CSS)?...(tooltip)?':U		link to URL U
#	[ ]	["(CSS)?...(tooltip)?":U]	link to URL U
#	[ ]	[...]U						alternate form
#
# Images
#	[x]	!PS?U!			Image whose URL is U.
#	[x]	!PS?U WxH!		Image with dimension (support percents / initial width, height).
#	[x]	!PS?U Ww Hh!	Image with dimension.
#	[ ]	!PS?U n%!		Percentage on w and h.
#	[x]	!PS?U (...)!	Alternate text.
#
# Meta-characters
#	[x]	(c), (r), (tm), {c|}, {|c} cent, {L-}, {-L} pound,
#		{Y=}, {=Y} yen 

import tparser
import doc
import re
import highlight
import common

SPEC_MAP = {
	'(c)' : 0x00a9,
	'(r)' : 0x00ae,
	'(tm)': 0x2122,
	'{c|}': 0x00a2,
	'{|c}': 0x00a2,
	'{L-}': 0x00a3,
	'{-L}': 0x00a3,
	'{Y=}': 0x00a5,
	'{=Y}': 0x00a5
}
SPEC_RE = ""
for k in SPEC_MAP.keys():
	if SPEC_RE <> "":
		SPEC_RE = SPEC_RE + "|"
	SPEC_RE = SPEC_RE + common.escape_re(k)


class BlockQuote(doc.Par):

	def __init__(self):
		doc.Par.__init__(self)

	def dumpHead(self, tab):
		print "%stextile.blockquote(" % tab

	def gen(self, gen):
		gen.genEmbeddedBegin(self)
		type = gen.getType()
		if type == 'html':
			gen.genVerbatim('<blockquote>\n')
			doc.Container.gen(self, gen)
			gen.genVerbatim('</blockquote>\n')
		elif type == 'latex':
			gen.genVerbatim('\\subparagraph{}\n')
			doc.Container.gen(self, gen)
		elif type == 'docbook':
			gen.genVerbatim('<blockquote>\n')
			doc.Container.gen(self, gen)
			gen.genVerbatim('</blockquote>\n')
		else:
			common.onWarning('%s back-end is not supported by file block' % type)
		gen.genEmbeddedEnd(self)


class MyDefList(doc.DefList):
	on_term = True

	def __init__(self, depth):
		doc.DefList.__init__(self, depth)

	def onEvent(self, man, event):
		if event.id is doc.ID_NEW_DEF:
			if self.on_term:
				man.push(self.last().last())
			else:
				doc.DefList.onEvent(self, man, event)
			self.on_term = not self.on_term
		else:
			doc.DefList.onEvent(self, man, event)


class MyDefEvent(doc.DefEvent):
	
	def __init__(self, id, depth):
		doc.DefEvent.__init__(self, id, depth)
	
	def make(self):
		return MyDefList(self.depth)
	

def new_style(man, match, style, id):
	man.send(doc.StyleEvent(style))
	tparser.handleText(man, match.group(id), '')
	man.send(doc.StyleEvent(style))

def new_style(man, match, style, id):
	if style:
		man.send(doc.StyleEvent(style))
	tparser.handleText(man, match.group(id), '')
	if style:
		man.send(doc.StyleEvent(style))

def new_escape(man, match):
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, doc.Word(match.group('esc'))))

def new_image(man, match):
	image = match.group('image')
	w = None
	h = None
	alt = None
	if match.group('wxh'):
		l = match.group('wxh').lower().split('x')
		w = int(l[0])
		h = int(l[1])
	elif match.group('w'):
		w = int(match.group('w'))
		h = int(match.group('h'))
	if match.group('alt'):
		alt = match.group('alt')[1:-1]
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_NEW,
		doc.EmbeddedImage(image, w, h, alt, None)))

def new_spec(man, match):
	glyph = doc.Glyph(SPEC_MAP[match.group(0)])
	man.send(doc.ObjectEvent(doc.L_WORD, doc.ID_NEW, glyph))

	
WORDS = [
	(lambda man, match: new_style(man, match, doc.STYLE_BOLD, "t1"),
		'\*\*(?P<t1>\S([^*]|\*[^*])*\S)\*\*'),
	(lambda man, match: new_style(man, match, doc.STYLE_STRONG, "t2"),
		'\*(?P<t2>\S([^*]*)*\S)\*'),
	(lambda man, match: new_style(man, match, doc.STYLE_ITALIC, "t3"),
		'__(?P<t3>\S([^_]|_[^_])*\S)__'),
	(lambda man, match: new_style(man, match, doc.STYLE_EMPHASIZED, "t4"),
	 	'_(?P<t4>\S[^_]*\S)_'),
	(lambda man, match: new_style(man, match, doc.STYLE_SMALLER, "t5"),
	 	'--(?P<t5>\S([^-]|-[^-])*\S)--'),
	(lambda man, match: new_style(man, match, doc.STYLE_STRIKE, "t6"),
		'-(?P<t6>\S[^-]*\S)-'),
	(lambda man, match: new_style(man, match, doc.STYLE_BIGGER, "t7"),
	 	'\+\+(?P<t7>\S([^+]|\+[^+])*\S)\+\+'),
	(lambda man, match: new_style(man, match, doc.STYLE_UNDERLINE, "t8"),
	 	'\+(?P<t8>\S[^+]*\S)\+'),
	(lambda man, match: new_style(man, match, doc.STYLE_SUBSCRIPT, "t9"),
	 	'~(?P<t9>\S[^~]*\S)~'),
	(lambda man, match: new_style(man, match, doc.STYLE_CITE, "t10"),
	 	'\?\?(?P<t10>\S([^?]|\?[^?])*\S)\?\?'),
	(lambda man, match: new_style(man, match, doc.STYLE_SUPERSCRIPT, "t11"),
	 	'\^(?P<t11>\S[^^]*\S)\^'),
	(lambda man, match: new_style(man, match, doc.STYLE_CODE, "t12"),
	 	'@(?P<t12>\S[^@]*\S)@'),
	(lambda man, match: new_style(man, match, None, "t13"),
	 	'%(?P<t13>\S[^%]*\S)%'),
	(new_escape,
		'==(?P<esc>\S([^=]|=[^=])*\S)=='),
	(new_image,
		'!(?P<image>[^!\s(]*)(\s+((?P<wxh>[0-9]+[xX][0-9]+)|((?P<w>[0-9]+)w\s+(?P<h>[0-9]+)h)))?(?P<alt>\([^)]*\))?!'),
	(new_spec, SPEC_RE)
]

def new_header(man, match):
	level = int(match.group(1))
	title = match.group(2)
	man.send(doc.ObjectEvent(doc.L_HEAD, doc.ID_NEW, doc.Header(level)))
	tparser.handleText(man, title)
	man.send(doc.Event(doc.L_HEAD, doc.ID_TITLE))

def new_par(man, match):
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, doc.Par()))

def new_par_ext(man, match):
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, doc.Par()))
	tparser.handleText(man, match.group(1))

def new_single_blockquote(man, match):
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, BlockQuote()))
	tparser.handleText(man, match.group(1))
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, doc.Par()))

def new_multi_blockquote(man, match):
	man.send(doc.ObjectEvent(doc.L_PAR, doc.ID_END, BlockQuote()))
	tparser.handleText(man, match.group(1))

def new_list_item(man, match):
	pref = match.group(1)
	if pref[-1] == '*':
		kind = doc.LIST_ITEM
	elif pref[-1] == '#':
		kind = doc.LIST_NUMBER
	depth = len(pref)
	man.send(doc.ItemEvent(kind, depth))
	tparser.handleText(man, match.group(2))

def new_definition(man, match):
	man.send(doc.DefEvent(doc.ID_NEW_DEF, 0))
	tparser.handleText(man, match.group(1), '')
	man.send(doc.DefEvent(doc.ID_END_TERM, 0))
	tparser.handleText(man, match.group(3), '')

def new_multi_def(man, match):
	man.send(MyDefEvent(doc.ID_NEW_DEF, 1))
	tparser.handleText(man, match.group(1), '')


LINES = [
	(new_par, re.compile("^$")),
	(new_header, re.compile("^h([1-6])\.(.*)")),
	(new_par_ext, re.compile("^p\.(.*)")),
	(new_multi_blockquote, re.compile("^bq\.\.(.*)")),
	(new_single_blockquote, re.compile("^bq\.(.*)")),
	(new_list_item, re.compile("^([#\*]+)(.*)")),
	(new_definition, re.compile("^-(([^:]|:[^=])*):=(.*)")),
	(new_multi_def, re.compile("^;(.*)"))
]

def init(man):
	man.setSyntax(LINES, WORDS)
