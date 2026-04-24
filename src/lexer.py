from tokens import Token, TokenType

KEYWORDS = {
    "let": TokenType.LET,
    "print": TokenType.PRINT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "func": TokenType.FUNC,
    "return": TokenType.RETURN
}

class Lexer:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.current_char = self.text[self.position] if self.text else None
        
    def advance(self):
        self.position += 1
        if self.position >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.position]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        result = ""
        is_float = False

        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                if is_float:
                    raise Exception("Invalid number format: too many decimal points")
                is_float = True
                
            result += self.current_char
            self.advance()

        if is_float:
            return Token(TokenType.FLOAT, float(result))
        return Token(TokenType.NUMBER, int(result))
    
    def identifier(self):
        result = ""
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == "_"):
            result += self.current_char
            self.advance()
        
        if result in KEYWORDS:
            return Token(KEYWORDS[result], result)
        
        return Token(TokenType.IDENTIFIER, result)
    
    def get_next_token(self):
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Check for comments
            if self.current_char == '#':
                while self.current_char is not None and self.current_char != '\n':
                    self.advance()
                continue

            if self.current_char.isdigit():
                return self.number()
            
            if self.current_char.isalpha():
                return self.identifier()
            
            if self.current_char == "+":
                self.advance()
                return Token(TokenType.PLUS)
            
            if self.current_char == "-":
                self.advance()
                if self.current_char == ">":
                    self.advance()
                    return Token(TokenType.ARROW)
                return Token(TokenType.MINUS)
            
            if self.current_char == "*":
                self.advance()
                return Token(TokenType.MULTIPLY)
            
            if self.current_char == "/":
                self.advance()
                return Token(TokenType.DIVIDE)
            
            # UPDATED: Handles both = and ==
            if self.current_char == "=":
                self.advance()
                if self.current_char == "=":
                    self.advance()
                    return Token(TokenType.EQUAL_EQUAL, "==")
                return Token(TokenType.EQUAL, "=")
            
            if self.current_char == ">":
                self.advance()
                return Token(TokenType.GREATER, ">")

            if self.current_char == "<":
                self.advance()
                return Token(TokenType.LESS, "<")

            if self.current_char == "(":
                self.advance()
                return Token(TokenType.LPAREN)

            if self.current_char == ")":
                self.advance()
                return Token(TokenType.RPAREN)
            
            if self.current_char == "{":
                self.advance()
                return Token(TokenType.LBRACE)

            if self.current_char == "}":
                self.advance()
                return Token(TokenType.RBRACE)
            
            if self.current_char == ":":
                self.advance()
                return Token(TokenType.COLON)
                
            if self.current_char == ",":
                self.advance()
                return Token(TokenType.COMMA)
                
            if self.current_char == "[":
                self.advance()
                return Token(TokenType.LBRACKET)
                
            if self.current_char == "]":
                self.advance()
                return Token(TokenType.RBRACKET)

            # If we reach here, the character is unknown
            char = self.current_char
            self.advance() 
            raise Exception(f"Illegal Character: {char}")

        return Token(TokenType.EOF)
    
    def tokenize(self):
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type.name == "EOF":
                break
        return tokens