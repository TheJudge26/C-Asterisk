from tokens import TokenType
from errors import ParserError


# =========================
# AST BASE
# =========================
class AST:
    pass


# =========================
# LITERALS
# =========================
class Number(AST):
    def __init__(self, value):
        self.value = value


class FloatNode(AST):
    def __init__(self, value):
        self.value = value


class StringNode(AST):
    def __init__(self, value):
        self.value = value


class BoolNode(AST):
    def __init__(self, value):
        self.value = value


# =========================
# EXPRESSIONS
# =========================
class Variable(AST):
    def __init__(self, name):
        self.name = name


class Call(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.object = None  # for method calls


class BinaryOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


# =========================
# STATEMENTS
# =========================
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


class For(AST):
    def __init__(self, var, iterable, body):
        self.var = var
        self.iterable = iterable
        self.body = body


class Return(AST):
    def __init__(self, value):
        self.value = value

class ExpressionStatement(AST):
    def __init__(self, expression):
        self.expression = expression


# =========================
# FUNCTIONS
# =========================
class Function(AST):
    def __init__(self, name, params, return_type, body):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body


# =========================
# ARRAYS
# =========================
class ArrayLiteral(AST):
    def __init__(self, elements):
        self.elements = elements


class ArrayIndex(AST):
    def __init__(self, array, index):
        self.array = array
        self.index = index


# =========================
# PROGRAM
# =========================
class Program(AST):
    def __init__(self, statements):
        self.statements = statements


# =========================
# CLASSES
# =========================
class ClassDecl(AST):
    def __init__(self, name, body):
        self.name = name
        self.body = body


class MemberAccess(AST):
    def __init__(self, obj, member):
        self.object = obj
        self.member = member


class Import(AST):
    def __init__(self, module):
        self.module = module

PRECEDENCE = {
    TokenType.EQUAL_EQUAL: 1,
    TokenType.NOT_EQUAL: 1,

    TokenType.GREATER: 2,
    TokenType.LESS: 2,
    TokenType.GREATER_EQUAL: 2,
    TokenType.LESS_EQUAL: 2,

    TokenType.PLUS: 3,
    TokenType.MINUS: 3,

    TokenType.MULTIPLY: 4,
    TokenType.DIVIDE: 4,
}

# =========================
# PARSER
# =========================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[self.pos]

    def advance(self):
        self.pos += 1
        self.current = self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def eat(self, token_type):
        if self.current.type == token_type:
            self.advance()
        else:
            raise ParserError(
                f"Expected {token_type}, got {self.current.type}",
                self.current.line,
                self.current.column
            )

    def peek(self):
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None

    # =========================
    # ENTRY
    # =========================
    def parse(self):
        statements = []
        while self.current.type != TokenType.EOF:
            statements.append(self.statement())
        return Program(statements)

    # =========================
    # STATEMENTS
    # =========================
    def statement(self):
        if self.current.type == TokenType.LET:
            return self.var_decl()
        elif self.current.type == TokenType.PRINT:
            return self.print_stmt()
        elif self.current.type == TokenType.IF:
            return self.if_stmt()
        elif self.current.type == TokenType.WHILE:
            return self.while_stmt()
        elif self.current.type == TokenType.FOR:
            return self.for_stmt()
        elif self.current.type == TokenType.RETURN:
            return self.return_stmt()
        elif self.current.type == TokenType.FUNC:
            return self.function_decl()
        elif self.current.type == TokenType.CLASS:
            return self.class_decl()
        elif self.current.type == TokenType.IMPORT:
            return self.import_stmt()
        elif self.current.type == TokenType.IDENTIFIER:
            if self.peek() and self.peek().type == TokenType.EQUAL:
                return self.assignment()
            else:
                expr = self.expression()
                if isinstance(expr, Variable):
                    return expr
                return ExpressionStatement(expr)
        else:
            raise ParserError(
                f"Unexpected statement {self.current.type}",
                self.current.line,
                self.current.column
            )


    def print_stmt(self):
        self.eat(TokenType.PRINT)
        value = self.expression()
        return Print(value)
    
    def return_stmt(self):
        self.eat(TokenType.RETURN)
        value = self.expression()
        return Return(value)
    
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

    # =========================
    # FUNCTION DECL
    # =========================
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

        return_type = str(self.current.value)
        self.eat(TokenType.IDENTIFIER)

        body = self.block()
        return Function(name, params, return_type, body)

    def parameter(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.COLON)

        if self.current.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            t = "[" + self.current.value + "]"
            self.eat(TokenType.IDENTIFIER)
            self.eat(TokenType.RBRACKET)
        else:
            t = self.current.value
            self.eat(TokenType.IDENTIFIER)

        return {"name": name, "type": str(t)}

    # =========================
    # CLASS / IMPORT
    # =========================
    def class_decl(self):
        self.eat(TokenType.CLASS)
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        return ClassDecl(name, self.block())

    def import_stmt(self):
        self.eat(TokenType.IMPORT)
        module = self.current.value
        self.eat(TokenType.IDENTIFIER)
        return Import(module)

    # =========================
    # BLOCK
    # =========================
    def block(self):
        statements = []
        self.eat(TokenType.LBRACE)

        while self.current.type not in (TokenType.RBRACE, TokenType.EOF):
            statements.append(self.statement())

        self.eat(TokenType.RBRACE)
        return statements

    # =========================
    # FOR LOOP FIXED
    # =========================
    def for_stmt(self):
        self.eat(TokenType.FOR)
        var = self.current.value
        self.eat(TokenType.IDENTIFIER)

        if self.current.type != TokenType.IN:
            raise ParserError("Expected 'in'", self.current.line, self.current.column)

        self.eat(TokenType.IN)

        iterable = self.expression()
        body = self.block()

        return For(var, iterable, body)

    # =========================
    # EXPRESSIONS (FIXED CHAINING)
    # =========================
    def primary(self):
        token = self.current

# UNARY MINUS
        if token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            if self.current.type == TokenType.FLOAT:
                val = self.current.value
                self.eat(TokenType.FLOAT)
                return FloatNode(-val)
            elif self.current.type == TokenType.NUMBER:
                val = self.current.value
                self.eat(TokenType.NUMBER)
                return Number(-val)
            else:
                raise ParserError("Expected a number after '-'", token.line, token.column)
            
        # literals
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(token.value)

        if token.type == TokenType.FLOAT:
            self.eat(TokenType.FLOAT)
            return FloatNode(token.value)

        if token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            return StringNode(token.value)

        if token.type == TokenType.TRUE:
            self.eat(TokenType.TRUE)
            return BoolNode(True)

        if token.type == TokenType.FALSE:
            self.eat(TokenType.FALSE)
            return BoolNode(False)

        # IDENTIFIER CHAINING FIX
        if token.type == TokenType.IDENTIFIER:
            node = Variable(token.value)
            self.eat(TokenType.IDENTIFIER)

            while True:

                # CALL
                if self.current.type == TokenType.LPAREN:
                    self.eat(TokenType.LPAREN)

                    args = []
                    if self.current.type != TokenType.RPAREN:
                        args.append(self.expression())
                        while self.current.type == TokenType.COMMA:
                            self.eat(TokenType.COMMA)
                            args.append(self.expression())

                    self.eat(TokenType.RPAREN)

                    if isinstance(node, MemberAccess):
                        call = Call(node.member, args)
                        call.object = node.object
                        node = call
                    else:
                        node = Call(node.name, args)

                # INDEX
                elif self.current.type == TokenType.LBRACKET:
                    self.eat(TokenType.LBRACKET)
                    index = self.expression()
                    self.eat(TokenType.RBRACKET)
                    node = ArrayIndex(node, index)

                # MEMBER ACCESS
                elif self.current.type == TokenType.DOT:
                    self.eat(TokenType.DOT)
                    member = self.current.value
                    self.eat(TokenType.IDENTIFIER)
                    node = MemberAccess(node, member)

                else:
                    break

            return node

        # grouping
        if token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
            return node

        # array
        if token.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            elements = []

            if self.current.type != TokenType.RBRACKET:
                elements.append(self.expression())
                while self.current.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    elements.append(self.expression())

            self.eat(TokenType.RBRACKET)
            return ArrayLiteral(elements)

        raise ParserError(f"Unexpected {token.type}", token.line, token.column)

    # =========================
    # EXPRESSIONS WRAPPER
    # =========================
    def expression(self, precedence=0):
        left = self.primary()

        # Fix: Removed 'self.' from PRECEDENCE
        while self.current.type in PRECEDENCE and PRECEDENCE[self.current.type] > precedence:

            op = self.current
            self.advance()

            # Fix: Removed 'self.' from PRECEDENCE
            right = self.expression(PRECEDENCE[op.type] + 1)

            left = BinaryOp(left, op.type, right)

        return left
    
    def assignment(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUAL)
        value = self.expression()
        return Assignment(name, value)
    
    def var_decl(self):
        """Parses a variable declaration: let name: type = value"""
        self.eat(TokenType.LET)
        
        # 1. Get the variable name
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)

        # 2. Get the type annotation (e.g., ': int' or ': [float]')
        type_annotation = None
        if self.current.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            if self.current.type == TokenType.LBRACKET:
                self.eat(TokenType.LBRACKET)
                type_annotation = f"[{self.current.value}]"
                self.eat(TokenType.IDENTIFIER)
                self.eat(TokenType.RBRACKET)
            else:
                type_annotation = str(self.current.value)
                self.eat(TokenType.IDENTIFIER)

        # 3. Get the value
        self.eat(TokenType.EQUAL)
        value = self.expression()

        return VarDecl(name, type_annotation, value)