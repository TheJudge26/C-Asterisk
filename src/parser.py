from tokens import TokenType
from errors import ParserError

class AST:
    pass

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


# expressions

class Variable(AST):
    def __init__(self, name):
        self.name = name


class Call(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.object = None  


class BinaryOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

# statement

class VarDecl(AST):
    def __init__(self, name, type_annotation, value):
        self.name = name
        self.type_annotation = type_annotation
        self.value = value


class Assignment(AST):
    def __init__(self, name, value, target=None):
        self.name = name
        self.value = value
        self.target = target 


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

# function
class Function(AST):
    def __init__(self, name, params, return_type, body):   #->
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body

# array

class ArrayLiteral(AST):
    def __init__(self, elements):
        self.elements = elements


class ArrayIndex(AST):
    def __init__(self, array, index):
        self.array = array
        self.index = index

# program

class Program(AST):
    def __init__(self, statements):
        self.statements = statements

#clases

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

# parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[self.pos]
        self.errors = []

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
    
    def synchronize(self):
        """Panic mode recovery: skip tokens until we hit a safe statement boundary."""
        self.advance()
        while self.current.type != TokenType.EOF:
            
            if self.current.type in (
                TokenType.LET, TokenType.FUNC, TokenType.CLASS, 
                TokenType.IF, TokenType.WHILE, TokenType.FOR, TokenType.RETURN
            ):
                return
            self.advance()

    # entry
    def parse(self):
        statements = []
        while self.current.type != TokenType.EOF:
         try:
                stmt = self.statement()
                if stmt:
                    statements.append(stmt)
         except ParserError as e:
                
                self.errors.append(str(e))
                self.synchronize()
        return Program(statements)

    
    # statements
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
    
            next_token = self.peek()
            if next_token and next_token.type == TokenType.COLON:
                return self.var_decl()
            target = self.expression()
           
            if self.current.type == TokenType.EQUAL:
                self.eat(TokenType.EQUAL)
                value = self.expression()
                
                if type(target).__name__ == "Variable":
                    return Assignment(target.name, value)
                
                return Assignment("memory_overwrite", value, target=target)

            if isinstance(target, Variable):
                return target
            return ExpressionStatement(target)
            


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

    # function decl
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

    # class+import
    
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

    # BLOCK
    
    def block(self):
        statements = []
        self.eat(TokenType.LBRACE)

        while self.current.type not in (TokenType.RBRACE, TokenType.EOF):
            statements.append(self.statement())

        self.eat(TokenType.RBRACE)
        return statements

    # for
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

    # expressions
    def primary(self):
        token = self.current

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

        if token.type == TokenType.IDENTIFIER:
            node = Variable(token.value)
            self.eat(TokenType.IDENTIFIER)

            while True:

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

                elif self.current.type == TokenType.LBRACKET:
                    self.eat(TokenType.LBRACKET)
                    index = self.expression()
                    self.eat(TokenType.RBRACKET)
                    node = ArrayIndex(node, index)

                elif self.current.type == TokenType.DOT:
                    self.eat(TokenType.DOT)
                    member = self.current.value
                    self.eat(TokenType.IDENTIFIER)
                    node = MemberAccess(node, member)

                else:
                    break

            return node

     
        if token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
            return node

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

    # expressions wrap
    
    def expression(self, precedence=0):
        left = self.primary()

        while self.current.type in PRECEDENCE and PRECEDENCE[self.current.type] > precedence:

            op = self.current
            self.advance()
            
            right = self.expression(PRECEDENCE[op.type] + 1)

            left = BinaryOp(left, op.type, right)

        return left
    
    def assignment(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUAL)
        value = self.expression()
        return Assignment(name, value)
    
   
    def parse_type(self):
        """Recursively parses types like int, float, [int], [[float]]."""
        if self.current.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            inner = self.parse_type()
            self.eat(TokenType.RBRACKET)
            return f"[{inner}]"
        else:
            val = self.current.value
            self.eat(TokenType.IDENTIFIER)
            return str(val)

    
    def var_decl(self):
        """Parses a variable declaration: [let] name: type = value"""
        if self.current.type == TokenType.LET:
            self.eat(TokenType.LET)

        name = self.current.value
        self.eat(TokenType.IDENTIFIER)

        type_annotation = None
        if self.current.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            type_annotation = self.parse_type()

        self.eat(TokenType.EQUAL)
        value = self.expression()
        return VarDecl(name, type_annotation, value)