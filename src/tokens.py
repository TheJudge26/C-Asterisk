from enum import Enum

class TokenType(Enum):
    LET = "LET"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUAL = "="
    GREATER = ">"
    LESS = "<"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    PRINT = "PRINT"
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    FUNC = "FUNC"
    RETURN = "RETURN"
    EOF = "EOF"

class Token:
    def __init__(self, type, value = None):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"{self.type} : {self.value}"