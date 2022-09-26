'''
precedence:
    application
    abstraction
    expression

association:
    application:
        left
    abstraction:
        right

testcase:
"\\x.x \\y.y" == {
    type: abstraction,
    param: Var(0),
    body: {
        type: application,
        abstraction: Var(0),
        argument: {
            type: abstraction,
            param: Var(1),
            body: {
                type: expression,
                body: Var(1)
            }
        }
    }
}
'''

from . import lambex
import enum

def objify_node(root):
    if not root:
        return {}
    
    if isinstance(root, str):
        return root

    return {
        "type": root.node_type.name,
        **{k:objify_node(v) if isinstance(v, LamNode) else v.value for k,v in root.values.items()}
    }

class NODES(enum.Enum):
    L_ABSTRACTION = enum.auto()
    L_APPLICATION = enum.auto()
    L_VARIABLE    = enum.auto()

class LamNode:
    def __init__(self, node_type, **kw):
        self.node_type = node_type
        self.values = kw
    
    def reconstruct(self):
        if self.node_type == NODES.L_ABSTRACTION:
            return "λ%s.%s" % (self.values["argument"].reconstruct(), self.values["body"].reconstruct())
        elif self.node_type == NODES.L_APPLICATION:
            return "(%s) %s" % (self.values["abstraction"].reconstruct(), self.values["parameter"].reconstruct())
        elif self.node_type == NODES.L_VARIABLE:
            return self.values["name"].value

    def __getitem__(self, key):
        return self.values[key]
    
    def __setitem__(self, key, value):
        self.values[key] = value

    def append(self, **kw):
        for k, v in kw.items():
            self.values[k] = v
    
    def __eq__(self, other):
        if not isinstance(other, LamNode):
            return False
        return self.node_type == other.node_type and self.values == other.values

    def __repr__(self):
        return self.reconstruct()

class ParseException(Exception):
    ...

class LamPar:
    def __init__(self, program):
        self.lamb = lambex.LambEx(program)
        self.number_of_abstractions = 0
        self.allow_anonymous_abstractions = True
    
    def assert_same_type(self, token, expect):
        if token.token_type != expect:
            pos = repr(self.lamb.get_position())

            raise ParseException("Expected a Lambda abstraction token \"%s\", got \"%s\" at (position, line, column): %s" % (lambex.TOKENS.get_charset(expect), token.value, pos))

    def next_token_of_type(self, expect):
        token = self.lamb.next_token()

        self.assert_same_type(token, expect)
        return token

    def next_token_is_type(self, expect):
        try:
            token = self.lamb.peek_token()
        except:
            return False
        
        return token.token_type == expect

    def parse_abstraction(self):
        '''
        anonymous_abstraction = lambex.TOKENS.T_LAMB expression
        abstraction = lambex.TOKENS.T_LAMB lambex.TOKENS.T_VAR lambex.TOKENS.T_OP expression
                    | anonymous_abstraction if allow_anonymous_abstractions
        '''

        if not self.next_token_is_type(lambex.TOKENS.T_LAMB):
            return False
        
        startpos = self.lamb.get_position()

        self.next_token_of_type(lambex.TOKENS.T_LAMB)

        self.number_of_abstractions += 1

        next_token_is_var = self.next_token_is_type(lambex.TOKENS.T_VAR)
        has_two_more_tokens = self.lamb.has_n_tokens_available(2)
    
        if not has_two_more_tokens:
            second_token_is_op = False
        else:
            second_token_is_op = self.lamb.peek_token(2).token_type == lambex.TOKENS.T_OP

        if not (next_token_is_var and second_token_is_op):
            if not second_token_is_op and self.allow_anonymous_abstractions:
                return LamNode(NODES.L_ABSTRACTION, argument=LamNode(NODES.L_VARIABLE, name=lambex.Token(lambex.TOKENS.T_VAR, f"α{self.number_of_abstractions}")), body=self.parse_expression())
            if not next_token_is_var:
                raise ParseException("Expected a variable at position %s, recieved \"%s\"" % (repr(self.lamb.get_position()), self.lamb.peek_token().token_type.name))
            raise ParseException("Anonymous abstractions are not allowed, encountered anonymous abstraction at position %s." % repr(self.lamb.get_position()))

        var = self.next_token_of_type(lambex.TOKENS.T_VAR)

        if not second_token_is_op:
            raise ParseException("Expected token \".\" at %s, recieved \"%s\"" % (repr(self.lamb.get_position(), self.lamb.peek_token().token_type.name)))
        
        self.next_token_of_type(lambex.TOKENS.T_OP)

        return LamNode(NODES.L_ABSTRACTION, argument=LamNode(NODES.L_VARIABLE, name=var), body=self.parse_expression())

    def parse_grouped_expression(self):
        '''
        expression = '(' expression ')'
        '''

        if not self.next_token_is_type(lambex.TOKENS.T_PUNC):
            return False

        startpos = self.lamb.get_position()
        
        if self.lamb.next_token().value != "(":
            return False

        expr = self.parse_expression()

        if not self.next_token_is_type(lambex.TOKENS.T_PUNC):
            raise ParseException("Tried to parse grouped expression starting at %s, missing end parenthesis." % repr(startpos))

        if (token := self.lamb.next_token()).value != ")":
            raise ParseException("Recieved \"%s\" at %s, expected \")\"" % (token.value, self.lamb.get_position()))

        return expr
    
    def parse_variable(self):
        '''
        expression = lambex.TOKENS.T_VAR
        '''

        if not self.next_token_is_type(lambex.TOKENS.T_VAR) and not self.next_token_is_type(lambex.TOKENS.T_NUM):
            raise ParseException("Expected a variable or number at position %s, got \"%s\"" % (repr(self.lamb.get_position()), self.lamb.next_token().token_type))

        return LamNode(NODES.L_VARIABLE, name=self.lamb.next_token())

    def parse_application(self, abstraction):
        '''
        application = abstraction expression
        '''

        return LamNode(NODES.L_APPLICATION, abstraction=abstraction, parameter=self.parse_expression(is_abstraction=True))
    
    def parse_expression(self, is_abstraction=False):
        '''
        expression := lambex.TOKENS.T_PUNC expression lambex.TOKENS.T_PUNC
                    | abstraction
                    | application
                    | lambex.TOKENS.T_VAR
        '''

        expression = None

        if (expr := self.parse_grouped_expression()):
            expression = expr
        elif (expr := self.parse_abstraction()):
            expression = expr
        else:
            expression = self.parse_variable()

        if is_abstraction:
            return expression # left-assoc

        while self.lamb.has_token() and self.lamb.peek_token().value != ")":
            expression = self.parse_application(expression)
        
        return expression
    
    def normalize_debruijn(self):
        '''
        λλλ 3 1 (2 1) -> λx0. λx1. λx2. x0 x2 (x1 x2)
        
        λ λ 1 (λ (λ 2 1 4) 1) -> λx0.λx1. x1 (λx2. (λx3. x2 x3 x0) x2) 

        Visit each anonymous lambda, insert "x[lambda-number]."
        Visit each number, swap with "x[lambda-number for reverse lambda depth]"        
        Unlex the normalized string to self.lamb
        '''
        pass

    
    def parse(self, allow_anonymous_abstractions=True):
        if not allow_anonymous_abstractions:
            self.allow_anonymous_abstractions = False
        
        try:
            return self.parse_expression()
        except ParseException as pe:
            print("Recieved ParseException: %s" % pe)
        except lambex.LexException as le:
            print("Lexer recieved exception: %s" % le)
        except EOFError as pe:
            print("Recieved EOF while parsing, %s" % pe)

if __name__ == "__main__":
    import json

    def test_LambEx_simple():
        p = LamPar("\\x.\\y. x")
        root = p.parse_expression()
        o = objify_node(root)

        assert o == {'type': 'L_ABSTRACTION', 'argument': {'type': 'L_VARIABLE', 'name': 'x'}, 'body': {'type': 'L_ABSTRACTION', 'argument': {'type': 'L_VARIABLE', 'name': 'y'}, 'body': {'type': 'L_VARIABLE', 'name': 'x'}}}

        #print(json.dumps(o, indent=4))
        print("\\x.\\y. x", ":", root.reconstruct())

        return True

    def test_LambEx_application_assoc():
        p = LamPar("(\\x. x y z) 4 5 6")
        root = p.parse_expression()
        o = objify_node(root)

        assert o == {'type': 'L_APPLICATION', 'abstraction': {'type': 'L_APPLICATION', 'abstraction': {'type': 'L_APPLICATION', 'abstraction': {'type': 'L_ABSTRACTION', 'argument': {'type': 'L_VARIABLE', 'name': 'x'}, 'body': {'type': 'L_APPLICATION', 'abstraction': {'type': 'L_APPLICATION', 'abstraction': {'type': 'L_VARIABLE', 'name': 'x'}, 'parameter': {'type': 'L_VARIABLE', 'name': 'y'}}, 'parameter': {'type': 'L_VARIABLE', 'name': 'z'}}}, 'parameter': {'type': 'L_VARIABLE', 'name': '4'}}, 'parameter': {'type': 'L_VARIABLE', 'name': '5'}}, 'parameter': {'type': 'L_VARIABLE', 'name': '6'}}

        print("(\\x. x y z) 4 5 6", ":", root.reconstruct())

        return True

    def test_LambEx_testcase():
        p = LamPar("λx . x\tλy. y\r\n")

        root = p.parse_expression()
        o = objify_node(root)

        print("λx.x λy.y", ":", root.reconstruct())

        return True

    print(test_LambEx_simple() and test_LambEx_application_assoc() and test_LambEx_testcase())