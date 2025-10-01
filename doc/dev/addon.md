# Add-on

In this part, we describe the different additional facilities that are provided by
the `thot.doc` classes that are used to improve the documents. These facilities
may match or not the syntaxes to describe the document.


## Generic Information

Each THOT supports a generic information system allowing to hook any information
in thrifty way. You have just to assign a string identifier to your data and
use the following function to manage it:

* `set_info`(//ID//, //data//) -- store the //data// with //ID// on the node,
* `get_info`(//ID//, //default//) -- retrieve data matching the //ID// or
	return the //default// value if it is not set.

`thot.doc` comes already with a collection identifiers prefixed by `INFO_`.


## Captions

Captions are added to any node supporting it with the notation below following
the node definition :

```
<some captionable contant>
@caption <text>
```

The following `<text>` is a common paragraph supporting word syntax.

The resulting paragraph is added to the topmost node supporting caption. Testing
and setting the caption is made with function `put_caption(text)` that returns
a boolean indicating if it supports or not the caption.

Supporting caption is as simple as returning True with this function and
recording the caption text. Basically `thot.doc.Block` supports caption. The
way the caption is then outputted depends on the actual nature of the node.

Caption can be easily and efficiently stored using `Node` functions `set_caption()`
and `get_caption()`  that uses in turn the _Generic Information_ system.


## Labels

Labels can hooked to headers and figures (images, listings, table, etc) that then
can referenced later (or event earlier) in the document. Labels are maintained
at the document level (in a dictionnary) for access any other point in the document
and on the node. A node may support several labels.

A label is usually declared with syntax:

```
@label label-name
```

The following functions can be used to manage labels:

* `Node.numbering()` get the numbering type supported by a a `Node`. Returns None
	if numbering is not supported and therefore cannot be referenced through
	a label.
* `Node.get_labels()` to get the list of labels on the node,
* `Document.add_label(label, node)` used to record a new label to a node,
* `Document.get_label(label)` to get the node associated with the label.

Then it can be referred with syntax

```
... @ref:label-name@ ...
```

The `@ref@` is, at generation time, replaced by a text designing the label
(in the locale of the document) and, when supported by the back-end, a link
to the actual node representation.






