# Thot V2.0

**Thot** is a document generator taking as input a textual document expressed in a wiki-like language (currently `creole`, `dokuwiki`, `markdown`, `textile` are supported but more will be added) and produces as output a nice displayable document (HTML, Latex, PDF, DocBook). The main concept is to make document-making as less painful as possible while unleashing powerful textual dialect: the basic wiki syntax may be improved by augmenting the syntax thanks to external modules.

Thot is delivered under the license GPL v2 delivered in the [COPYING.md](file:COPYING.md) file.


## Installation

To install **Thot**, unpack the archive containing it and type:
```sh
	$ PYTHON -m install .
```

With `PYTHON` your command to invoke Python V3.

Notice that the `PYTHON` command is optional on OSes supporting script invocation in the first line.


## Using it

**Thot** comes with several applications to generate documents :
* `thot-gen` -- generates a document from a wiki document.
* `thot-view` -- opens the document in your browser and allows to navigate along the links.

Ton consult the documentation,
```sh
	$ ./thot-view.py doc
```
Notice that **Thot** does not need to be installed to look to the documentation.


## Modules

**Thot** comes with 3 wiki syntaxes but more will be added later:
* [creole](http://www.wikicreole.org/wiki/Home)
* [dokuwiki](https://www.dokuwiki.org/fr:wiki:syntax)
* [markdown](https://www.markdownguide.org/)
* [textile](https://textile-lang.com/)

**Thot** comes several modules providing different extension modules to generate the document :
* [aafig](https://pythonhosted.org/aafigure/index.html) -- AAFIG figure from text,
* `box` -- includes various boxes in your document,
* `codeme` -- teaching inclusion of programming and testing,
* [ditaa](https://ditaa.sourceforge.net/) -- another figure from text extension,
* [dot](https://graphviz.org/) -- GraphViz graph generation,
* [gnuplot](http://www.gnuplot.info/) -- GNUPlot diagrams,
* `latexmath` -- generate Math formula from Latex syntax,
* `lexicon` -- provides definition to hash-prefixed words,
* [plantuml](https://plantuml.com/fr/) -- UML diagrams from text description,
* `unicode` -- Unicode character insertion.

Finally, several back-ends are provided:
* [HTML](https://www.w3schools.com/html/default.asp)
* [Latex](https://fr.wikipedia.org/wiki/LaTeX)
* [DocBook](https://docbook.org/)
* [PDF](https://en.wikipedia.org/wiki/PDF) -- based on Latex output.


## Help

**Thot** makes explicit the syntax and the different extension forms:

	$ thot-gen --list-avail

displays the list of all extensions and back-ends.

	$ thot-gen DOCUMENT --list-syntax

displays the syntax available in the document according to the used modules.

New with this version of **Thot**, you do need any more to generate the documentation.
You can view it on-line with `thot-view` in your browser:

	$ thot-view any-document

For example, the documentation of **Thot** can be examined with:

	$ thot-view doc/index.md


For any problem, you can contact me to [hug.casse@gmail.com](mailto:hug.casse@gmail.com).
