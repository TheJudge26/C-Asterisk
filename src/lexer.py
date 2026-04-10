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

        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        return Token(TokenType.NUMBER, int(result))
    
    def identifier(self):
        result = ""

        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
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

            if self.current_char.isdigit():
                return self.number()
            
            if self.current_char.isalpha():
                return self.identifier()
            
            if self.current_char == "+":
                self.advance()
                return Token(TokenType.PLUS)
            
            if self.current_char == "-":
                self.advance()
                return Token(TokenType.MINUS)
            
            if self.current_char == "*":
                self.advance()
                return Token(TokenType.MULTIPLY)
            
            if self.current_char == "/":
                self.advance()
                return Token(TokenType.DIVIDE)
            
            if self.current_char == "=":
                self.advance()
                return Token(TokenType.EQUAL)
            
            if self.current_char == ">":
                self.advance()
                return Token(TokenType.GREATER)
            
            if self.current_char == "<":
                self.advance()
                return Token(TokenType.LESS)

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
            
            raise Exception(f"Illegal Character: {self.current_char}")

        return Token(TokenType.EOF)
    
    def tokenize(self):
        tokens = []

        while True:
            token = self.get_next_token()
            tokens.append(token)

            if token.type.name == "EOF":
                break

        return tokens