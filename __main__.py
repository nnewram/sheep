import src.parsex as parsex
import src.tools as tools

if __name__ == "__main__":
    print(tools.beta_reduction(parsex.LamPar("(λx.x) y").parse()))