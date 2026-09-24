PYLINT=pylint

export PYTHONPATH=$(PWD)

SOURCES = \
	thot/common.py

all:

check:
	$(PYLINT) thot | less

autodoc:
	gnome-terminal -- pydoc3 -b

type:
	mypy $(SOURCES)
