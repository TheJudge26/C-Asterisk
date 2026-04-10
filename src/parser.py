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
    def __init__(self, name, value):
        self.name = name
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


class Function(AST):
    def __init__(self, name, body):
        self.name = name
        self.body = body


class Program(AST):
    def __init__(self, statements):
        self.statements = statements


# -------------------------
# PARSER
# -------------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[self.pos]

    # -------------------------
    # CORE UTILS
    # -------------------------
    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = self.tokens[-1]

    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None

    def eat(self, token_type):
        if self.current.type == token_type:
            self.advance()
        else:
            raise Exception(
                f"Expected {token_type}, got {self.current.type}"
            )

    # -------------------------
    # ENTRY POINT
    # -------------------------
    def parse(self):
        statements = []

        while self.current.type != TokenType.EOF:
            stmt = self.statement()
            statements.append(stmt)

        return Program(statements)

    # -------------------------
    # STATEMENTS
    # -------------------------
    def statement(self):
        if self.current.type == TokenType.LET:
            return self.var_decl()

        elif self.current.type == TokenType.PRINT:
            return self.print_stmt()

        elif self.current.type == TokenType.IF:
            return self.if_stmt()

        elif self.current.type == TokenType.WHILE:
            return self.while_stmt()

        elif self.current.type == TokenType.RETURN:
            return self.return_stmt()

        elif self.current.type == TokenType.FUNC:
            return self.function_decl()

        elif (
            self.current.type == TokenType.IDENTIFIER
            and self.peek()
            and self.peek().type == TokenType.EQUAL
        ):
            return self.assignment()

        else:
            raise Exception(f"Unexpected statement: {self.current.type}")

    # -------------------------
    # FUNCTION
    # -------------------------
    def function_decl(self):
        self.eat(TokenType.FUNC)

        name = self.current.value
        self.eat(TokenType.IDENTIFIER)

        body = self.block()

        return Function(name, body)

    # -------------------------
    # ASSIGNMENT
    # -------------------------
    def assignment(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)

        self.eat(TokenType.EQUAL)

        value = self.expression()

        return Assignment(name, value)

    # -------------------------
    # let x = expr
    # -------------------------
    def var_decl(self):
        self.eat(TokenType.LET)

        name = self.current.value
        self.eat(TokenType.IDENTIFIER)

        self.eat(TokenType.EQUAL)

        value = self.expression()

        return VarDecl(name, value)

    # -------------------------
    # print(expr)
    # -------------------------
    def print_stmt(self):
        self.eat(TokenType.PRINT)
        self.eat(TokenType.LPAREN)

        value = self.expression()

        self.eat(TokenType.RPAREN)

        return Print(value)

    # -------------------------
    # if condition (...) else (...)
    # -------------------------
    def if_stmt(self):
        self.eat(TokenType.IF)

        condition = self.expression()

        body = self.block()

        else_body = None

        if self.current.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            else_body = self.block()

        return If(condition, body, else_body)

    # -------------------------
    # while condition (...)
    # -------------------------
    def while_stmt(self):
        self.eat(TokenType.WHILE)

        condition = self.expression()

        body = self.block()

        return While(condition, body)

    # -------------------------
    # return expr
    # -------------------------
    def return_stmt(self):
        self.eat(TokenType.RETURN)
        value = self.expression()
        return Return(value)

    # -------------------------
    # BLOCK
    # -------------------------
    def block(self):
        statements = []

        self.eat(TokenType.LBRACE)

        while (
            self.current.type != TokenType.RBRACE
            and self.current.type != TokenType.EOF
        ):
            statements.append(self.statement())

        self.eat(TokenType.RBRACE)

        return statements

   
    # EXPRESSIONS
  
    def expression(self):
        return self.comparison()

    def comparison(self):
        node = self.term()

        while self.current.type in (
            TokenType.GREATER,
            TokenType.LESS,
        ):
            op = self.current.type
            self.advance()
            right = self.term()
            node = BinaryOp(node, op, right)

        return node

    def term(self):
        node = self.factor()

        while self.current.type in (
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            op = self.current.type
            self.advance()
            right = self.factor()
            node = BinaryOp(node, op, right)

        return node

    def factor(self):
        node = self.unary()

        while self.current.type in (
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
        ):
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

    def primary(self):
        token = self.current

        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(token.value)

        elif token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            return Variable(token.value)

        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
            return node

        else:
            raise Exception(f"Unexpected token: {token.type}")