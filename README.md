# sheep
λ-calculus toolkit

## Usage
```py
from sheep import parsex

p = parsex.LamPar("λλλ 3 1 (2 1)")
parsed = p.parse()

print("λα1.λα2.λα3.((3 1) (2 1)) =", parsed)
```

## Reason
I made this project mainly because it's fun, but I hope it can be useful for other people as well.\
Currently working on "normalizing" de bruijn indexed anonymous abstractions, feel free to add more tools in tools.py.\
The end goal is to have an interactive graph-viewer for lambda expressions.
