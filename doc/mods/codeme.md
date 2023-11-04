# Codeme Module

@use codeme

This module allows to embed coding and testing in pages. It is first intended to teach programming and to embed testing in course page to avoid a break between the course and the experimentation.

## Example

Below is an example is an example of its work. First running the interpreter of Python:
<codeme interpreter=python3>
print("Hello, World!")
</codeme>

<codeme interpreter=python3>
def make(n):
	return [i for i in range(0, n)]
@@test:
print(make(3))
@@expected:
[0, 1, 2]
@@test:
print(make(0))
@@expected:
[0]
</codeme>

The example below is provided with the text:
	```xml
	<codeme interpreter=python3>
	print("Hello, World!")
	</codeme>

	<codeme interpreter=python3>
	def make(n):
		return [i for i in range(0, n)]
	@@test:
	print(make(3))
	@@expected:
	[0, 1, 2]
	@@test:
	print(make(0))
	@@expected:
	[0]
	</codeme>
	```

## Syntax
This module provides basically 2 syntaxes:

	```
	<codeme OPTIONS> CONTENT </codeme>
	<codeme-set OPTIONS>
	```

The first one provides an interactive way, on display supportting it like `thot-view`, to type code, ton run them and to display the result. The second command allows to defines options that will be used by subsequence `<codeme>` commands.

The _CONTENT_ is structured as follows:

	```
	<init>
	(@@test: \n <test-code> (@@expected: \n <expected code>))*
	```

The _<init>_ content is inserted as ann initial content in the text area where the reader has to type its code. This code content will be send to the interpreter.

Following _test_ code can be used to perform different tests with or without  an expected value. Basically, the run code for a test is the concatenation of the _initial content code_ and of the _code test_. If an _expected code_ is provided, the test is run and compared to the _expected code_ causing a test success or fail if there are equal or not. Different options allows to manage the tested output to reduce typing work or improve the reader display.

The following options are available:
* `language=` _LANGUAGE_ -  only for code colorization (not supported for now).
* `interpreter=` _COMMAND_ - interpreter path to run the program.
* `norm-spaces` -- normalize spaces (remove head/tail spaces, replace several spaces by 1),
* `timeout=` _SECONDS_ - number of seconds to time-out the command (4s as default),
* `skip=` _NUMBER_ - number of lines to skip at the beginning of the output,
* `skiplast=` _NUMBER_ - number of lines to skip at the end of the output,
* `cols=` _NUMBER_ - number of columns for the code display,
* `rows=` _NUMBER_ - number of rows for the code display,
* `testrows=` _NUMBER_ - number of rows for the test display.

