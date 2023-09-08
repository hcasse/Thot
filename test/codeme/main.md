
@use codeme

Make `Hello World!` to be printed:
<codeme language=ocaml,interpreter=ocaml>
</codeme>


Write a recursive function that computes recursively the sum of the 10 first integer starting from 0.
<codeme language=ocaml,interpreter=ocaml,skip=3>
let f n =
;;
@@test:
f 0;;
@@expected:
- : int = 0
@@test:
f 2;;
@@expected:
- : int = 3
</codeme>

