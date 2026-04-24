from tokens import TokenType

class AST: pass
class Number(AST):
    def __init__(self, value): self.value = value
class FloatNode(AST):
    def __init__(self, value): self.value = value
class Call(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args
class Variable(AST):
    def __init__(self, name): self.name = name
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
    def __init__(self, value): self.value = value
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
    def __init__(self, value): self.value = value
class Function(AST):
    def __init__(self, name, params, return_type, body):
        self.name = name
        self.params = params  
        self.return_type = return_type
        self.body = body
class ArrayLiteral(AST):
    def __init__(self, elements): self.elements = elements
class ArrayIndex(AST):
    def __init__(self, name, index):
        self.name = name
        self.index = index
class Program(AST):
    def __init__(self, statements): self.statements = statements

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[self.pos]

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = self.tokens[-1]

    def peek(self):
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None

    def eat(self, token_type):
        if self.current.type == token_type: self.advance()
        else: raise Exception(f"Parser Error: Expected {token_type}, got {self.current.type}")

    def parse(self):
        statements = []
        while self.current.type != TokenType.EOF:
            statements.append(self.statement())
        return Program(statements)

    def statement(self):
        if self.current.type == TokenType.LET: return self.var_decl()
        elif self.current.type == TokenType.PRINT: return self.print_stmt()
        elif self.current.type == TokenType.IF: return self.if_stmt()
        elif self.current.type == TokenType.WHILE: return self.while_stmt()
        elif self.current.type == TokenType.RETURN: return self.return_stmt()
        elif self.current.type == TokenType.FUNC: return self.function_decl()
        elif self.current.type == TokenType.IDENTIFIER and self.peek() and self.peek().type == TokenType.EQUAL:
            return self.assignment()
        else: raise Exception(f"Unexpected statement: {self.current.type}")

    def function_decl(self):
        self.eat(TokenType.FUNC)
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.LPAREN)
        params = []
        if self.current.type != TokenType.RPAREN:
            params.append(self.parameter())
            while self.current.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                params.append(self.parameter())
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.ARROW)
        return_type = self.current.value
        self.eat(TokenType.IDENTIFIER)
        body = self.block()
        return Function(name, params, return_type, body)

    def parameter(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.COLON)
        param_type = ""
        if self.current.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            param_type = "[" + self.current.value + "]"
            self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.RBRACKET)
        else:
            param_type = self.current.value
            self.eat(TokenType.IDENTIFIER)
        return {"name": name, "type": param_type}

    def assignment(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUAL)
        value = self.expression()
        return Assignment(name, value)

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
        value = self.expression()
        return Return(value)

    def block(self):
        statements = []
        self.eat(TokenType.LBRACE)
        while self.current.type != TokenType.RBRACE and self.current.type != TokenType.EOF:
            statements.append(self.statement())
        self.eat(TokenType.RBRACE)
        return statements

    def expression(self): return self.comparison()

    def comparison(self):
        node = self.term()
        while self.current.type in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
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
        if self.current.type == TokenType.MINUS:
            self.advance()
            return BinaryOp(Number(0), TokenType.MINUS, self.primary())
        return self.primary()

    def primary(self):
        token = self.current
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(token.value)
        elif token.type == TokenType.FLOAT:
            self.eat(TokenType.FLOAT)
            return FloatNode(token.value)
        elif token.type == TokenType.IDENTIFIER:
            name = token.value
            self.eat(TokenType.IDENTIFIER)
            if self.current.type == TokenType.LPAREN: # FIXED: Call check added
                self.eat(TokenType.LPAREN)
                args = []
                if self.current.type != TokenType.RPAREN:
                    args.append(self.expression())
                    while self.current.type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        args.append(self.expression())
                self.eat(TokenType.RPAREN)
                return Call(name, args)
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
        else: raise Exception(f"Unexpected token: {token.type}")