@TITLE=Markdown test
@AUTHORS=H. Cassé <hugues.casse@laposte.net>
@VERSION=0.1
@LANG=en_EN

First paragraph.

Second paragraph.

Level 1 header
==============


Text in header.

Subsection 1
------------

Text in subsection 1.

Subsection 2
------------

Text in subsection 2.

# Level 1 header with ##

Text in section 2.

## Level 2 header with ##

Test in level 2.

## Level 2 header with ##

Test in level 2.

# Lists

## Unumbered

Now an item list:
* item 1
* item 2
* item 3
+ item 4
- item 5

## Numbered

And a numbered list:
0. item 1
1. number 2
33. number 3

## Embedded

1. item 1
2. item 2
	1. sub-item 1
	2. sub-item 2
3. item 3


# Bars

Now, 5 horizontal rules:

***
*****
* * *
- - -

------------

# Word-leval Syntax

This is a link to [Google](http://www.google.fr).

This is *emphasis* and _emphasis_.

And **strong** and __strong__.

And ***strong emphasis*** here.

Protected \* and \_.

This is `code`. And with ``back`trick``.

This is ~~~strike-through~~~.

This is ==highlight==.

Subscript: H~2~O water !

Superscript: x^2^


# Links

This is an automatic link <http://www.google.fr>.

This is an automatic email address: <me@here.somewhere>.

This is a [reference link] [google].

[google]: http://www.google.fr	'This is Google!'

[a link](http://www.gnu.com)

[1]: http://gcc.gnu.org

A [backward link][1] here !

A [forward link][2] now.

[2]: http://www.irit.fr

An [unknown][3] link.

A [link](https://www.gnu.org/ "This is GNU!") with title.


[h1]: https://en.wikipedia.org/wiki/Hobbit#Lifestyle
[h2]: https://en.wikipedia.org/wiki/Hobbit#Lifestyle "Hobbit lifestyles"
[h3]: https://en.wikipedia.org/wiki/Hobbit#Lifestyle 'Hobbit lifestyles'
[h4]: https://en.wikipedia.org/wiki/Hobbit#Lifestyle (Hobbit lifestyles)
[h5]: <https://en.wikipedia.org/wiki/Hobbit#Lifestyle> "Hobbit lifestyles"
[h6]: <https://en.wikipedia.org/wiki/Hobbit#Lifestyle> 'Hobbit lifestyles'
[h7]: <https://en.wikipedia.org/wiki/Hobbit#Lifestyle> (Hobbit lifestyles)

Combinations of links with titles:
1. [hobbit][h1]
1. [hobbit][h2]
1. [hobbit][h3]
1. [hobbit][h4]
1. [hobbit][h5]
1. [hobbit][h6]


# Code colorization

```c++
/* my first code */

// single line

#include <stdio.h>

#define A 0
#ifdef A
#	define B 1
#endif

#ifdef C
int coucou;
#endif

class C {
	C() {}
	~C() {};
	int operator*() { return 0; }
};

static int y;

/**
 * my main
 * @param x
 */
int main(int x) {
	int t[10];
	int x = 0;
	printf("Hello, World!\n");
	if(x < 3)
		x = 0;
	while(x != 0.1)
		x--;
	x = 'a';
}
```


# Special paragraph

> Single quote.
> Next line
>
> Another quote paragraph.

> level 1
>> level 2
>>> level 3
> level 1


# Emoji's

This is a smile :smile:!

And a skull :skull:.

And a non-existing emoji :coucou:.



# Tables

| Syntax | Description |
| --- | ----------- |
| Header | Title |
| Paragraph | Text |



| Syntax      | Description | Test Text     |
| :---        |    :----:   |          ---: |
| Header      | Title       | Here's this   |
| Paragraph   | Text        | And more      |


# Definitions

First Term
: This is the definition of the first term.

Second Term
: This is one definition of the second term.
DEBUG: : This is another definition of the second term.

