"""
visualizer.py — Pretty-prints a C* AST to stdout using box-drawing characters.
"""

from parser import (
    Program, Function, BinaryOp, VarDecl, Assignment,
    If, While, Call, ArrayIndex, ArrayLiteral,
    Variable, Number, FloatNode, Return, Print,
)


class ASTPrinter:
    def __init__(self):
        self._indent = ""

    def print_node(self, node, label: str = "", is_last: bool = True):
        marker = "└── " if is_last else "├── "
        prefix = f"{label}: " if label else ""

        if node is None:
            print(f"{self._indent}{marker}{prefix}None")
            return

        if isinstance(node, list):
            # Render a block (list of statements) inline
            for i, stmt in enumerate(node):
                self.print_node(stmt, label=label if i == 0 else "", is_last=(i == len(node) - 1))
            return

        node_name = type(node).__name__
        extra     = ""
        if isinstance(node, (Number, FloatNode)):
            extra = f" ({node.value})"
        elif isinstance(node, Variable):
            extra = f" ({node.name})"
        elif isinstance(node, BinaryOp):
            extra = f" ({node.op})"
        elif isinstance(node, (VarDecl, Assignment)):
            extra = f" ({node.name})"
        elif isinstance(node, Function):
            extra = f" ({node.name})"
        elif isinstance(node, Call):
            extra = f" ({node.name})"

        print(f"{self._indent}{marker}{prefix}{node_name}{extra}")

        saved_indent  = self._indent
        self._indent += "    " if is_last else "│   "

        if isinstance(node, Program):
            for i, s in enumerate(node.statements):
                self.print_node(s, is_last=(i == len(node.statements) - 1))

        elif isinstance(node, Function):
            params_str = ", ".join(f"{p['name']}: {p['type']}" for p in node.params)
            print(f"{self._indent}├── params: [{params_str}]")
            print(f"{self._indent}├── returns: {node.return_type}")
            self.print_node(node.body, label="body", is_last=True)

        elif isinstance(node, BinaryOp):
            self.print_node(node.left,  label="L", is_last=False)
            self.print_node(node.right, label="R", is_last=True)

        elif isinstance(node, (VarDecl, Assignment)):
            self.print_node(node.value, label="value", is_last=True)

        elif isinstance(node, (If, While)):
            self.print_node(node.condition, label="cond", is_last=False)
            has_else = isinstance(node, If) and node.else_body
            self.print_node(node.body, label="then", is_last=not has_else)
            if has_else:
                self.print_node(node.else_body, label="else", is_last=True)

        elif isinstance(node, Call):
            for i, arg in enumerate(node.args):
                self.print_node(arg, label=f"arg{i}", is_last=(i == len(node.args) - 1))

        elif isinstance(node, ArrayIndex):
            self.print_node(node.name,  label="base", is_last=False)
            self.print_node(node.index, label="idx",  is_last=True)

        elif isinstance(node, ArrayLiteral):
            for i, el in enumerate(node.elements):
                self.print_node(el, label=f"[{i}]", is_last=(i == len(node.elements) - 1))

        elif isinstance(node, (Return, Print)):
            self.print_node(node.value, label="value", is_last=True)

        self._indent = saved_indent
