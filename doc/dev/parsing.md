# Parsing

Parsing of the document is performed by classes in the module `tparser`.
Basically, the parsing process is handled by `tparser.Manager` that opens
the document, keep a trace of operations (for error output for example) and
call, in turn, the parsers that are able to scan the text, a kind of conductor.


## Raw text parsing

Basically, using the default parser provided by `tparser.DefaultParser`, the parsing
is performed in two levels:

1. The text is parsed line by line and each line is tested against __line REs__.
As soon as one RE scans the line (order is important here); the corresponding
handler handler (it is supposed to update the document) and the parsing passes
to the next line.

2. If no line RE applies, the line is split according to __word REs__.
Pieces of text that are not scanned are generated as `doc.Word` while
handlers of the word RE are called on  the scanned parts (and are also
suppose to update the document).


## Document update

The update of the document is performed using a system based on stack
(of the document nodes currently processed) and events that represents
the creation of new nodes.

All events extends the class `doc.Event` that provides the following information:

`id`
: identifier of the event (mainly for debugging purpose).

`level`
: document level at which the event applies

`make\_ext`(manager)
: function that creates a node at the point of insertion in the document.

Basically, the event is applied along the document stack using the function
`Manager.send`. In this case, the function `Node.onEvent`() of the top of the stack is called with the event.

This function can do what it wants with the event but a usual rule is that it passes up the event if the event level is higher than the node level (bubbling effect). This is performed with function `Manager.forward`()
that pops the current top object from the document stack.

If the node do not pass up the event, it can apply internally its effect
(often a call to `make\_ext`() is performed) and potentially update the
document stack with new nodes ready to get newt text content (function `Manager.push`()).

The reaction to event is fully managed in the `onEvent`() function and
therefore by the created nodes. In order to customize this behaviour,
one can provide its own implementation of the document classes by
extending `doc.Factory` class that, as said by its name, acts as n object
factory.

In this implementation, three additional function are used to build the document and may be useful to customize :

`is_empty`()
: Called by a container, test if the node is empty (typically a pargraph) in order to remove it from the document. This test is often performed before adding a new item to the container or when the container is popped.

`aggregate`()
: Called by a container just before adding a new item to let some items to  aggregate (like entries of lists, etc).

`complete`()
: Called before popping the top node of the current list.


## Structure of modules

Module allows to extend **THOT** and therefore provides new syntaxes and possibly new nodes. In order to provides these extension, the module Python file provides the following global variables:

`__factory__`
: Factory used to build nodes (if not available, uses the default factory).

`__lines__`
: List of triples (handler, RE, description) used to parse the lines. An handler takes as parameter the manager and the corresponding RE match object.

`__short__`
: Short description of the extension.

`__syntax__`
: If true, the extension represents a __whole syntax__ (markdown, etc) and not only a __simple syntax__ extension that add a few syntax items. Old whole syntax is removed and replaced by this one.

`__words__`
: List of triples (handler, RE, description) used to parse text at word level.
An handler takes as parameter the manager and the corresponding RE match object.

_Notice that word RE are aggregated together. As the uses of extensions makes hard to predict the group numbers in RE, a better solution, when groupes are used, is to name them._







