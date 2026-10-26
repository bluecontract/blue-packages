# Features

Authored native Blue proposal package. See the top-level evidence and catalogue for tested scope. No JavaScript business interpreter.


Unpublished candidate. Authored Blue/BEX definitions are authoritative. See ../docs/payment-family.md for the tested package selection and integration boundaries.


## Typed action inputs

An action can declare `args` as ordinary Blue field constraints and `require` as
an explicit business precondition. The generated handler checks the argument
pattern and precondition before running either the connection's `before` hook
or the action body. Missing required values and incompatible types reject the
operation without effects.

The `Action Declaration` and `Action Parameters` types preserve schema identity
when all argument values are still unfilled. They are inherited by the action;
application authors do not add these type annotations themselves. The argument
pattern is compiled separately from executable BEX; executable expressions are
not permitted in the static schema.
