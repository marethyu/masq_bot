import enum

from abc import ABC, abstractmethod

supported_funcs = ["pow",
                   "sqrt",
                   "abs",
                   "floor",
                   "ceil",
                   "log2",
                   "log10",
                   "exp",
                   "sin",
                   "cos",
                   "tan",
                   "asin",
                   "acos",
                   "atan",]

class TokType(enum.Enum):
    REAL_NUM = 0
    OPERATOR = 1
    UNARY_OP = 2
    FUNCTION = 3
    UNK_FUNC = 4
    LBRACKET = 5
    RBRACKET = 6
    UNKNOWNT = 7

class Token:
    def __init__(self, t_type, value):
        self.t_type = t_type
        self.value = value

class MiniLexer:
    def __init__(self, expr):
        self.expr = expr
        self.idx = -1
        self.peek = None
        self.prev_ttype = None
        self.ht = {}
        self._init_dict()
        self._advance()
        self.done = False
    
    def scan(self):
        if self.done:
            return
        
        while self.expr[self.idx] == " ":
            self.idx += 1
        self.peek = self.expr[self.idx]
        
        if self.peek in ["+", "-", "*", "/"]:
            token = None
            
            if (self.expr[self.idx + 1] == "(" or self.expr[self.idx + 1].isalnum()) and self.peek in ["+", "-"] and (self.prev_ttype is TokType.OPERATOR or self.prev_ttype is TokType.LBRACKET or self.prev_ttype is None):
                self.prev_ttype = TokType.UNARY_OP
                token = Token(TokType.UNARY_OP, self.peek)
            else:
                self.prev_ttype = TokType.OPERATOR
                token = Token(TokType.OPERATOR, self.peek)
            
            self._advance()
            
            return token
        
        if self.peek.isdigit():
            value = 0.0
            
            while self.peek.isdigit():
                value = 10 * value + float(self.peek)
                self._advance()
            
            if self.peek is not ".":
                self.prev_ttype = TokType.REAL_NUM
                return Token(TokType.REAL_NUM, str(value))
            
            x = 10.0
            
            while True:
                self._advance()
                
                if not self.peek.isdigit():
                    break
                
                value += float(self.peek) / x
                x *= 10.0
            
            self.prev_ttype = TokType.REAL_NUM
            return Token(TokType.REAL_NUM, str(value))
        
        if self.peek.isalpha():
            func = ""
            
            while self.peek.isalnum():
                func += self.peek
                self._advance()
            
            if func in self.ht:
                return self.ht[func]
            
            self.prev_ttype = TokType.UNK_FUNC
            return Token(TokType.UNK_FUNC, func)
        
        if self.peek is "(":
            self.prev_ttype = TokType.LBRACKET
            token = Token(TokType.LBRACKET, self.peek)
            self._advance()
            return token
        
        if self.peek is ")":
            self.prev_ttype = TokType.RBRACKET
            token = Token(TokType.RBRACKET, self.peek)
            self._advance()
            return token
        
        self.prev_ttype = TokType.UNKNOWNT
        token = Token(TokType.UNKNOWNT, self.peek)
        self._advance()
        
        return token
    
    def _advance(self):
        self.idx += 1
        if self.idx == len(self.expr):
            self.peek = "_"
            self.done = True
            return
        elif self.idx > len(self.expr):
            self.peek = "_"
            return
        self.peek = self.expr[self.idx]
    
    def _init_dict(self):
        for func in supported_funcs:
            self.ht[func] = Token(TokType.FUNCTION, func)

class ASTNode(ABC):
    def __init__(self):
        super.__init__()
    
    @abstractmethod
    def reduce(self):
        pass

class RealNumber(ASTNode):
    def __init__(self, fvalue):
        self.fvalue = fvalue
    
    def reduce(self):
        return self.fvalue

class FunctionCall(ASTNode):
    def __init__(self, fname, expr):
        self.fname = fname
        self.expr = expr
    
    def reduce(self):
        import math
        return math.__dict__[self.fname](self.expr.reduce())

class UnaryOperator(ASTNode):
    def __init__(self, is_minus, expr):
        self.is_minus = is_minus
        self.expr = expr
    
    def reduce(self):
        reduced_val = self.expr.reduce()
        return -reduced_val if self.is_minus else reduced_val

class BinaryOperator(ASTNode):
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op
    
    def reduce(self):
        if self.op == "+":
            return self.left.reduce() + self.right.reduce()
        elif self.op == "-":
            return self.left.reduce() - self.right.reduce()
        elif self.op == "*":
            return self.left.reduce() * self.right.reduce()
        elif self.op == "/":
            return self.left.reduce() / self.right.reduce()

class ParseError(Exception):
    def __init__(self, message):
        super(ParseError, self).__init__(message)

class ExpressionParser:
    def __init__(self, lex):
        self.lex = lex
        self.look = None
        self._next()
    
    def parse(self):
        '''
        BNF grammar for a math expression
        
        <expression> ::= <term> "+" <term> |
                         <term> "-" <term> |
                         <term>
        <term> ::= <factor> "*" <factor> |
                   <factor> "/" <factor> |
                   <factor>
        <factor> ::= <real number> | <function call> | <unary op> "(" <expression> ")" | "(" <expression> ")"
        '''
        return self._expr().reduce()
    
    def _expr(self):
        expr = self._term()
        
        while self.look.t_type is TokType.OPERATOR and self.look.value in ["+", "-"]:
            op = self.look.value
            self._consume(TokType.OPERATOR)
            expr = BinaryOperator(expr, self._term(), op)
        
        return expr
    
    def _term(self):
        term = self._factor()
        
        while self.look.t_type is TokType.OPERATOR and self.look.value in ["*", "/"]:
            op = self.look.value
            self._consume(TokType.OPERATOR)
            term = BinaryOperator(term, self._factor(), op)
        
        return term
    
    def _factor(self):
        if self.look.t_type is TokType.REAL_NUM:
            real_num = RealNumber(float(self.look.value))
            self._consume(TokType.REAL_NUM)
            return real_num
        elif self.look.t_type is TokType.FUNCTION:
            fcall = None
            fname = self.look.value
            
            self._consume(TokType.FUNCTION)
            self._consume(TokType.LBRACKET)
            fcall = FunctionCall(fname, self._expr())
            self._consume(TokType.RBRACKET)
            
            return fcall
        elif self.look.t_type is TokType.UNARY_OP:
            unary_op = None
            is_minus = self.look.value is "-"
            
            self._consume(TokType.UNARY_OP)
            
            if self.look.t_type is TokType.LBRACKET:
                self._consume(TokType.LBRACKET)
                unary_op = UnaryOperator(is_minus, self._expr())
                self._consume(TokType.RBRACKET)
            elif self.look.t_type is TokType.FUNCTION:
                fname = self.look.value
                
                self._consume(TokType.FUNCTION)
                self._consume(TokType.LBRACKET)
                unary_op = UnaryOperator(is_minus, FunctionCall(fname, self._expr()))
                self._consume(TokType.RBRACKET)
            else: # self.look.t_type is TokType.REAL_NUM
                unary_op = UnaryOperator(is_minus, self._expr())
            
            return unary_op
        elif self.look.t_type is TokType.LBRACKET:
            expr = None
            
            self._consume(TokType.LBRACKET)
            expr = self._expr()
            self._consume(TokType.RBRACKET)
            
            return expr
        else:
            raise ParseError("Got " + str(self.look.t_type) + " what happened?")
    
    def _consume(self, t_type):
        if self.look.t_type is t_type:
            self._next()
        else:
            raise ParseError("Expected " + str(t_type) + ", but got " + str(self.look.t_type))
    
    def _next(self):
        if not self.lex.done:
            self.look = self.lex.scan()