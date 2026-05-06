from enum import Enum

class TokenType(Enum):
    LET = "LET"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    FLOAT = "FLOAT"

    # New String/Bool/For Addition
    STRING = "STRING"
    BOOL = "BOOL"
    TRUE = "TRUE"
    FALSE = "FALSE"

    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUAL = "="
    EQUAL_EQUAL = "=="      # NEW
    NOT_EQUAL = "!="        # NEW
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="    # NEW
    LESS_EQUAL = "<="       # NEW

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

    FOR = "FOR"
    IN = "IN"

    EOF = "EOF"

    # NEW TOKENS
    COLON = ":"
    COMMA = ","
    LBRACKET = "["
    RBRACKET = "]"
    ARROW = "->"

    # NEW: DOT/CLASS/IMPORT/FROM/AS
    DOT = "."
    CLASS = "CLASS"
    IMPORT = "IMPORT"
    FROM = "FROM"
    AS = "AS"

class Token:
    def __init__(self, type, value=None, line=None, column=None):
        self.type = type
        self.value = value
        # NEW: store position for error reporting
        self.line = line
        self.column = column

    def __repr__(self):
        return f"{self.type} : {self.value} (Line {self.line}, Col {self.column})"