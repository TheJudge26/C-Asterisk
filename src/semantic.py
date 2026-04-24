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
)

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name, var_type):
        if name in self.scopes[-1]:
            raise Exception(f"Variable '{name}' already declared")
        self.scopes[-1][name] = var_type

    def assign(self, name, var_type):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = var_type
                return
        raise Exception(f"Variable '{name}' not declared")

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"Variable '{name}' not declared")

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()

    def analyze(self, ast):
        self.visit(ast)
        print("   -> [Analyzer is checking rules...]")

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
        elif isinstance(node, Function):
            return self.visit_function(node)
        elif isinstance(node, Return):
            return self.visit(node.value)
        elif isinstance(node, Call):
            return self.visit_call(node)
        elif isinstance(node, ArrayLiteral):
            return self.visit_array_literal(node)
        elif isinstance(node, ArrayIndex):
            return self.visit_array_index(node)
        elif isinstance(node, list):
            for stmt in node:
                self.visit(stmt)
        else:
            raise Exception(f"Unknown node: {node}")
        
    def visit_program(self, node):
        for stmt in node.statements:
            self.visit(stmt) 
            
    def visit_var_decl(self, node):
        var_type = node.type_annotation
        value_type = self.visit(node.value)
        if var_type != value_type:
            raise Exception(f"Type mismatch in declaration of {node.name}")
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

        if left_type == right_type and (left_type == "int" or left_type == "float"):
            # If the operation is a comparison, the result is ALWAYS an int (0 or 1)
            if node.op in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
                return "int"
            return left_type

        raise Exception(f"Invalid binary operation: {left_type} {node.op} {right_type}")  

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

    def visit_function(self, node):
        self.symbol_table.declare(node.name, node.return_type) 
        self.symbol_table.enter_scope()
        for param in node.params:
            self.symbol_table.declare(param['name'], param['type'])
        self.visit(node.body)
        self.symbol_table.exit_scope()

    def visit_call(self, node):
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