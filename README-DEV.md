# Developer README

## Directory organization

  * `data` -- not installed data,
  * `doc` -- documentation,
  * `test` -- testing scripts and examples,
  * `thot` -- Thot module,
  * `thot/data` -- installed data,
  * `thot/mods` -- usable modules,
  * `thot/backs` -- backends,
  * `thot/langs` -- language modules,
  * `slidy` -- to remove,
  * `exp` -- to remove.


## Testing

To avoid conflict with installed version, define the PYTHONPATH to the
top directory :

```
$ export PYTHONPATH=$PWD:$PYTHONPATH
```

## Documentation

Read it from an HTTP local server:
```
$ pydoc3 -b
```

## Adding module

Just add `.py` in `thot/mods`.

Put data in `thot/data` and complete `MANIFEST.in`.
