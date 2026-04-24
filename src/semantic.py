from parser import (
    AST, Number, Variable, BinaryOp, VarDecl, Assignment, Print,
    If, While, Return, Call, Function, ArrayLiteral, ArrayIndex, Program
)

NUMERIC_TYPES = ("int", "float")
CONDITION_TYPES = ("bool", "int")
_MISSING = object()


class SymbolTable:
    """Manages scoped symbol resolution for variables and functions."""

    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, name, symbol):
        """Define a new symbol in current scope."""
        self.symbols[name] = symbol

    def lookup(self, name):
        """Look up a symbol, searching parent scopes if not found."""
        scope = self
        while scope is not None:
            symbol = scope.symbols.get(name, _MISSING)
            if symbol is not _MISSING:
                return symbol
            scope = scope.parent
        return None

    def enter_scope(self):
        """Create and return a new child scope."""
        return SymbolTable(parent=self)


class Symbol:
    """Base class for all symbols."""
    def __init__(self, name, type_):
        self.name = name
        self.type = type_


class VariableSymbol(Symbol):
    """Represents a variable in the symbol table."""
    def __init__(self, name, type_):
        super().__init__(name, type_)


class FunctionSymbol(Symbol):
    """Represents a function in the symbol table."""
    def __init__(self, name, return_type, param_types=None):
        super().__init__(name, return_type)
        self.param_types = param_types or []


class SemanticAnalyzer:
    """Performs semantic analysis and type checking on the AST."""

    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.current_function = None
        self.errors = []

    def analyze(self, ast):
        """Run semantic analysis on the AST."""
        print("   -> [Analyzer is checking rules...]")

        # First pass: collect all function declarations
        self._collect_functions(ast)

        # Second pass: analyze all statements with type checking
        self.visit(ast)

        if self.errors:
            print("\n   [!] Semantic Analysis FAILED:")
            for error in self.errors:
                print(f"       - {error}")
            raise Exception("Semantic analysis failed")

        print("   -> [Type checking passed]")

    def _collect_functions(self, node):
        """First pass: collect function declarations before analyzing bodies."""
        if isinstance(node, Program):
            for stmt in node.statements:
                if isinstance(stmt, Function):
                    func_symbol = FunctionSymbol(
                        stmt.name,
                        stmt.return_type or "void",
                        []  # Will support parameters later
                    )
                    self.global_scope.define(stmt.name, func_symbol)

    def visit(self, node):
        """Visit a node and perform type checking."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        """Default visitor for nodes without specific handlers."""
        if isinstance(node, AST):
            for attr_name, attr_value in node.__dict__.items():
                if isinstance(attr_value, AST):
                    self.visit(attr_value)
                elif isinstance(attr_value, list):
                    for item in attr_value:
                        if isinstance(item, AST):
                            self.visit(item)

    def visit_Program(self, node):
        """Analyze a program node."""
        for stmt in node.statements:
            self.visit(stmt)

    def _visit_block_in_child_scope(self, statements):
        self.current_scope = self.current_scope.enter_scope()
        try:
            for stmt in statements:
                self.visit(stmt)
        finally:
            self.current_scope = self.current_scope.parent

    def visit_Function(self, node):
        """Analyze a function declaration."""
        old_function = self.current_function
        self.current_function = node
        try:
            self._visit_block_in_child_scope(node.body)
        finally:
            self.current_function = old_function

    def visit_VarDecl(self, node):
        """Analyze a variable declaration with type checking."""
        # Analyze the initializer expression
        expr_type = self.visit(node.value)

        # Get declared type
        declared_type = node.type_annotation

        # Type check: ensure initializer matches declared type
        if expr_type and declared_type:
            if not self._types_compatible(declared_type, expr_type):
                self.errors.append(
                    f"Type mismatch: variable '{node.name}' declared as '{declared_type}' "
                    f"but initialized with '{expr_type}'"
                )

        # Define variable in current scope
        var_symbol = VariableSymbol(node.name, declared_type)
        self.current_scope.define(node.name, var_symbol)

        return declared_type

    def visit_Assignment(self, node):
        """Analyze an assignment statement."""
        # Look up the variable
        var_symbol = self.current_scope.lookup(node.name)
        if not var_symbol:
            self.errors.append(f"Undefined variable: '{node.name}'")
            return None

        # Analyze the value expression
        expr_type = self.visit(node.value)

        # Type check assignment
        if var_symbol.type and expr_type:
            if not self._types_compatible(var_symbol.type, expr_type):
                self.errors.append(
                    f"Cannot assign '{expr_type}' to variable '{node.name}' of type '{var_symbol.type}'"
                )

        return var_symbol.type

    def visit_Print(self, node):
        """Analyze a print statement."""
        self.visit(node.value)
        return None

    def visit_If(self, node):
        """Analyze an if statement."""
        # Check condition type
        cond_type = self.visit(node.condition)
        if cond_type and cond_type not in CONDITION_TYPES:
            self.errors.append(
                f"If condition must be bool or int, got '{cond_type}'"
            )

        # Analyze then/else branches
        self._visit_block_in_child_scope(node.body)

        if node.else_body:
            self._visit_block_in_child_scope(node.else_body)

        return None

    def visit_While(self, node):
        """Analyze a while loop."""
        # Check condition type
        cond_type = self.visit(node.condition)
        if cond_type and cond_type not in CONDITION_TYPES:
            self.errors.append(
                f"While condition must be bool or int, got '{cond_type}'"
            )

        # Analyze loop body
        self._visit_block_in_child_scope(node.body)

        return None

    def visit_Return(self, node):
        """Analyze a return statement."""
        if node.value is None:
            return None  # Void return

        return_type = self.visit(node.value)

        if self.current_function:
            expected_type = self.current_function.return_type or "void"
            if expected_type == "void" and return_type:
                self.errors.append(
                    f"Function '{self.current_function.name}' has void return type "
                    f"but return statement has value of type '{return_type}'"
                )
            elif expected_type != "void" and not return_type:
                self.errors.append(
                    f"Function '{self.current_function.name}' returns '{expected_type}' "
                    f"but return statement has no value"
                )
            elif expected_type and return_type and not self._types_compatible(expected_type, return_type):
                self.errors.append(
                    f"Cannot return '{return_type}' from function with return type '{expected_type}'"
                )

        return return_type

    def visit_Call(self, node):
        """Analyze a function call."""
        # Look up the function
        func_symbol = self.current_scope.lookup(node.name)
        if not func_symbol:
            self.errors.append(f"Undefined function: '{node.name}'")
            return None

        if not isinstance(func_symbol, FunctionSymbol):
            self.errors.append(f"'{node.name}' is not a function")
            return None

        # Check argument count (when we support parameters)
        # For now, just analyze arguments
        for arg in node.args:
            self.visit(arg)

        return func_symbol.type

    def visit_BinaryOp(self, node):
        """Analyze a binary operation with type checking."""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        # Type check binary operations
        if left_type and right_type:
            op_name = node.op.name

            # Arithmetic operations require numeric types
            if op_name in ("PLUS", "MINUS", "MULTIPLY", "DIVIDE"):
                if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                    self.errors.append(
                        f"Arithmetic operator '{op_name}' requires numeric operands, "
                        f"got '{left_type}' and '{right_type}'"
                    )
                # Return type is the more general type
                return "float" if "float" in (left_type, right_type) else "int"

            # Comparison operations
            elif op_name in ("GREATER", "LESS"):
                if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                    self.errors.append(
                        f"Comparison operator '{op_name}' requires numeric operands, "
                        f"got '{left_type}' and '{right_type}'"
                    )
                return "bool"

        return None

    def visit_Number(self, node):
        """Analyze a number literal."""
        return "int"

    def visit_Variable(self, node):
        """Analyze a variable reference."""
        var_symbol = self.current_scope.lookup(node.name)
        if not var_symbol:
            self.errors.append(f"Undefined variable: '{node.name}'")
            return None
        return var_symbol.type

    def visit_ArrayLiteral(self, node):
        """Analyze an array literal."""
        if not node.elements:
            return "[any]"

        # Check all elements have the same type
        element_type = self.visit(node.elements[0])
        for i, elem in enumerate(node.elements[1:], 1):
            elem_type = self.visit(elem)
            if elem_type != element_type:
                self.errors.append(
                    f"Array element {i} has type '{elem_type}' but expected '{element_type}'"
                )

        return f"[{element_type}]"

    def visit_ArrayIndex(self, node):
        """Analyze an array indexing operation."""
        var_symbol = self.current_scope.lookup(node.name)
        if not var_symbol:
            self.errors.append(f"Undefined variable: '{node.name}'")
            return None

        # Check index type
        index_type = self.visit(node.index)
        if index_type != "int":
            self.errors.append(
                f"Array index must be int, got '{index_type}'"
            )

        # Extract element type from array type
        arr_type = var_symbol.type
        if arr_type and arr_type.startswith("[") and arr_type.endswith("]"):
            return arr_type[1:-1]  # Extract inner type
        else:
            self.errors.append(f"Cannot index non-array variable '{node.name}'")
            return None

    def _types_compatible(self, expected, actual):
        """Check if two types are compatible."""
        if expected == actual:
            return True

        # int can be used where float is expected
        if expected == "float" and actual == "int":
            return True

        # Array type matching
        if expected.startswith("[") and actual.startswith("["):
            expected_inner = expected[1:-1]
            actual_inner = actual[1:-1]
            return self._types_compatible(expected_inner, actual_inner)

        return False
