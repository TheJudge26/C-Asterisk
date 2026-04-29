from enum import Enum

class TokenType(Enum):
    # Core Keywords (Level 1-4)
    LET          = "LET"
    PRINT        = "PRINT"
    IF           = "IF"
    ELSE         = "ELSE"
    WHILE        = "WHILE"
    FUNC         = "FUNC"
    RETURN       = "RETURN"
    
    # Milestone 1: Booleans (Level 6)
    TRUE         = "TRUE"
    FALSE        = "FALSE"
    BOOL_TYPE    = "BOOL"
    
    # Identifiers & Literals
    IDENTIFIER   = "IDENTIFIER"
    NUMBER       = "NUMBER"
    FLOAT        = "FLOAT"
    
    # Operators (Level 1-4)
    PLUS         = "+"
    MINUS        = "-"
    MULTIPLY     = "*"
    DIVIDE       = "/"
    EQUAL        = "="
    EQUAL_EQUAL  = "=="
    GREATER      = ">"
    LESS         = "<"
    
    # Punctuation & Brackets (Level 4-5)
    LPAREN       = "("
    RPAREN       = ")"
    LBRACE       = "{"
    RBRACE       = "}"
    LBRACKET     = "["
    RBRACKET     = "]"
    COLON        = ":"
    COMMA        = ","
    ARROW        = "->"
    EOF          = "EOF"

class Token:
    """A single lexical unit with its type, value, and source location."""
    def __init__(self, type: TokenType, value=None, line: int = 0, column: int = 0):
        self.type   = type
        self.value  = value
        self.line   = line
        self.column = column

    def __repr__(self):
        # Professional representation for debugging
        return f"Token({self.type.name}, value={self.value!r}, line={self.line}, col={self.column})"