from parser import (
    Program, VarDecl, Assignment, BinaryOp, Number, 
    Variable, Print, If, While, Function, Return, 
    ArrayLiteral, ArrayIndex, FloatNode, Call
)

class ASTPrinter:
    def __init__(self):
        self.indent = ""

    def print_node(self, node, label="", is_last=True):
        marker = "└── " if is_last else "├── "
        prefix = f"{label}: " if label else ""
        
        if node is None:
            print(f"{self.indent}{marker}{prefix}None")
            return

        # Print the current node
        name = type(node).__name__
        val = f" ({node.value})" if hasattr(node, 'value') else ""
        if hasattr(node, 'name') and not isinstance(node.name, (Variable, ArrayIndex)):
            val = f" (name: {node.name})"
            
        print(f"{self.indent}{marker}{prefix}{name}{val}")

        # Prepare for children
        old_indent = self.indent
        self.indent += "    " if is_last else "│   "

        # Logic for specific nodes to find their "children"
        if isinstance(node, Program):
            for i, stmt in enumerate(node.statements):
                self.print_node(stmt, is_last=(i == len(node.statements) - 1))

        elif isinstance(node, Function):
            self.print_node(node.body, label="Body", is_last=True)

        elif isinstance(node, BinaryOp):
            self.print_node(node.left, label="Left", is_last=False)
            self.print_node(node.right, label="Right", is_last=True)

        elif isinstance(node, VarDecl) or isinstance(node, Assignment):
            self.print_node(node.value, label="Value", is_last=True)

        elif isinstance(node, If):
            self.print_node(node.condition, label="Cond", is_last=False)
            self.print_node(node.body, label="Then", is_last=node.else_body is None)
            if node.else_body:
                self.print_node(node.else_body, label="Else", is_last=True)

        elif isinstance(node, While):
            self.print_node(node.condition, label="Cond", is_last=False)
            self.print_node(node.body, label="Body", is_last=True)

        elif isinstance(node, Call):
            for i, arg in enumerate(node.args):
                self.print_node(arg, label=f"Arg[{i}]", is_last=(i == len(node.args) - 1))

        elif isinstance(node, ArrayIndex):
            # This handles recursive indexing like matrix[i][j]
            self.print_node(node.array, label="Base", is_last=False)
            self.print_node(node.index, label="Index", is_last=True)

        elif isinstance(node, list): # For block bodies
            for i, stmt in enumerate(node):
                self.print_node(stmt, is_last=(i == len(node) - 1))

        # Restore indent
        self.indent = old_indent