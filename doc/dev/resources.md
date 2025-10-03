# Resources

In @THOT@, resources is the set of files used for building a document or are part
of the final resulting document (typically with HTML backend).


## Retrieving the resources

During parsing, different syntaxes have to retrive local or distant files,
sometimes relative to the processed file. The class `thot.tparser.Manager`,
passed as first parameter each a syntax is scanned, may help with:

* `fix_path(path)` -- in case of relative path, resolve it relatively to the
	parsed document.
* `fix_url(path)` -- same as above but takes into account also paths that are URLs.



## Creating resources

Sometimes, a new resources has to be generated, typically by an external generator,
and kept with the resulting document. This is one using class `thot.back.Manager`.




## Referencing resources


## HTML Managers


