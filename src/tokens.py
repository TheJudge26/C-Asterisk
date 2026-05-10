from enum import Enum

class TokenType(Enum):
    LET = "LET"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOL = "BOOL"
    TRUE = "TRUE"
    FALSE = "FALSE"
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUAL = "="
    EQUAL_EQUAL = "=="      
    NOT_EQUAL = "!="        
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="    
    LESS_EQUAL = "<="       
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
    COLON = ":"
    COMMA = ","
    LBRACKET = "["
    RBRACKET = "]"
    ARROW = "->"
    DOT = "."
    CLASS = "CLASS"
    IMPORT = "IMPORT"
    FROM = "FROM"
    AS = "AS"

class Token:
    def __init__(self, type, value=None, line=None, column=None):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"{self.type} : {self.value} (Line {self.line}, Col {self.column})"