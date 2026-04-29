"""
parser.py — Recursive-descent parser for C*.

Level 6 Updates:
1. Added Boolean AST node.
2. Updated parse_type() to handle the 'bool' keyword.
3. Updated _primary() to handle 'true' and 'false' literals.
4. Preserved Level 5 recursive tensor parsing and ArrayIndex chaining.
"""

from tokens import TokenType

# ═══════════════════════════════════════════════════════════════════
#  AST node hierarchy
# ═══════════════════════════════════════════════════════════════════

class AST:                  pass

class Number(AST):
    def __init__(self, value):                self.value = value

class FloatNode(AST):
    def __init__(self, value):                self.value = value

class Boolean(AST):
    """New for Level 6: Represents true or false literals."""
    def __init__(self, value):                self.value = value

class Variable(AST):
    def __init__(self, name):                 self.name = name

class ArrayLiteral(AST):
    def __init__(self, elements):             self.elements = elements

class ArrayIndex(AST):
    """Represents a single indexing step: base[index]."""
    def __init__(self, base, index):
        self.name  = base   
        self.index = index

class BinaryOp(AST):
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op
        self.right = right

class VarDecl(AST):
    def __init__(self, name, type_annotation, value):
        self.name            = name
        self.type_annotation = type_annotation
        self.value           = value

class Assignment(AST):
    def __init__(self, name, value):
        self.name  = name
        self.value = value

class Print(AST):
    def __init__(self, value):                self.value = value

class If(AST):
    def __init__(self, condition, body, else_body=None):
        self.condition = condition
        self.body      = body
        self.else_body = else_body

class While(AST):
    def __init__(self, condition, body):
        self.condition = condition
        self.body      = body

class Return(AST):
    def __init__(self, value):                self.value = value

class Call(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class Function(AST):
    def __init__(self, name, params, return_type, body):
        self.name        = name
        self.params      = params        
        self.return_type = return_type
        self.body        = body

class Program(AST):
    def __init__(self, statements):       self.statements = statements


# ═══════════════════════════════════════════════════════════════════
#  Parser
# ═══════════════════════════════════════════════════════════════════

class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens  = tokens
        self.pos     = 0
        self.current = tokens[0]

    # ---------------------------------------------------------------- helpers

    def _advance(self):
        self.pos += 1
        self.current = self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def _peek(self):
        nxt = self.pos + 1
        return self.tokens[nxt] if nxt < len(self.tokens) else None

    def _eat(self, token_type: TokenType):
        if self.current.type == token_type:
            self._advance()
        else:
            raise ParseError(
                f"Line {self.current.line}, Col {self.current.column}: "
                f"Expected {token_type}, got {self.current.type} ({self.current.value!r})"
            )

    # ---------------------------------------------------------------- types

    def parse_type(self) -> str:
        """Preserves Level 5 recursive parsing for [[float]]."""
        if self.current.type == TokenType.LBRACKET:
            self._eat(TokenType.LBRACKET)
            inner = self.parse_type()          
            self._eat(TokenType.RBRACKET)
            return f"[{inner}]"
        
        # Milestone 1: Handle bool keyword
        if self.current.type == TokenType.BOOL_TYPE:
            self._eat(TokenType.BOOL_TYPE)
            return "bool"
            
        name = self.current.value
        self._eat(TokenType.IDENTIFIER)
        return name

    # ---------------------------------------------------------------- entry

    def parse(self) -> Program:
        statements = []
        while self.current.type != TokenType.EOF:
            statements.append(self._statement())
        return Program(statements)

    # ---------------------------------------------------------------- statements

    def _statement(self):
        t = self.current.type
        if   t == TokenType.LET:    return self._var_decl()
        elif t == TokenType.PRINT:  return self._print_stmt()
        elif t == TokenType.IF:     return self._if_stmt()
        elif t == TokenType.WHILE:  return self._while_stmt()
        elif t == TokenType.RETURN: return self._return_stmt()
        elif t == TokenType.FUNC:   return self._function_decl()
        elif (t == TokenType.IDENTIFIER
              and self._peek() is not None
              and self._peek().type == TokenType.EQUAL):
            return self._assignment()
        else:
            raise ParseError(
                f"Line {self.current.line}, Col {self.current.column}: "
                f"Unexpected token {self.current.type} ({self.current.value!r})"
            )

    def _function_decl(self) -> Function:
        self._eat(TokenType.FUNC)
        name = self.current.value
        self._eat(TokenType.IDENTIFIER)
        self._eat(TokenType.LPAREN)

        params = []
        if self.current.type != TokenType.RPAREN:
            params.append(self._parameter())
            while self.current.type == TokenType.COMMA:
                self._eat(TokenType.COMMA)
                params.append(self._parameter())

        self._eat(TokenType.RPAREN)
        self._eat(TokenType.ARROW)
        ret_ty = self.parse_type()          
        return Function(name, params, ret_ty, self._block())

    def _parameter(self) -> dict:
        name = self.current.value
        self._eat(TokenType.IDENTIFIER)
        self._eat(TokenType.COLON)
        return {"name": name, "type": self.parse_type()}   

    def _var_decl(self) -> VarDecl:
        self._eat(TokenType.LET)
        name = self.current.value
        self._eat(TokenType.IDENTIFIER)
        self._eat(TokenType.COLON)
        ty = self.parse_type()              
        self._eat(TokenType.EQUAL)
        return VarDecl(name, ty, self._expression())

    def _assignment(self) -> Assignment:
        name = self.current.value
        self._eat(TokenType.IDENTIFIER)
        self._eat(TokenType.EQUAL)
        return Assignment(name, self._expression())

    def _print_stmt(self) -> Print:
        self._eat(TokenType.PRINT)
        self._eat(TokenType.LPAREN)
        val = self._expression()
        self._eat(TokenType.RPAREN)
        return Print(val)

    def _if_stmt(self) -> If:
        self._eat(TokenType.IF)
        cond = self._expression()
        body = self._block()
        else_body = None
        if self.current.type == TokenType.ELSE:
            self._eat(TokenType.ELSE)
            else_body = self._block()
        return If(cond, body, else_body)

    def _while_stmt(self) -> While:
        self._eat(TokenType.WHILE)
        return While(self._expression(), self._block())

    def _return_stmt(self) -> Return:
        self._eat(TokenType.RETURN)
        return Return(self._expression())

    def _block(self) -> list:
        statements = []
        self._eat(TokenType.LBRACE)
        while self.current.type not in (TokenType.RBRACE, TokenType.EOF):
            statements.append(self._statement())
        self._eat(TokenType.RBRACE)
        return statements

    # ---------------------------------------------------------------- expressions

    def _expression(self):
        return self._comparison()

    def _comparison(self):
        node = self._term()
        while self.current.type in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
            op = self.current.type
            self._advance()
            node = BinaryOp(node, op, self._term())
        return node

    def _term(self):
        node = self._factor()
        while self.current.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current.type
            self._advance()
            node = BinaryOp(node, op, self._factor())
        return node

    def _factor(self):
        node = self._unary()
        while self.current.type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.current.type
            self._advance()
            node = BinaryOp(node, op, self._unary())
        return node

    def _unary(self):
        if self.current.type == TokenType.MINUS:
            self._advance()
            return BinaryOp(Number(0), TokenType.MINUS, self._primary())
        return self._primary()

    def _primary(self):
        token = self.current

        if token.type == TokenType.NUMBER:
            self._eat(TokenType.NUMBER)
            return Number(token.value)

        if token.type == TokenType.FLOAT:
            self._eat(TokenType.FLOAT)
            return FloatNode(token.value)
            
        # Milestone 1: Boolean literals
        if token.type == TokenType.TRUE:
            self._eat(TokenType.TRUE)
            return Boolean(True)
        if token.type == TokenType.FALSE:
            self._eat(TokenType.FALSE)
            return Boolean(False)

        if token.type == TokenType.IDENTIFIER:
            name = token.value
            self._eat(TokenType.IDENTIFIER)

            if self.current.type == TokenType.LPAREN:
                self._eat(TokenType.LPAREN)
                args = []
                if self.current.type != TokenType.RPAREN:
                    args.append(self._expression())
                    while self.current.type == TokenType.COMMA:
                        self._eat(TokenType.COMMA)
                        args.append(self._expression())
                self._eat(TokenType.RPAREN)
                return Call(name, args)

            # Preserves chaining: matrix[i][j]
            node = Variable(name)
            while self.current.type == TokenType.LBRACKET:
                self._eat(TokenType.LBRACKET)
                idx  = self._expression()
                self._eat(TokenType.RBRACKET)
                node = ArrayIndex(node, idx)
            return node

        if token.type == TokenType.LPAREN:
            self._eat(TokenType.LPAREN)
            node = self._expression()
            self._eat(TokenType.RPAREN)
            return node

        if token.type == TokenType.LBRACKET:
            self._eat(TokenType.LBRACKET)
            elements = []
            if self.current.type != TokenType.RBRACKET:
                elements.append(self._expression())
                while self.current.type == TokenType.COMMA:
                    self._eat(TokenType.COMMA)
                    elements.append(self._expression())
            self._eat(TokenType.RBRACKET)
            return ArrayLiteral(elements)

        raise ParseError(
            f"Line {token.line}, Col {token.column}: "
            f"Unexpected token {token.type} ({token.value!r}) in expression"
        )