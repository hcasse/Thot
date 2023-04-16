# View Tool

`thot-view` or `python3 -m thot.view` allows to read and navigate through a set of documents in different from your prefered browser.

You have just to invoke `thot-view` on one of the document composing the set and, assuming that the document is linked together, you can access any of the document and the corresponding HTML page is automatically generated in your browser.


## Wiki language

**THOT** supports several wiki languages but one has to include the module corresponding to the used language document with a syntax like:

	```
	@use WIKI-MODULE
	```

If this approach still works with `.thot` files, `thot-view` is able to use the right wiki-language module automatically from the extension of the processed file:

| Extension | Wiki-language |
|-----------|---------------|
| .md       | markdown      |
| .doku     | dokuwiki      |
| .textile  | textile       |


## Links in the document set

Links in the document set (other document or images) are processed in a special way:

  * If they are absolute or targetting the web, they are processed as-is and clicking on them will drive out of the document set.

  * Relative links are computed relatively to the document they belong to (as for HTML link).

**Example**

	```
		Link to external Markdown Guide:
		[Markdown Guide](https://www.markdownguide.org/)

		Image in the same directory as the current file:
		![My Image](image.png)
	```


## Configuration file

The documentation may be as a bunch of Markdown files in different directories. Accessing directly any file using `thot-view` is ok but the generated URL may be not very friendly. To prevent this, one declare a file named  `config.thot` in the top-level directory of the documentation. `thot-view` will automatically look for such a file traversing back the directories containing the accessed document until finding `thot-view` and all generated URL will be relative to this directory.

In addition, you can pass in `config.thot` declarations that will be shared by all pages of the documentation set as in the example below:

	```
	@TITLE=documentation title
	@AUTHOR=...
	@ICON=@(THOT_BASE_DIR)/icon.png

	@use markdown
	```

The definitions provided here are available to all document files. Basically the following definition may be useful but more relative to your documentation may be added:

  * `TITLE` -- the first header found in a file as taken as the title of the page but a global title can be passed  by this variable.
  * `AUTHOR` -- authors of the set of pages.
  * `ICON` -- icon displayed on each page.

In addition, we can use this file to avoid to repeat the use of some modules widely employed. In the example above, the `markdown` module is automatically used for each page.


## Styles

`thot-view` comes with a default style to display the HTML but you can use a different either from **Thot**'s style collection or your own style.

To use a **Thot**'s style named XXX, invoke `thot-view` with:

	$ thot-view -s XXX FILE

User styles must be `.css` files and the corresponding path must be passed to `-s` option:

	$ thot-view -s XXX.css FILE

To list the available styles in **Thot**'s collection, type the command:

	$ thot-view --list-styles

The styles used by `thot-view` have the same organization as the [ones used by **Thot**](../extend/styles.md).


