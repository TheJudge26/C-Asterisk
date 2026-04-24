from tokens import TokenType

# -------------------------
# AST BASE
# -------------------------
class AST:
    pass

# -------------------------
# AST NODES
# -------------------------
class Number(AST):
    def __init__(self, value):
        self.value = value

class Variable(AST):
    def __init__(self, name):
        self.name = name

class BinaryOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class VarDecl(AST):
    def __init__(self, name, type_annotation, value):
        self.name = name
        self.type_annotation = type_annotation
        self.value = value

class Assignment(AST):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Print(AST):
    def __init__(self, value):
        self.value = value

class If(AST):
    def __init__(self, condition, body, else_body=None):
        self.condition = condition
        self.body = body
        self.else_body = else_body

class While(AST):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class Return(AST):
    def __init__(self, value):
        self.value = value

# NEW: For function calls like calculate()
class Call(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args

# UPDATED: Added return_type
class Function(AST):
    def __init__(self, name, body, return_type=None):
        self.name = name
        self.body = body
        self.return_type = return_type

# NEW: For [1, 2, 3]
class ArrayLiteral(AST):
    def __init__(self, elements):
        self.elements = elements

# NEW: For weights[i]
class ArrayIndex(AST):
    def __init__(self, name, index):
        self.name = name
        self.index = index

class Program(AST):
    def __init__(self, statements):
        self.statements = statements

# -------------------------
# PARSER
# -------------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tokens_len = len(tokens)
        self.pos = 0
        self.current = tokens[self.pos]

    def advance(self):
        self.pos += 1
        if self.pos < self.tokens_len:
            self.current = self.tokens[self.pos]
        else:
            self.current = self.tokens[-1]

    def peek(self):
        if self.pos + 1 < self.tokens_len:
            return self.tokens[self.pos + 1]
        return None

    def next_token_type(self):
        next_pos = self.pos + 1
        if next_pos < self.tokens_len:
            return self.tokens[next_pos].type
        return None

    def eat(self, token_type):
        if self.current.type == token_type:
            self.advance()
        else:
            raise Exception(f"Expected {token_type}, got {self.current.type}")

    def parse(self):
        statements = []
        append_statement = statements.append
        while self.current.type != TokenType.EOF:
            append_statement(self.statement())
        return Program(statements)

    def statement(self):
        current_type = self.current.type
        if current_type == TokenType.LET:
            return self.var_decl()
        elif current_type == TokenType.PRINT:
            return self.print_stmt()
        elif current_type == TokenType.IF:
            return self.if_stmt()
        elif current_type == TokenType.WHILE:
            return self.while_stmt()
        elif current_type == TokenType.RETURN:
            return self.return_stmt()
        elif current_type == TokenType.FUNC:
            return self.function_decl()
        elif current_type == TokenType.IDENTIFIER and self.next_token_type() == TokenType.EQUAL:
            return self.assignment()
        else:
            raise Exception(f"Unexpected statement: {self.current.type}")

    # UPDATED: Handles "func calculate() -> int {"
    def function_decl(self):
        self.eat(TokenType.FUNC)
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        
        return_type = "void"
        if self.current.type == TokenType.ARROW:
            self.eat(TokenType.ARROW)
            return_type = self.current.value
            self.eat(TokenType.IDENTIFIER)
            
        body = self.block()
        return Function(name, body, return_type)

    def assignment(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUAL)
        value = self.expression()
        return Assignment(name, value)

    # UPDATED: Handles both "let x: int" AND "let x: [int]"
    def var_decl(self):
        self.eat(TokenType.LET)
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.COLON)

        type_annotation = ""
        if self.current.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            type_annotation = "[" + self.current.value + "]"
            self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.RBRACKET)
        else:
            type_annotation = self.current.value
            self.eat(TokenType.IDENTIFIER)

        self.eat(TokenType.EQUAL)
        value = self.expression()
        return VarDecl(name, type_annotation, value)

    def print_stmt(self):
        self.eat(TokenType.PRINT)
        self.eat(TokenType.LPAREN)
        value = self.expression()
        self.eat(TokenType.RPAREN)
        return Print(value)

    def if_stmt(self):
        self.eat(TokenType.IF)
        condition = self.expression()
        body = self.block()
        else_body = None
        if self.current.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            else_body = self.block()
        return If(condition, body, else_body)

    def while_stmt(self):
        self.eat(TokenType.WHILE)
        condition = self.expression()
        body = self.block()
        return While(condition, body)

    def return_stmt(self):
        self.eat(TokenType.RETURN)
        # Check if there's an expression or just semicolon
        if self.current.type in (TokenType.RBRACE, TokenType.EOF):
            return Return(None)
        value = self.expression()
        return Return(value)

    def block(self):
        statements = []
        append_statement = statements.append
        self.eat(TokenType.LBRACE)
        while self.current.type != TokenType.RBRACE and self.current.type != TokenType.EOF:
            append_statement(self.statement())
        self.eat(TokenType.RBRACE)
        return statements

    def expression(self):
        return self.comparison()

    def comparison(self):
        node = self.term()
        while self.current.type in (TokenType.GREATER, TokenType.LESS):
            op = self.current.type
            self.advance()
            right = self.term()
            node = BinaryOp(node, op, right)
        return node

    def term(self):
        node = self.factor()
        while self.current.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current.type
            self.advance()
            right = self.factor()
            node = BinaryOp(node, op, right)
        return node

    def factor(self):
        node = self.unary()
        while self.current.type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.current.type
            self.advance()
            right = self.unary()
            node = BinaryOp(node, op, right)
        return node

    def unary(self):
        token = self.current
        if token.type == TokenType.MINUS:
            self.advance()
            return BinaryOp(Number(0), TokenType.MINUS, self.primary())
        return self.primary()

    # UPDATED: Handles [1,2,3] and weights[i]
    def primary(self):
        token = self.current

        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(token.value)

        elif token.type == TokenType.IDENTIFIER:
            name = token.value
            self.eat(TokenType.IDENTIFIER)

            # Is it a function call? e.g. calculate()
            if self.current.type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = []
                if self.current.type != TokenType.RPAREN:
                    args.append(self.expression())
                    while self.current.type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        args.append(self.expression())
                self.eat(TokenType.RPAREN)
                return Call(name, args)

            # Is it an array index? e.g. weights[i]
            if self.current.type == TokenType.LBRACKET:
                self.eat(TokenType.LBRACKET)
                index = self.expression()
                self.eat(TokenType.RBRACKET)
                return ArrayIndex(name, index)

            return Variable(name)

        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
            return node
            
        elif token.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            elements = []
            if self.current.type != TokenType.RBRACKET:
                elements.append(self.expression())
                while self.current.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    elements.append(self.expression())
            self.eat(TokenType.RBRACKET)
            return ArrayLiteral(elements)

        else:
            raise Exception(f"Unexpected token: {token.type}")
