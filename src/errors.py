class CompilerError(Exception):
    def __init__(self, message, line=None, column=None):
        self.line = line
        self.column = column

        # Human-readable message
        if line is not None and column is not None:
            full_message = f"The error is: {message} | Located at Line {line}, Column {column}"
        elif line is not None:
            full_message = f"The error is: {message} | Located at Line {line}"
        else:
            full_message = f"The error is: {message}"

        super().__init__(full_message)

class LexerError(CompilerError):
    pass


class ParserError(CompilerError):
    pass


class SemanticError(CompilerError):
    pass