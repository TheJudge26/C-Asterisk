from tokens import Token, TokenType

KEYWORDS = {
    "let":    TokenType.LET,
    "print":  TokenType.PRINT,
    "if":     TokenType.IF,
    "else":   TokenType.ELSE,
    "while":  TokenType.WHILE,
    "func":   TokenType.FUNC,
    "return": TokenType.RETURN,
    "true":   TokenType.TRUE,
    "false":  TokenType.FALSE,
    "bool":   TokenType.BOOL_TYPE,
}


class LexerError(Exception):
    pass


class Lexer:
    """
    Converts a C* source string into a flat list of Token objects.
    Every token carries its exact line and column for diagnostic messages.
    """

    def __init__(self, text: str):
        self.text    = text
        self.pos     = 0
        self.line    = 1
        self.column  = 1
        self.current = self.text[0] if self.text else None

    # ------------------------------------------------------------------ helpers

    def _advance(self):
        """Move forward one character, updating line/column counters."""
        if self.current == '\n':
            self.line  += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1
        self.current = self.text[self.pos] if self.pos < len(self.text) else None

    def _skip_whitespace(self):
        while self.current is not None and self.current.isspace():
            self._advance()

    def _skip_line_comment(self):
        """Skip from '#' to end-of-line."""
        while self.current is not None and self.current != '\n':
            self._advance()

    # ------------------------------------------------------------------ scanners

    def _scan_number(self) -> Token:
        start_line, start_col = self.line, self.column
        result    = ""
        is_float  = False
        dot_count = 0

        while self.current is not None and (self.current.isdigit() or self.current == '.'):
            if self.current == '.':
                dot_count += 1
                if dot_count > 1:
                    raise LexerError(
                        f"Line {self.line}, Col {self.column}: "
                        "Invalid number — multiple decimal points."
                    )
                is_float = True
            result += self.current
            self._advance()

        tok_type = TokenType.FLOAT if is_float else TokenType.NUMBER
        tok_val  = float(result)   if is_float else int(result)
        return Token(tok_type, tok_val, start_line, start_col)

    def _scan_identifier_or_keyword(self) -> Token:
        start_line, start_col = self.line, self.column
        result = ""

        while self.current is not None and (self.current.isalnum() or self.current == '_'):
            result += self.current
            self._advance()

        tok_type = KEYWORDS.get(result, TokenType.IDENTIFIER)
        return Token(tok_type, result, start_line, start_col)

    # ------------------------------------------------------------------ public API

    def get_next_token(self) -> Token:
        while self.current is not None:

            # ---- whitespace
            if self.current.isspace():
                self._skip_whitespace()
                continue

            # ---- line comment
            if self.current == '#':
                self._skip_line_comment()
                continue

            # ---- numbers
            if self.current.isdigit():
                return self._scan_number()

            # ---- identifiers / keywords
            if self.current.isalpha() or self.current == '_':
                return self._scan_identifier_or_keyword()

            # ---- single / double character operators & punctuation
            ch  = self.current
            ln  = self.line
            col = self.column

            if ch == '+':  self._advance(); return Token(TokenType.PLUS,     None, ln, col)
            if ch == '*':  self._advance(); return Token(TokenType.MULTIPLY,  None, ln, col)
            if ch == '/':  self._advance(); return Token(TokenType.DIVIDE,    None, ln, col)
            if ch == '(':  self._advance(); return Token(TokenType.LPAREN,    None, ln, col)
            if ch == ')':  self._advance(); return Token(TokenType.RPAREN,    None, ln, col)
            if ch == '{':  self._advance(); return Token(TokenType.LBRACE,    None, ln, col)
            if ch == '}':  self._advance(); return Token(TokenType.RBRACE,    None, ln, col)
            if ch == '[':  self._advance(); return Token(TokenType.LBRACKET,  None, ln, col)
            if ch == ']':  self._advance(); return Token(TokenType.RBRACKET,  None, ln, col)
            if ch == ':':  self._advance(); return Token(TokenType.COLON,     None, ln, col)
            if ch == ',':  self._advance(); return Token(TokenType.COMMA,     None, ln, col)
            if ch == '>':  self._advance(); return Token(TokenType.GREATER,   None, ln, col)
            if ch == '<':  self._advance(); return Token(TokenType.LESS,      None, ln, col)

            if ch == '-':
                self._advance()
                if self.current == '>':
                    self._advance()
                    return Token(TokenType.ARROW, None, ln, col)
                return Token(TokenType.MINUS, None, ln, col)

            if ch == '=':
                self._advance()
                if self.current == '=':
                    self._advance()
                    return Token(TokenType.EQUAL_EQUAL, None, ln, col)
                return Token(TokenType.EQUAL, None, ln, col)

            # ---- unrecognised character
            self._advance()
            raise LexerError(
                f"Line {ln}, Col {col}: Illegal character {ch!r}"
            )

        return Token(TokenType.EOF, None, self.line, self.column)

    def tokenize(self) -> list:
        tokens = []
        while True:
            tok = self.get_next_token()
            tokens.append(tok)
            if tok.type == TokenType.EOF:
                break
        return tokens