# MarkDown

MarkDown is currently, maybe, the most used wiki-like syntax.
Our implementation is based on [https://www.markdownguide.org/](https://www.markdownguide.org/) and covers 90% of the syntax (including extended syntax).
Remaining 10% will be quickly implemented in the future.

Below is an overview of the MarkDown syntax but you refer to [https://www.markdownguide.org/](https://www.markdownguide.org/) for more details.

```
# Heading level 1
## Heading level 2

Paragraph 1

Paragraph 2

Line<br>
break!

**bold text** or __bold text__

*italic text* or _italic text_

`code text`

~~strike-through text~~

==highlight text==


> quoted paragraph

1. Ordered list.
2. And next.

* Unordered list.
* And next.

	Code block
	block next

\```language
Other code block.
\```

![alternate image text](image URL)

Horizontal rules :
***
---
________

[link text](URL)

\c escape character _c_ from interpretation.


Table:
| Header 1 | Header 2 |
| -------- | -------- |
| Content 1 | Content 2 |

Definition lists:

Term 1
: Definition 1

Term 2
: Definition 2

Emoji's: :joy:
```

Emoji's identifier are taken from [https://gist.github.com/rxaviers/7360908](https://gist.github.com/rxaviers/7360908) .


