# Thot V0.1

Thot is a document generator taking as input a textual document
expressed in a wiki-like language (currently dokuwiki syntax is
supported but more will be added) and produces as output a nice
displayable document (HTML, Latex, PDF, etc). The main concept is to
make document-making as less painful as possible while unleashing
powerful textual dialect: the basic wiki syntax may be improved by
augmenting the syntax thanks to external modules.

Thot is delivered under the license GPL v2 delivered in the [COPYING.md](file:COPYING.md) file.


## Installation

To install Thot, unpack the archive containing it and type:
```
	$ PYTHON ./setup.py install [--user]
```
With `PYTHON` your command to invoke Python V3 and `--user` optional to install Thot locally.

Notice that the `PYTHON` command is optional on OSes supporting script invocation in the first line.


## Development

For developing Thot, use instead the command below:
```
	$ PYTHON ./setup.py develop --user
```

To perform testing,
```
	$ PYTHON ./test/test.py
```

Test items can be invoked individually. To get their list:
```
	$ PYTHON ./test/test.py -l
```


## Help

For any problem, you can contact me to [hug.casse@gmail.com](mailto:hug.casse@gmail.com).
