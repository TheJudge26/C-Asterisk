from enum import Enum

class TokenType(Enum):
    LET = "LET"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    FLOAT = "FLOAT"
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUAL = "="
    EQUAL_EQUAL = "=="  # <--- NEW: For comparisons (if x == 1.0)
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
    
    # NEW TOKENS
    COLON = ":"
    COMMA = ","
    LBRACKET = "["
    RBRACKET = "]"
    ARROW = "->"

class Token:
    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"{self.type} : {self.value}"