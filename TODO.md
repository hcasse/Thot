# Improvement to Thot

## Commands

	[ ] Add a --clean option to clean generated files.
	[x] Allow thot-view to automatically open `index.EXT`.
	[x] Add ``thot-view`` command.
	[x] Add ``thot-gen`` command.  
	[x] Add ANSI colorization.
	[o] Remove ``thot.py`` command.  


## Core

	[ ] Add a console text back-end
	[ ] Add a PDF back-end
	[ ] Replace use of TT by CODE.
	[ ] Create a module `mathjax`.
	[ ] Support for language local to a part of text.
	[ ] Add more standard paragraph types (like blockquote, file, verse, etc).
	[ ] Add inclusion from shell with syntax like @{command line}.
	[ ] Proposes alternatives to ``highlight``.
 	[ ] Use monitor every to produce errors.
	[ ] Highlight Python native solution if available (https://pygments.org/).
	[ ] Use console throughout the code.
	[ ] Make code non-interruptive except if very fatal case.
	[x] Share the parser extension list ( `thot.view` ) with other modules in `thot.tparser`.
	[x] Rewrite the dump system to support streams.
	[x] Add option ``-u``/``--use`` __module__ -- to select externaly a module (like a front-end).


## Front-Ends

  [ ] Accept to output reference to label for textual form (title, Section, etc).
  [ ] Support of reStructuredText: http://docutils.sourceforge.net/rst.html.
  [X] Support Textile.
  [X] Support for Markdown.


### Markdown

Basic : [Source](https://www.markdownguide.org/basic-syntax/)
	[x] `" "{2,}` for line break
	[x] `***|___` bold and italic
	[x] `>` blockquote
	[ ] `>` blockquote with other content
	[ ] indented sub-content to list (4 space = 1 tab)
	[x] `[...](URL "comment")` link with tooltip
	[x] `<URL>` quick link
	[x] `<email>` fast email link
	[x] Automatic link support the different forms.

Advanced: [Source](https://www.markdownguide.org/extended-syntax/)
	[x] Support image link.
	[x] Support tables.
	[x] Support code with language.
	[ ] Support for footnotes.
	[ ] Support for header label.
	[ ] Support for header reference.
	[x] Support for definition list.
	[ ] Support multiple definitions for definition list.
	[x] `~~...~~` Support for strike-through.
	[ ] Support for task list.
	[x] Emoji support.
	[x] Support for ==highlight==.
	[x] Support for ~subscript~.
	[x] Support for ^superscript^.


### DokuWiki

  [ ] ``:::`` in table for vertical spanning.
  [ ] Use of internal links [[...]] for inetr-document linking.
  [ ] Support of InterWiki links.
  [ ] Support for "~~NOTOC~~"
  [ ] Support for "wiki:" protocol.
  [ ] ``<html>`` ... ``</html>`` -- HTML embedding (``<php>`` ... ``</ph>`` -- currently, no meaning).

## HTML Backend

	[ ] Provide standard HTML generator (jinja, mako).
	[ ] Provide static website generator solution.


## Modules

### latexmath

	[ ] Use latex2mathml library directly.
	[ ] Look for availibility of latex2mathml and make it the default.


### PlantUML

	[ ] fix the localisation of the JAR.


## Attic

### SCORM

Obsolete standard (it seems).

### Slidy

Simply not working.
