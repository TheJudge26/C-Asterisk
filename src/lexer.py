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

SINGLE_CHAR_TOKENS = {
    "+": TokenType.PLUS,
    "*": TokenType.MULTIPLY,
    "/": TokenType.DIVIDE,
    "=": TokenType.EQUAL,
    ">": TokenType.GREATER,
    "<": TokenType.LESS,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
}

class Lexer:
    def __init__(self, text):
        self.text = text
        self.text_len = len(text)
        self.position = 0
        self.current_char = self.text[self.position] if self.text else None
        
    def advance(self):
        self.position += 1

        if self.position >= self.text_len:
            self.current_char = None
        else:
            self.current_char = self.text[self.position]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        start = self.position
        while self.current_char is not None and self.current_char.isdigit():
            self.advance()
        return Token(TokenType.NUMBER, int(self.text[start:self.position]))
    
    def identifier(self):
        start = self.position
        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            self.advance()

        result = self.text[start:self.position]
        keyword = KEYWORDS.get(result)
        if keyword is not None:
            return Token(keyword, result)

        return Token(TokenType.IDENTIFIER, result)
    
    def get_next_token(self):
        single_char_tokens = SINGLE_CHAR_TOKENS
        while self.current_char is not None:
            current_char = self.current_char

            if current_char.isspace():
                self.skip_whitespace()
                continue

            if current_char.isdigit():
                return self.number()

            if current_char.isalpha():
                return self.identifier()

            if current_char == "+":
                self.advance()
                return Token(TokenType.PLUS)

            if current_char == "-":
                self.advance()
                if self.current_char == ">":
                    self.advance()
                    return Token(TokenType.ARROW)
                return Token(TokenType.MINUS)

            token_type = single_char_tokens.get(current_char)
            if token_type is not None:
                self.advance()
                return Token(token_type)

            raise Exception(f"Illegal Character: {current_char}")

        return Token(TokenType.EOF)
    
    def tokenize(self):
        tokens = []
        append_token = tokens.append

        while True:
            token = self.get_next_token()
            append_token(token)

            if token.type == TokenType.EOF:
                break

        return tokens
