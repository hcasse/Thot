PYLINT=pylint

export PYTHONPATH=$(PWD)

SOURCES = \
	thot/builtin.py \
	thot/common.py \
	thot/command.py \
	thot/doc.py \
	thot/tparser.py

all:

check:
	$(PYLINT) thot | less

autodoc:
	gnome-terminal -- pydoc3 -b

type:
	mypy $(SOURCES)
