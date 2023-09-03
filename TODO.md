# Improvement to Thot

## Application

  [ ] Add ``thot-view`` command.
  [ ] Add ``thot-gen`` command.  
  [ ] Add a --clean option to clean generated filkes.
  [ ] Add ANSI colorization.
  [ ] Remove ``thot.py`` command.  

## Core

	[ ] Support for language local to a part of text.
	[ ] Add more standard paragraph types (like blockquote, file, verse, etc).
	[ ] Add inclusion from shell with syntax like @{command line}.
	[ ] Proposes alternatives to ``highlight``.
 	[ ] Use monitor every to produce errors.
	[ ] Share the parser extension list ( `thot.view` ) with other modules in `thot.tparser`.
	[ ] Highlight Python native solution if available (https://pygments.org/).
	[ ] Use console throughout the code.
	[ ] Make code non-interruptive except if very fatal case.
	[x] Add option ``-u``/``--use`` __module__ -- to select externaly a module (like a front-end).


## Front-Ends

  [ ] Accept to output reference to label for textual form (title, Section, etc).
  [ ] Support of reStructuredText: http://docutils.sourceforge.net/rst.html.
  [X] Support Textile.
  [X] Support for Markdown.


### Markdown

Basic : [Source](https://www.markdownguide.org/basic-syntax/)
	[ ] `" "{2,}` for linbe break
	[ ] `***|___` bold and italic
	[ ] `>` blockquote
	[ ] `>` blockquote with other content
	[ ] indented sub-content to list (4 space = 1 tab)
	[ ] `[...](URL "comment")` link with tooltip
	[ ] `<URL>` quick link
	[ ] `<email>` fast email link
	[ ] Automatic link support the different forms.

Advanced: [Source](https://www.markdownguide.org/extended-syntax/)
	[ ] Support image link.
	[ ] Support tables.
	[ ] Support code with language.
	[ ] Support for footnotes.
	[ ] Support for header label.
	[ ] Support for header reference.
	[ ] Support for definition list.
	[ ] `~~...~~` Support for strike-through.
	[ ] Support for task list.
	[ ] Emoji support.
	[ ] Support for ==highlight==.
	[ ] Support for ~subscript~.
	[ ] Support for ^superscript^.


### DokuWiki

  [ ] ``:::`` in table for vertical spanning.
  [ ] Use of internal links [[...]] for inetr-document linking.
  [ ] Support of InterWiki links.
  [ ] Support for "~~NOTOC~~"
  [ ] Support for "wiki:" protocol.
  [ ] ``<html>`` ... ``</html>`` -- HTML embedding (``<php>`` ... ``</ph>`` -- currently, no meaning).

## HTML Bakcend

	[ ] Provide standard HTML generator (jinja, mako).
	[ ] Provide static website generator solution.


## Modules

## Attic

### SCORM

Obsolete standard (it seems).
