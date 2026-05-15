from tokens import Token, TokenType
from errors import LexerError

KEYWORDS = {
    "let": TokenType.LET,
    "print": TokenType.PRINT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "func": TokenType.FUNC,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "class": TokenType.CLASS,
    "import": TokenType.IMPORT,
}

SINGLE_CHAR_TOKENS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MULTIPLY,
    "/": TokenType.DIVIDE,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
}


class Lexer:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.current_char = self.text[self.position] if self.text else None

        self.line = 1
        self.column = 1

    def advance(self):
        if self.current_char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        self.position += 1

        if self.position >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.position]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        result = []
        append = result.append
        start_line = self.line
        start_column = self.column

        dot_count = 0

        while self.current_char is not None and (
            self.current_char.isdigit() or self.current_char == "."
        ):
            if self.current_char == ".":
                dot_count += 1
                if dot_count > 1:
                    raise LexerError(
                        "Invalid number: multiple decimal points",
                        self.line,
                        self.column
                    )

            append(self.current_char)
            self.advance()

        value = "".join(result)

        if value == ".":
            raise LexerError("Invalid standalone '.'", start_line, start_column)


        if value.count(".") > 1:
            raise LexerError("Invalid number format", start_line, start_column)

        if dot_count == 1:
            return Token(TokenType.FLOAT, float(value), start_line, start_column)

        return Token(TokenType.NUMBER, int(value), start_line, start_column)

    
    def identifier(self):
        result = []

        start_line = self.line
        start_column = self.column

        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            result.append(self.current_char)
            self.advance()

        value = "".join(result)

        if value in KEYWORDS:
            return Token(KEYWORDS[value], value, start_line, start_column)

        return Token(TokenType.IDENTIFIER, value, start_line, start_column)
        

    
    def string(self):
        result = []
        append = result.append
        start_line = self.line
        start_column = self.column

        self.advance()  

        while self.current_char is not None and self.current_char != '"':
            if self.current_char == "\\":  
                self.advance()
                if self.current_char == '"':
                    append('"')
                elif self.current_char == 'n':
                    append('\n')
                elif self.current_char == '\\':
                    append('\\')
                else:
                    append(self.current_char)
            else:
                append(self.current_char)
            
            self.advance()

        if self.current_char != '"':
            raise LexerError("Unterminated string", self.line, self.column)

        self.advance()  
        return Token(TokenType.STRING, "".join(result), start_line, start_column)

    def get_next_token(self):

        while self.current_char is not None:

            
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == "#":
                while self.current_char is not None and self.current_char != "\n":
                    self.advance()
                continue

            if self.current_char.isdigit():
                return self.number()

            if self.current_char == '"':
                return self.string()
            
            if self.current_char.isalpha() or self.current_char == "_":
                return self.identifier()
            
            if self.current_char in ("=", "!", ">", "<", "-"):
                return self._handle_operators()

            if self.current_char == ".":
                start_line = self.line
                start_column = self.column

                next_char = self.text[self.position + 1] if self.position + 1 < len(self.text) else None

                if next_char is not None and next_char.isdigit():
                    return self.number()

                # prev_char = self.text[self.position - 1] if self.position > 0 else None
                # if prev_char is not None and prev_char.isdigit():
                #     raise LexerError("Invalid number format", start_line, start_column)

                self.advance()
                return Token(TokenType.DOT, ".", start_line, start_column)

            if self.current_char in SINGLE_CHAR_TOKENS:
                tok_type = SINGLE_CHAR_TOKENS[self.current_char]
                start_line = self.line
                start_column = self.column
                value = self.current_char
                self.advance()
                return Token(tok_type, value, start_line, start_column)

            char = self.current_char
            self.advance()
            raise LexerError(f"Illegal character '{char}'", self.line, self.column)

        return Token(TokenType.EOF, None, self.line, self.column)
    
    def _handle_operators(self):

        start_line = self.line
        start_column = self.column

        char = self.current_char
        self.advance()

        if char == "-":
            if self.current_char == ">":
                self.advance()
                return Token(TokenType.ARROW, "->", start_line, start_column)
            return Token(TokenType.MINUS, "-", start_line, start_column)

        if char == "=":
            if self.current_char == "=":
                self.advance()
                return Token(TokenType.EQUAL_EQUAL, "==", start_line, start_column)
            return Token(TokenType.EQUAL, "=", start_line, start_column)

        if char == "!":
            if self.current_char == "=":
                self.advance()
                return Token(TokenType.NOT_EQUAL, "!=", start_line, start_column)
            raise LexerError("Unexpected '!'", self.line, self.column)
       
        if char == ">":
            if self.current_char == "=":
                self.advance()
                return Token(TokenType.GREATER_EQUAL, ">=", start_line, start_column)
            return Token(TokenType.GREATER, ">", start_line, start_column)

        if char == "<":
            if self.current_char == "=":
                self.advance()
                return Token(TokenType.LESS_EQUAL, "<=", start_line, start_column)
            return Token(TokenType.LESS, "<", start_line, start_column)

        raise LexerError(f"Unknown operator '{char}'", self.line, self.column)

    def tokenize(self):
        tokens = []

        while True:
            token = self.get_next_token()
            tokens.append(token)

            if token.type == TokenType.EOF:
                break


        return tokens