from parsex import LamPar, LamNode, NODES
from lambex import TOKENS, Token
import random

variable_anonymous_counter = 0

'''
class LamNode:
    def __init__(self, node_type, **kw):
        self.node_type = node_type
        self.values = kw

LamNode(NODES.L_ABSTRACTION, argument=LamNode(NODES.L_VARIABLE, name=var), body=self.parse_expression())
LamNode(NODES.L_APPLICATION, abstraction=abstraction, parameter=self.parse_expression(is_abstraction=True))
LamNode(NODES.L_VARIABLE, name=self.lamb.next_token())
'''

def repeat_fx(f, x, n):
    serie = x
    
    while n:
        serie = f"{f} ({serie})"
        n -= 1
    
    return serie

def encode_church(num):
    global variable_anonymous_counter
    variable_anonymous_counter += 1
    return f"\\f{variable_anonymous_counter}.\\x{variable_anonymous_counter}." + repeat_fx(f"f{variable_anonymous_counter}", f"x{variable_anonymous_counter}", num)

def convert_church(root):
    if isinstance(root, Token):
        return root
    
    if root.node_type == NODES.L_VARIABLE and root.values["name"].token_type == TOKENS.T_NUM:
        return LamPar(encode_church(int(root.values["name"].value))).parse()
    
    return LamNode(root.node_type, **{k: convert_church(v) for k, v in root.values.items()})

class ReductionException(Exception):
    pass

def substitute_variable_name(tree, var, new_var):
    if not isinstance(tree, LamNode):
        return tree

    if tree.node_type == NODES.L_VARIABLE and tree.values["name"].value == var:
        return LamNode(tree.node_type, name=Token(TOKENS.T_VAR, new_var))

    node = LamNode(tree.node_type)

    for k, v in tree.values.items():
        node[k] = substitute_variable_name(v, var, new_var)

    return node

def alpha_conversion(tree):
    """
    convert naming by λx.M[x] -> λy.M[y] to avoid conflicts through de bruijn indexing.
    e.g. λλ.x1 would be equivalent to λx.λy.x.
    """

    if tree.node_type != NODES.L_ABSTRACTION:
        raise ReductionException("Expected an abstraction in alpha-conversion, recieved a %s." % tree.node_type.name)
    
    if "argument" not in tree.values:
        raise ReductionException("Expected abstraction to have an argument in alpha-conversion.")

    argument = tree.values["argument"]

    if argument.node_type != NODES.L_VARIABLE:
        raise ReductionException("Expected a variable as argument type to abstraction in alpha-conversion, recieved a %s." % argument.node_type.name)

    print(substitute_variable_name(tree, "x", "0").reconstruct())


def beta_reduction(tree):
    '''
    reduce applications, (λx.a) b -> a[x := b].
    a tree is beta-normal when no further beta-reduction can take place.
    '''
    pass

def is_beta_normal(tree):
    '''
    given a tree T, if beta-reduction applied on T = T, the tree is beta-normal.
    '''
    pass

if __name__ == "__main__":
    for i in range(5):
        print(encode_church(i))
    
    print(convert_church(LamPar("(λm.λn.m (λn.λf.λx.f (n f x)) n) 1 1").parse()).reconstruct())


    print("Testing alpha-conversion")
    alpha_conversion(LamPar("\\x.\\y.x").parse())
    
    print(LamPar("\\\\ x").parse())
    print(LamPar("λ λ 1 (λ (λ 2 1 4) 1 x)").parse().reconstruct())