PYLINT=pylint

export PYTHONPATH=$(PWD)

all:

check:
	$(PYLINT) thot | less

autodoc:
	gnome-terminal -- pydoc3 -b
