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
    Parser
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
        pass


    def analyze(self, ast, node):
        # Node      
        self.visit(node)
        print("   -> [Analyzer is checking rules...]")
        pass 

# Visitor (core engine)

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

        elif isinstance(node, ArrayLiteral):
            return self.visit_array_literal(node)

        elif isinstance(node, ArrayIndex):
            return self.visit_array_index(node)

        elif isinstance(node, list):  # blocks
            for stmt in node:
                self.visit(stmt)

        else:
            raise Exception(f"Unknown node: {node}")
        
# Program root

    def visit_program(self, node):
        for stmt in node.statements:
            self.visit(stmt) 
            
# Variable declaration

    def visit_var_decl(self, node):
        var_type = node.type_annotation

        value_type = self.visit(node.value)

        if var_type != value_type:
            raise Exception(f"Type mismatch in declaration of {node.name}")

        self.symbol_table.declare(node.name, var_type) 

# Assignment

    def visit_assignment(self, node):
        var_type = self.symbol_table.lookup(node.name)
        value_type = self.visit(node.value)

        if var_type != value_type:
            raise Exception(f"Type mismatch in assignment to {node.name}") 
        
# Binary operations        

    def visit_binary_op(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if left_type == "int" and right_type == "int":
            return "int"

        raise Exception("Invalid binary operation")  

# If

    def visit_if(self, node):
        self.visit(node.condition)

        self.symbol_table.enter_scope()
        self.visit(node.body)
        self.symbol_table.exit_scope()

        if node.else_body:
            self.symbol_table.enter_scope()
            self.visit(node.else_body)
            self.symbol_table.exit_scope()  

# While

    def visit_while(self, node):
        self.visit(node.condition)

        self.symbol_table.enter_scope()
        self.visit(node.body)
        self.symbol_table.exit_scope()

# Function

    def visit_function(self, node):
        self.symbol_table.enter_scope()

        self.visit(node.body)

        self.symbol_table.exit_scope()

# Array literal

    def visit_array_literal(self, node):
        if not node.elements:
            return "[]"

        first_type = self.visit(node.elements[0])

        for el in node.elements:
            if self.visit(el) != first_type:
                raise Exception("Array elements must have same type")

        return f"[{first_type}]"

# Array index

    def visit_array_index(self, node):
        array_type = self.symbol_table.lookup(node.name)

        if not array_type.startswith("["):
            raise Exception(f"{node.name} is not an array")

        index_type = self.visit(node.index)
        if index_type != "int":
            raise Exception("Array index must be int")

        return array_type[1:-1]  # return element type

            
