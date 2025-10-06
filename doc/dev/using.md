# Using Thot as a Library

@(THOT) comes with two tools, `thot-gen` and `thot-view`, using a front-end
to parse wiki-like syntax documents and generating the document in a different
user-friendly format. Yet, written in Python, it can used as a library for
partsing text document or to generate documents.

## Simple Use

Before any action, a document has to be created:

```python
from thot.doc import Document
env = {}
doc = Document(env)
```

_env_ is a list of definitions as if they were done in the document with the
syntax `@ID=VALUE`. These definitions can provide parameters to some used
modules.

After that, a parser manager has to be created:

```python
from thot.tparser import Manager
manager = Manager(doc)
```

Now, it can be used to parse file by name:
```python
manager.parse("mydoc.md")
```

Or as a stream:
```python
with open("mydoc" as input):
	manager.parse(input)
```

Additionally, you can also parse simple text:
```python
manager.parse_text("""
This is my first **markdown** text!

And another line!
""")
```

Any fatal error will be reported with exception `thot.common.ParseException`.
Another way to control the exchange of @(THOT) with interactive user is the monitor
passed to manager construction. It contains functions, `error()`, `info()`, `warn()`, etc
that are called by the parser manager:
```python
from thot.common import Monitor

class MyMonitor(Monitor):

	def error(self, msg):
		# transform any error into fatal error
		self.fatal(msg)

manager = Manager(MyMonitor())
```

Notice also that at this point, you can also enable modules from the manager.
For example, to load module `latexmath`for use in the document, you can write:
```python
manager.use("latexmath")
```

Or you can select your preferred wiki syntax:
```python
manager.use("markdown")
```

All _parse_ function calls accumulate in the _document_ all built structures.

Finally, you can output it by invoking a back-end:
```python
from thot import back
backend = back.get_back("html")
```

Now, you can create the generator, set the out path (if not with environment
variables) and run the generation:
```python
gen = backend.Generator()
gen.set_out_path("mydoc.html")
gen.run()
```

That's it!


## Working on the Document Representation

