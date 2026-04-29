from tokens import TokenType # NEW: Added this import
from parser import (
    Program,
    VarDecl,
    Assignment,
    BinaryOp,
    Number,
    Variable,
    Print,
    If,
    While,
    Function,
    Return,
    ArrayLiteral,
    ArrayIndex,
    Parser,
    FloatNode,
    Call, 
    StringNode,
    BoolNode,
    For,
)

SEMANTIC_TYPES = {
    "int": "int",
    "float": "float",
    "string": "string",
    "bool": "bool"
}

BUILTINS = {
    "range": "range",
    "print": "void",
}

def is_array_type(t):
    return isinstance(t, str) and t.startswith("[") and t.endswith("]")

def get_array_inner(t):
    return t[1:-1] if is_array_type(t) else None

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def normalize_type(self, t):
        if isinstance(t, str):
            return t.strip()
        return t

    def declare(self, name, var_type):
        if name in self.scopes[-1]:
            raise Exception(f"Variable '{name}' already declared")
        self.scopes[-1][name] = {
        "type": self.normalize_type(var_type),
        "mutable": True
    }

    def assign(self, name, var_type):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = var_type
                return
        raise Exception(f"Variable '{name}' not declared")

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                value = scope[name]

                if isinstance(value, dict):
                    return value["type"]

                return value

        raise Exception(f"Variable '{name}' not declared")

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()

    def analyze(self, ast):
        self.visit(ast)
        print("   -> [Analyzer is checking rules...]")

    # Added String/Bool
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
        
        elif isinstance(node, Variable):
            return self.symbol_table.lookup(node.name)
        
        elif isinstance(node, Print):
            return self.visit(node.value)
        
        elif isinstance(node, If):
            return self.visit_if(node)
        
        elif isinstance(node, While):
            return self.visit_while(node)
        
        elif isinstance(node, For):
            return self.visit_for(node)
        
        elif isinstance(node, Function):
            return self.visit_function(node)
        
        elif isinstance(node, Return):
            return self.visit(node.value)
        
        elif isinstance(node, Call):
            return self.visit_call(node)
        
        elif isinstance(node, ArrayLiteral):
            return self.visit_array_literal(node)
        
        elif isinstance(node, ArrayIndex):
            array_type = self.symbol_table.lookup(node.name)

            if not is_array_type(array_type):
                raise Exception(f"{node.name} is not an array")

            index_type = self.visit(node.index)

            if index_type != "int":
                raise Exception("Array index must be int")

            return get_array_inner(array_type)
        
        elif isinstance(node, list):
            for stmt in node:
                self.visit(stmt)
        
        elif isinstance(node, StringNode):
            return "string"
        
        elif isinstance(node, BoolNode):
            return "bool"
        
        else:
            raise Exception(f"Unknown node: {node}")
        
    def visit_program(self, node):
        for stmt in node.statements:
            self.visit(stmt) 
            
    def visit_var_decl(self, node):
        var_type = node.type_annotation
        value_type = self.visit(node.value)

        if var_type in SEMANTIC_TYPES:
            pass
        elif isinstance(var_type, str) and var_type.startswith("[") and var_type.endswith("]"):
            inner_type = var_type[1:-1]
            if inner_type not in SEMANTIC_TYPES:
                raise Exception(f"Unknown inner type {inner_type}")
        else:
            raise Exception(f"Unknown type {var_type}")

        if var_type != value_type:
            raise Exception(f"Type mismatch: {var_type} = {value_type}")

        self.symbol_table.declare(node.name, var_type)

    def visit_assignment(self, node):
        var_type = self.symbol_table.lookup(node.name)
        value_type = self.visit(node.value)
        if var_type != value_type:
            raise Exception(f"Type mismatch in assignment to {node.name}") 
        
    # UPDATED: Handles comparison operators
    def visit_binary_op(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if left_type != right_type:
            raise Exception(f"Type mismatch: {left_type} vs {right_type}")

        # arithmetic
        if node.op in (TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE):
            if left_type not in ("int", "float"):
                raise Exception("Arithmetic only allowed on int/float")
            return left_type

        # comparisons
        if node.op in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
            return "bool"

        raise Exception(f"Unknown operator {node.op}")

    def visit_if(self, node):
        self.visit(node.condition)
        self.symbol_table.enter_scope()
        self.visit(node.body)
        self.symbol_table.exit_scope()
        if node.else_body:
            self.symbol_table.enter_scope()
            self.visit(node.else_body)
            self.symbol_table.exit_scope()  

    def visit_while(self, node):
        self.visit(node.condition)
        self.symbol_table.enter_scope()
        self.visit(node.body)
        self.symbol_table.exit_scope()

    def visit_for(self, node):
        self.symbol_table.enter_scope()

        iterable_type = self.visit(node.iterable)

        # CASE 1: range()
        if iterable_type == "range":
            self.symbol_table.declare(node.var, "int")

        # CASE 2: array [int], [float], etc.
        elif isinstance(iterable_type, str) and iterable_type.startswith("["):
            inner = iterable_type[1:-1]
            self.symbol_table.declare(node.var, inner)

        else:
            raise Exception("Invalid type in for-loop")

        for stmt in node.body:
            self.visit(stmt)

        self.symbol_table.exit_scope()
    
    def visit_function(self, node):
        self.symbol_table.declare(node.name, node.return_type) 
        self.symbol_table.enter_scope()
        for param in node.params:
            self.symbol_table.declare(param['name'], param['type'])
        self.visit(node.body)
        self.symbol_table.exit_scope()

    # Cleaner Code/Usage
    def visit_call(self, node):
        if node.name in BUILTINS:
            for arg in node.args:
                self.visit(arg)
            return BUILTINS[node.name]
    
        return_type = self.symbol_table.lookup(node.name)

        for arg in node.args:
            self.visit(arg)

        return return_type

    def visit_array_literal(self, node):
        if not node.elements:
            return "[]"
        first_type = self.visit(node.elements[0])
        for el in node.elements:
            if self.visit(el) != first_type:
                raise Exception("Array elements must have same type")
        return f"[{first_type}]"

    def visit_array_index(self, node):
        array_type = self.symbol_table.lookup(node.name)
        if not array_type.startswith("["):
            raise Exception(f"{node.name} is not an array")
        index_type = self.visit(node.index)
        if index_type != "int":
            raise Exception("Array index must be int")
        return array_type[1:-1]