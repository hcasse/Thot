
@use codeme

Make `Hello World!` to be printed:
<codeme language=ocaml,interpreter=ocaml>
</codeme>


Write a recursive function that computes recursively the sum of the 10 first integer starting from 0.
<codeme language=ocaml,interpreter=ocaml,skip=3,skiplast=2>
let f n =
;;
@@test:
f 0;;
@@expected:
# - : int = 0
@@test:
f 2;;
@@expected:
# - : int = 3
@@test:
f (-1);;
</codeme>

Two definitions: a = 0, b = 1 :
<codeme language=ocaml,interpreter=ocaml,skip=2,skiplast=2>

let a = 0;;
let b = 1;;
@@test:
@@expected:
#   val a : int = 0
# val b : int = 1
</codeme>


Without `set`, option test:
<codeme language=ocaml,interpreter=ocaml>
print_string "Hello, World!";;
</codeme>

<codeme-set rows=2,testrows=10,interpreter=ocaml>

With `set`, option test:
<codeme>
print_string "Hello, World!";;
</codeme>

And another one:
With `set`, option test:
<codeme>
print_string "Ciao!";;
</codeme>
