from tokens import TokenType
from parser import (
    Program, VarDecl, Assignment, BinaryOp, Number, Variable, Print,
    If, While, Function, Return, ArrayLiteral, ArrayIndex,
    FloatNode, Call, StringNode, BoolNode, For,
    ClassDecl, MemberAccess, Import, ExpressionStatement,
)
from errors import SemanticError
from error_list import ErrorReporter


# -----------------------------
# TYPES
# -----------------------------
SEMANTIC_TYPES = {
    "int": "int",
    "float": "float",
    "string": "string",
    "bool": "bool",
    "read": "string",
    "write": "void",
}

BUILTINS = {
    "range": "range",
    "print": "void",
    "len": "int",
}

def normalize_type(t):
    if isinstance(t, dict):
        return t.get("type")
    return t

# -----------------------------
# HELPERS
# -----------------------------
def is_array_type(t):
    return isinstance(t, str) and t.startswith("[") and t.endswith("]")


def get_array_inner(t):
    return t[1:-1] if is_array_type(t) else None


# -----------------------------
# SYMBOL TABLE
# -----------------------------
class SymbolTable:
    def __init__(self, errors):
        self.scopes = [{}]
        self.errors = errors

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, var_type):
        if name in self.scopes[-1]:
            self.errors.add(SemanticError(f"Variable '{name}' already declared"))
            return

        self.scopes[-1][name] = {
            "type": var_type,
            "mutable": True
        }

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                value = scope[name]
                return value["type"] if isinstance(value, dict) else value

        self.errors.add(SemanticError(f"Variable '{name}' not declared"))
        return None


# -----------------------------
# SEMANTIC ANALYZER
# -----------------------------
class SemanticAnalyzer:
    def __init__(self):
        self.errors = ErrorReporter()
        self.symbol_table = SymbolTable(self.errors)
        self.class_table = {}
        self.module_table = {}
        self.in_function = False
        self.current_return_type = None

    def analyze(self, ast):
        self.visit(ast)

        if self.errors.has_errors():
            self.errors.print_errors()
        else:
            print("   -> Semantic analysis passed successfully")

    # -----------------------------
    # VISITOR
    # -----------------------------
    def visit(self, node):
        if isinstance(node, Program):
            return self.visit_program(node)

        elif isinstance(node, VarDecl):
            return self.visit_var_decl(node)

        elif isinstance(node, Assignment):
            return self.visit_assignment(node)

        elif isinstance(node, BinaryOp):
            return self.visit_binary_op(node)

        elif isinstance(node, Number):
            return "int"

        elif isinstance(node, FloatNode):
            return "float"

        elif isinstance(node, StringNode):
            return "string"

        elif isinstance(node, BoolNode):
            return "bool"

        elif isinstance(node, Variable):
            return self.symbol_table.lookup(node.name)

        elif isinstance(node, Print):
            self.visit(node.value)
            return None

        elif isinstance(node, If):
            return self.visit_if(node)

        elif isinstance(node, While):
            return self.visit_while(node)

        elif isinstance(node, For):
            return self.visit_for(node)

        elif isinstance(node, Function):
            return self.visit_function(node)

        elif isinstance(node, Return):
            value_type = self.visit(node.value)

            if self.in_function and value_type != self.current_return_type:
                self.errors.add(SemanticError(
                    f"Return type mismatch: expected {self.current_return_type} got {value_type}"
                ))

            return value_type

        elif isinstance(node, Call):
            return self.visit_call(node)

        elif isinstance(node, ArrayLiteral):
            return self.visit_array_literal(node)

        elif isinstance(node, ArrayIndex):
            array_type = self.visit(node.array)
            if not is_array_type(array_type):
                self.errors.add(SemanticError("Not an array"))
                return None

            index_type = self.visit(node.index)
            if index_type != "int":
                self.errors.add(SemanticError("Array index must be int"))
                return None

            return get_array_inner(array_type)

        elif isinstance(node, ClassDecl):
            return self.visit_class(node)

        elif isinstance(node, MemberAccess):
            return self.visit_member_access(node)

        elif isinstance(node, ExpressionStatement):
            return self.visit(node.expression)
        
        elif isinstance(node, list):
            for stmt in node:
                self.visit(stmt)

        return None

    # -----------------------------
    # PROGRAM
    # -----------------------------
    def visit_program(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    # -----------------------------
    # VAR DECL
    # -----------------------------
    def visit_var_decl(self, node):
        var_type = normalize_type(node.type_annotation)
        value_type = self.visit(node.value)

        if var_type is None:
            self.symbol_table.declare(node.name, value_type)
            return

        if var_type != value_type:
            self.errors.add(SemanticError(
                f"Type mismatch: expected {var_type} but got {value_type}"
            ))
            return

        self.symbol_table.declare(node.name, var_type)

    # -----------------------------
    # ASSIGNMENT
    # -----------------------------
    def visit_assignment(self, node):
        var_type = normalize_type(self.symbol_table.lookup(node.name))
        value_type = self.visit(node.value)

        if var_type != value_type:
            self.errors.add(SemanticError(
                f"Type mismatch in assignment: {var_type} vs {value_type}"
            ))

    # -----------------------------
    # BINARY OP
    # -----------------------------
    def visit_binary_op(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if left is None or right is None:
            return None

        if left != right:
            self.errors.add(SemanticError(f"Type mismatch: {left} vs {right}"))
            return None

        if node.op in (TokenType.PLUS, TokenType.MINUS,
                       TokenType.MULTIPLY, TokenType.DIVIDE):
            if left not in ("int", "float"):
                self.errors.add(SemanticError("Invalid arithmetic types"))
                return None
            return left

        if node.op in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
            return "bool"

        self.errors.add(SemanticError("Unknown operator"))
        return None

    # -----------------------------
    # IF / WHILE
    # -----------------------------
    def visit_if(self, node):
        if self.visit(node.condition) != "bool":
            self.errors.add(SemanticError("If condition must be bool"))

        self.symbol_table.enter_scope()
        self.visit(node.body)
        self.symbol_table.exit_scope()

        if node.else_body:
            self.symbol_table.enter_scope()
            self.visit(node.else_body)
            self.symbol_table.exit_scope()

    def visit_while(self, node):
        if self.visit(node.condition) != "bool":
            self.errors.add(SemanticError("While condition must be bool"))

        self.symbol_table.enter_scope()
        self.visit(node.body)
        self.symbol_table.exit_scope()

    # -----------------------------
    # FOR
    # -----------------------------
    def visit_for(self, node):
        self.symbol_table.enter_scope()

        iterable = self.visit(node.iterable)

        if iterable == ("range", "int"):
            self.symbol_table.declare(node.var, "int")

        elif is_array_type(iterable):
            self.symbol_table.declare(node.var, get_array_inner(iterable))

        else:
            self.errors.add(SemanticError(f"Invalid iterable type: {iterable}"))
            return

        for stmt in node.body:
            self.visit(stmt)

        self.symbol_table.exit_scope()

    # -----------------------------
    # FUNCTION
    # -----------------------------
    def visit_function(self, node):
        self.symbol_table.declare(node.name, {
            "type": "function",
            "return": node.return_type,
            "params": node.params
        })

        self.symbol_table.enter_scope()
        self.in_function = True
        self.current_return_type = node.return_type

        for p in node.params:
            self.symbol_table.declare(p["name"], p["type"])

        self.visit(node.body)

        self.symbol_table.exit_scope()
        self.in_function = False
        self.current_return_type = None

    # -----------------------------
    # CALLS (FIXED & CLEAN)
    # -----------------------------
    def visit_call(self, node):

        func = self.symbol_table.lookup(node.name)

        # function call
        if isinstance(func, dict) and func.get("type") == "function":
            params = func["params"]

            if len(params) != len(node.args):
                self.errors.add(SemanticError("Argument count mismatch"))
                return func["return"]

            for i in range(len(params)):
                arg_type = self.visit(node.args[i])
                if arg_type != params[i]["type"]:
                    self.errors.add(SemanticError(
                        f"Argument type mismatch: expected {params[i]['type']} got {arg_type}"
                    ))

            return func["return"]

        # class constructor
        if node.name in self.class_table:
            for a in node.args:
                self.visit(a)
            return node.name

        # builtins
        if node.name in BUILTINS:
            for a in node.args:
                self.visit(a)
            return BUILTINS[node.name]

        return self.symbol_table.lookup(node.name)

    # -----------------------------
    # ARRAY
    # -----------------------------
    def visit_array_literal(self, node):
        if not node.elements:
            return "[any]"

        t = self.visit(node.elements[0])

        for e in node.elements:
            if self.visit(e) != t:
                self.errors.add(SemanticError("Array type mismatch"))
                return None

        return f"[{t}]"

    # -----------------------------
    # CLASS
    # -----------------------------
    def visit_class(self, node):
        if node.name in self.class_table:
            self.errors.add(SemanticError("Duplicate class"))
            return

        fields = {}
        methods = {}

        for m in node.body:
            if isinstance(m, VarDecl):
                fields[m.name] = m.type_annotation
            elif isinstance(m, Function):
                methods[m.name] = {
                    "params": m.params,
                    "return": m.return_type
                }

        self.class_table[node.name] = {
            "fields": fields,
            "methods": methods
        }

        self.symbol_table.enter_scope()
        for m in node.body:
            self.visit(m)
        self.symbol_table.exit_scope()

    # -----------------------------
    # MEMBER ACCESS
    # -----------------------------
    def visit_member_access(self, node):
        obj = self.visit(node.object)

        if obj not in self.class_table:
            self.errors.add(SemanticError("Not a class instance"))
            return None

        cls = self.class_table[obj]

        if node.member in cls["fields"]:
            return cls["fields"][node.member]

        if node.member in cls["methods"]:
            return cls["methods"][node.member]["return"]

        self.errors.add(SemanticError("Invalid member"))
        return None