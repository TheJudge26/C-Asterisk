"""
semantic.py — Type-checking / scope-resolution pass for C*.

Level 6 Updates:
1. Added validation for the 'bool' primitive type.
2. Added visitor for Boolean nodes.
3. Updated BinaryOp to return 'bool' for comparisons (>, <, ==).
4. Preserved Level 5 N-D array/tensor logic and math built-ins.
"""

from tokens import TokenType
from parser import (
    Program, VarDecl, Assignment, BinaryOp, Number, FloatNode, Boolean,
    Variable, Print, If, While, Return, Function, Call,
    ArrayIndex, ArrayLiteral,
)


class SemanticError(Exception):
    pass


# ═══════════════════════════════════════════════════════════════════
#  Symbol table (lexically-scoped)
# ═══════════════════════════════════════════════════════════════════

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]          # stack; index 0 = global scope

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name: str, var_type: str):
        if name in self.scopes[-1]:
            raise SemanticError(f"Variable '{name}' is already declared in this scope.")
        self.scopes[-1][name] = var_type

    def lookup(self, name: str) -> str:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise SemanticError(f"Variable '{name}' is not declared.")

    def assign(self, name: str, new_type: str):
        """Check that an assignment is type-safe."""
        existing = self.lookup(name)
        if existing != new_type:
            # ALLOW WIDENING: Permit int to be assigned to a float
            if existing == "float" and new_type == "int":
                return
            raise SemanticError(
                f"Type mismatch on assignment to '{name}': "
                f"expected '{existing}', got '{new_type}'."
            )
            


# ═══════════════════════════════════════════════════════════════════
#  Semantic analyser
# ═══════════════════════════════════════════════════════════════════

_MATH_BUILTINS = {"sqrt", "exp"}     # always return float


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()

    # ---------------------------------------------------------------- public

    def analyze(self, ast: Program):
        self._visit(ast)
        print("   -> [Semantic Analyzer: all checks passed ✓]")

    # ---------------------------------------------------------------- dispatcher

    def _visit(self, node):
        if node is None:
            return None
        method_name = f"_visit_{type(node).__name__}"
        method      = getattr(self, method_name, self._visit_list_or_raise)
        return method(node)

    def _visit_list_or_raise(self, node):
        if isinstance(node, list):
            results = [self._visit(s) for s in node]
            return results[-1] if results else None
        raise SemanticError(f"No semantic rule for node type '{type(node).__name__}'")

    # ---------------------------------------------------------------- nodes

    def _visit_Program(self, node: Program):
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_VarDecl(self, node: VarDecl):
        val_type = self._visit(node.value)
        if node.type_annotation != val_type:
            # ALLOW WIDENING: let x: float = 5
            if node.type_annotation == "float" and val_type == "int":
                pass
            else:
                raise SemanticError(
                    f"Type mismatch in declaration of '{node.name}': "
                    f"annotated as '{node.type_annotation}', got '{val_type}'."
                )
        self.symbols.declare(node.name, node.type_annotation)

    def _visit_Assignment(self, node: Assignment):
        val_type = self._visit(node.value)
        self.symbols.assign(node.name, val_type)

    def _visit_BinaryOp(self, node: BinaryOp):
        l = self._visit(node.left)
        r = self._visit(node.right)
        
        # 1. Handle Comparisons (Milestone 1)
        if node.op in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
            if l != r and not ({l, r} == {"int", "float"}):
                raise SemanticError(f"Cannot compare different types: '{l}' vs '{r}'.")
            return "bool"
            
        # 2. Handle Math Widening (int + float -> float)
        if l != r:
            if {l, r} == {"int", "float"}:
                return "float"
            raise SemanticError(
                f"Type mismatch in binary operation: '{l}' vs '{r}'."
            )
        return l

    def _visit_Number(self,    node):  return "int"
    def _visit_FloatNode(self, node):  return "float"
    
    # Milestone 1: Boolean literals
    def _visit_Boolean(self,   node):  return "bool"

    def _visit_Variable(self, node: Variable):
        return self.symbols.lookup(node.name)

    def _visit_Print(self, node: Print):
        return self._visit(node.value)

    def _visit_If(self, node: If):
        cond_type = self._visit(node.condition)
        # In Level 6, we prefer formal 'bool' for conditions
        if cond_type not in ("bool", "int"):
            raise SemanticError(f"IF condition must be bool or int, got '{cond_type}'.")
            
        self.symbols.enter_scope()
        self._visit(node.body)
        self.symbols.exit_scope()
        if node.else_body is not None:
            self.symbols.enter_scope()
            self._visit(node.else_body)
            self.symbols.exit_scope()

    def _visit_While(self, node: While):
        cond_type = self._visit(node.condition)
        if cond_type not in ("bool", "int"):
            raise SemanticError(f"WHILE condition must be bool or int, got '{cond_type}'.")
            
        self.symbols.enter_scope()
        self._visit(node.body)
        self.symbols.exit_scope()

    def _visit_Function(self, node: Function):
        # Register the function name in the outer scope
        self.symbols.declare(node.name, node.return_type)
        self.symbols.enter_scope()
        for param in node.params:
            self.symbols.declare(param["name"], param["type"])
        self._visit(node.body)
        self.symbols.exit_scope()

    def _visit_Return(self, node: Return):
        return self._visit(node.value)

    def _visit_Call(self, node: Call):
        if node.name in _MATH_BUILTINS:
            if len(node.args) != 1:
                raise SemanticError(f"'{node.name}' expects exactly 1 argument.")
            self._visit(node.args[0])
            return "float"
        return self.symbols.lookup(node.name)

    def _visit_ArrayLiteral(self, node: ArrayLiteral):
        """Semantic Analysis: Determines the TYPE of the array."""
        if not node.elements: 
            return "[]"
        
        # Get the type of the first element (e.g., "float")
        first_type = self._visit(node.elements[0])
        final_type = first_type
        
        for el in node.elements[1:]:
            el_type = self._visit(el)
            if el_type != final_type:
                # Support implicit widening: [1, 2.5] becomes [float]
                if {final_type, el_type} == {"int", "float"}:
                    final_type = "float"
                else:
                    raise SemanticError(f"Mixed types in array: '{final_type}' vs '{el_type}'.")
        
        return f"[{final_type}]"

    def _visit_ArrayIndex(self, node: ArrayIndex):
        """Preserves Level 5 recursive array indexing."""
        base_type  = self._visit(node.name)
        idx_type   = self._visit(node.index)
        if idx_type != "int":
            raise SemanticError("Array index must be of type 'int'.")
        if not base_type.startswith("["):
            raise SemanticError(
                f"Cannot index into non-array type '{base_type}'."
            )
        # Strip one layer of brackets: "[[float]]" -> "[float]"
        return base_type[1:-1]