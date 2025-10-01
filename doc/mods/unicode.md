# Unicode

@use unicode
<unicode>
0x25A1:|_|
9651:/\
∫:!int
</unicode>



`unicode` makes easier the use of [Unicode](https://fr.wikipedia.org/wiki/Unicode)
symbols by associating an Unicode character with a special sequence of characters.

In the example below, we associate the |_|, which hexadecimal code is `25A1`,
with the string that follows `:`. In the same, character /\ with decimal code
9651 is replaced by the following string. The unicode character can also be
written as is and associated with a character sequence.

```
<unicode>
0x25A1:|_|
9651:/\
∫:!int
</unicode>
```

So the following code:

```
A square here: |_|!

And two quares: |_||_|!

And a triangle: /\

!int (x + 1)dx
```

generates:

---
A square here: |_|!

And two quares: |_||_|!

And a triangle: /\

!int (x + 1)dx

---
