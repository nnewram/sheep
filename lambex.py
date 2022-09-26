'''
tokens:
    whitespace = ' \t\r\n'
    lamb = 'λ\\'
    num = r'\d+'
    var = r'[a-zA-Z]+[a-zA-Z0-9]*'
'''

import string
import enum

class TOKENS(enum.Enum):
    T_LAMB = enum.auto()
    T_OP   = enum.auto()
    T_PUNC = enum.auto()
    T_VAR  = enum.auto()
    T_NUM  = enum.auto()
    T_WHITESPACE = enum.auto()

    @staticmethod
    def get_charset(token_type):
        if token_type == TOKENS.T_LAMB:
            return "λ\\"

        if token_type == TOKENS.T_OP:
            return "."

        if token_type == TOKENS.T_PUNC:
            return "()"

        if token_type == TOKENS.T_VAR:
            return string.ascii_letters + string.digits

        if token_type == TOKENS.T_NUM:
            return string.digits
        
        if token_type == TOKENS.T_WHITESPACE:
            return " \t\r\n"

        return ""

    @staticmethod
    def is_whitespace(letter):
        return letter in TOKENS.get_charset(TOKENS.T_WHITESPACE)

    @staticmethod
    def is_lamb(tok):
        return tok in TOKENS.get_charset(TOKENS.T_LAMB)
    
    @staticmethod
    def is_op(tok):
        return tok in TOKENS.get_charset(TOKENS.T_OP)
    
    @staticmethod
    def is_punc(tok):
        return tok in TOKENS.get_charset(TOKENS.T_PUNC)
    
    @staticmethod
    def is_var(tok):
        return tok in TOKENS.get_charset(TOKENS.T_VAR)

    @staticmethod
    def is_num(tok):
        return tok in TOKENS.get_charset(TOKENS.T_NUM)

class Token:
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

    def __eq__(self, other):
        return self.token_type == other.token_type and self.value == other.value
    
    def __repr__(self):
        return "Token(%s, '%s')" % (self.token_type, self.value)

class LanguageStream:
    def __init__(self, container, skip_charset=" \t\r\n"):
        self.container = container
        self.skip_charset = skip_charset
        self.pos = 0
        self.save_pos = []

    def peek(self):
        return self.container[self.pos]
    
    def seek(self, position):
        self.pos = position

    def move(self, offset):
        self.pos += offset

    def push_pos(self):
        self.save_pos.append(self.pos)
    
    def pop_pos(self):
        self.pos = self.save_pos.pop()

    def decrease(self):
        self.move(-1)

    def increase(self):
        self.move(1)
    
    def first(self):
        try:
            current = self.peek()
        except:
            raise EOFError(self.get_position())
        
        self.increase()
        return current
    
    def eof(self):
        return self.pos >= len(self.container.strip())

    def get_position(self):
        return (self.pos, self.container[:self.pos].count("\n"), len(self.container[:self.pos].split("\n")[-1]))

class LexException(Exception):
    ...

class LambEx(LanguageStream):
    def read_multitoken(self, allowed_variable_charset):
        token = ""

        while not self.eof() and (curr := self.first()) in allowed_variable_charset:
            token += curr
        
        if curr not in allowed_variable_charset:
            self.decrease()
        
        if not token:
            raise LexException("Empty token, while trying to lex at (index, line, column): %s" % repr(self.get_position()))

        return token

    def read_var(self):
        return Token(TOKENS.T_VAR, self.read_multitoken(TOKENS.get_charset(TOKENS.T_VAR)))

    def read_num(self):
        return Token(TOKENS.T_NUM, self.read_multitoken(TOKENS.get_charset(TOKENS.T_NUM)))

    def next_token(self):
        while TOKENS.is_whitespace(curr := self.first()):
            pass
        
        if TOKENS.is_lamb(curr):
            return Token(TOKENS.T_LAMB, curr)
        
        if TOKENS.is_op(curr):
            return Token(TOKENS.T_OP, curr)
        
        if TOKENS.is_punc(curr):
            return Token(TOKENS.T_PUNC, curr)

        self.decrease()

        if TOKENS.is_num(curr):
            return self.read_num()

        if TOKENS.is_var(curr):
            return self.read_var()
        
        self.increase()

        raise LexException("Could not lex \"%s\" at (index, line, column): %s" % (curr, self.get_position()))

    def peek_token(self, n=1):
        tokens = []

        self.push_pos()

        for _ in range(n):
            tokens.append(self.next_token())
        
        self.pop_pos()

        return tokens[n-1]

    def has_token(self):
        return not self.eof()

    def has_n_tokens_available(self, n):
        tokens = []
        
        self.push_pos()

        for _ in range(n):
            try:
                tokens.append(self.next_token())
            except:
                break
        
        self.pop_pos()

        return len(tokens) == n

    def __iter__(self):
        self.seek(0)
        return self
    
    def __next__(self):
        if self.has_token():
            return self.next_token()
        
        raise StopIteration

if __name__ == "__main__":
    def test_LanguageStream():
        l = LanguageStream("this is\nan example lang\nStream!")

        l.increase()
        
        assert l.first() == "h"
        assert l.first() == "i"
        assert l.eof() == False
        
        while l.first() != "n":
            pass
        
        assert l.first() == " "
        assert l.get_position() == (len("this is\nan "), 1, 2), l.get_position()

        while l.first() != "!":
            pass
        
        assert l.eof() == True

        return True

    def test_LambEx():
        lex = LambEx("(\\x.λy.x) fo456obar 5672")

        assert all([a == b for a, b in zip(lex, [Token(TOKENS.T_PUNC, "("), Token(TOKENS.T_LAMB, "\\"), Token(TOKENS.T_VAR, "x"), Token(TOKENS.T_OP, "."), Token(TOKENS.T_LAMB, "λ"), Token(TOKENS.T_VAR, "y"), Token(TOKENS.T_OP, "."), Token(TOKENS.T_VAR, "x"), Token(TOKENS.T_PUNC, ")"), Token(TOKENS.T_VAR, "fo456obar"), Token(TOKENS.T_NUM, "5672")])])

        assert lex.eof()
        
        lex.seek(0)

        assert not lex.eof()

        assert all([lex.next_token() == correct for correct in [Token(TOKENS.T_PUNC, "("), Token(TOKENS.T_LAMB, "\\"), Token(TOKENS.T_VAR, "x"), Token(TOKENS.T_OP, "."), Token(TOKENS.T_LAMB, "λ"), Token(TOKENS.T_VAR, "y"), Token(TOKENS.T_OP, "."), Token(TOKENS.T_VAR, "x"), Token(TOKENS.T_PUNC, ")"), Token(TOKENS.T_VAR, "fo456obar"), Token(TOKENS.T_NUM, "5672")]])

        assert lex.eof()

        return True
    
    print(test_LanguageStream())
    print(test_LambEx())