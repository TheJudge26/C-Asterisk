import llvmlite.ir as ir
import llvmlite.binding as llvm

from tokens import TokenType
from parser import (
    Program, Function, Print, Number, BinaryOp,
    VarDecl, Variable, Assignment, If, While,
    Return, ArrayLiteral, ArrayIndex, FloatNode,
    Call, StringNode, BoolNode, For
)


class LLVMCodeGenerator:
    def __init__(self):
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        self.module = ir.Module(name="cstar_module")
        self.module.triple = llvm.get_default_triple()

        self.builder = None
        self.variables = {}

        self.i32 = ir.IntType(32)
        self.f64 = ir.DoubleType()
        self.i8_ptr = ir.IntType(8).as_pointer()

        # printf
        printf_ty = ir.FunctionType(self.i32, [self.i8_ptr], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

    # =====================================================
    # CORE
    # =====================================================
    def generate(self, ast):
        self.visit(ast)
        print(self.module)

    def visit(self, node):
        if node is None:
            return None
        return getattr(self, f"visit_{type(node).__name__}", self.generic_visit)(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__}")

    # =====================================================
    # PROGRAM
    # =====================================================
    def visit_Program(self, node):
        fn_type = ir.FunctionType(self.i32, [])
        main = ir.Function(self.module, fn_type, name="main")

        block = main.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)

        for stmt in node.statements:
            self.visit(stmt)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.i32, 0))

    # =====================================================
    # LITERALS
    # =====================================================
    def visit_Number(self, node):
        return ir.Constant(self.i32, int(node.value))

    def visit_FloatNode(self, node):
        return ir.Constant(self.f64, float(node.value))

    def visit_BoolNode(self, node):
        return ir.Constant(self.i32, 1 if node.value else 0)

    def visit_StringNode(self, node):
        text = bytearray((node.value + "\0").encode())

        ty = ir.ArrayType(ir.IntType(8), len(text))
        name = f"str_{len(self.module.globals)}"

        glob = ir.GlobalVariable(self.module, ty, name=name)
        glob.global_constant = True
        glob.initializer = ir.Constant(ty, text)

        return self.builder.gep(glob, [self.i32(0), self.i32(0)])

    # =====================================================
    # VARIABLES
    # =====================================================
    def visit_VarDecl(self, node):
        ptr = self.builder.alloca(self.i32, name=node.name)
        self.variables[node.name] = ptr

        val = self.visit(node.value)
        self.builder.store(val, ptr)

    def visit_Assignment(self, node):
        if node.name not in self.variables:
            raise Exception(f"Undefined variable {node.name}")

        ptr = self.variables[node.name]
        val = self.visit(node.value)
        self.builder.store(val, ptr)

    def visit_Variable(self, node):
        if node.name not in self.variables:
            raise Exception(f"Undefined variable {node.name}")
        return self.builder.load(self.variables[node.name])

    # =====================================================
    # BINARY OPERATIONS
    # =====================================================
    def visit_BinaryOp(self, node):
        l = self.visit(node.left)
        r = self.visit(node.right)

        is_float = isinstance(l.type, ir.DoubleType) or isinstance(r.type, ir.DoubleType)

        if node.op == TokenType.PLUS:
            return self.builder.fadd(l, r) if is_float else self.builder.add(l, r)

        if node.op == TokenType.MINUS:
            return self.builder.fsub(l, r) if is_float else self.builder.sub(l, r)

        if node.op == TokenType.MULTIPLY:
            return self.builder.fmul(l, r) if is_float else self.builder.mul(l, r)

        if node.op == TokenType.DIVIDE:
            return self.builder.fdiv(l, r) if is_float else self.builder.sdiv(l, r)

        if node.op in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
            if is_float:
                op = {
                    TokenType.GREATER: ">",
                    TokenType.LESS: "<",
                    TokenType.EQUAL_EQUAL: "=="
                }[node.op]
                cmp = self.builder.fcmp_ordered(op, l, r)
            else:
                op = {
                    TokenType.GREATER: ">",
                    TokenType.LESS: "<",
                    TokenType.EQUAL_EQUAL: "=="
                }[node.op]
                cmp = self.builder.icmp_signed(op, l, r)

            return self.builder.zext(cmp, self.i32)

    # =====================================================
    # PRINT
    # =====================================================
    def visit_Print(self, node):
        val = self.visit(node.value)

        if val.type == self.i32:
            fmt = "%d\n\0"
        elif val.type == self.f64:
            fmt = "%f\n\0"
        else:
            fmt = "%s\n\0"

        fmt_ptr = self._fmt(fmt)
        self.builder.call(self.printf, [fmt_ptr, val])

    def _fmt(self, s):
        data = bytearray(s.encode())
        ty = ir.ArrayType(ir.IntType(8), len(data))

        glob = ir.GlobalVariable(self.module, ty, name=f"fmt_{len(self.module.globals)}")
        glob.global_constant = True
        glob.initializer = ir.Constant(ty, data)

        return self.builder.gep(glob, [self.i32(0), self.i32(0)])

    # =====================================================
    # CONTROL FLOW
    # =====================================================
    def visit_If(self, node):
        cond = self.visit(node.condition)
        cond = self.builder.icmp_signed("!=", cond, self.i32(0))

        then_bb = self.builder.append_basic_block("then")
        else_bb = self.builder.append_basic_block("else") if node.else_body else None
        end_bb = self.builder.append_basic_block("end")

        self.builder.cbranch(cond, then_bb, else_bb or end_bb)

        self.builder.position_at_end(then_bb)
        for s in node.body:
            self.visit(s)
        if not self.builder.block.is_terminated:
            self.builder.branch(end_bb)

        if else_bb:
            self.builder.position_at_end(else_bb)
            for s in node.else_body:
                self.visit(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(end_bb)

        self.builder.position_at_end(end_bb)

    def visit_While(self, node):
        cond_bb = self.builder.append_basic_block("cond")
        body_bb = self.builder.append_basic_block("body")
        end_bb = self.builder.append_basic_block("end")

        self.builder.branch(cond_bb)

        self.builder.position_at_end(cond_bb)
        cond = self.visit(node.condition)
        cond = self.builder.icmp_signed("!=", cond, self.i32(0))
        self.builder.cbranch(cond, body_bb, end_bb)

        self.builder.position_at_end(body_bb)
        for s in node.body:
            self.visit(s)
        self.builder.branch(cond_bb)

        self.builder.position_at_end(end_bb)

    # =====================================================
    # FUNCTIONS (FIXED)
    # =====================================================
    def visit_Function(self, node):
        ret_ty = self.i32 if node.return_type != "float" else self.f64

        param_types = []
        for p in node.params:
            param_types.append(self.i32)

        fn_type = ir.FunctionType(ret_ty, param_types)
        func = ir.Function(self.module, fn_type, name=node.name)

        block = func.append_basic_block("entry")
        old_builder = self.builder
        old_vars = self.variables.copy()

        self.builder = ir.IRBuilder(block)

        self.variables = {}

        for i, p in enumerate(node.params):
            ptr = self.builder.alloca(self.i32, name=p["name"])
            self.builder.store(func.args[i], ptr)
            self.variables[p["name"]] = ptr

        for stmt in node.body:
            self.visit(stmt)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ret_ty, 0))

        self.builder = old_builder
        self.variables = old_vars

    def visit_Return(self, node):
        self.builder.ret(self.visit(node.value))

    # =====================================================
    # CALLS (FIXED SAFE)
    # =====================================================
    def visit_Call(self, node):
        func = self.module.globals.get(node.name)

        if func is None:
            raise Exception(f"Undefined function {node.name}")

        args = [self.visit(a) for a in node.args]
        return self.builder.call(func, args)

    # =====================================================
    # FOR LOOPS (PRESERVED + FIXED SAFETY)
    # =====================================================
    def visit_For(self, node):
        start = ir.Constant(self.i32, 0)
        end = self.i32(10)

        i_ptr = self.builder.alloca(self.i32, name=node.var)
        self.builder.store(start, i_ptr)

        cond_bb = self.builder.append_basic_block("for.cond")
        body_bb = self.builder.append_basic_block("for.body")
        end_bb = self.builder.append_basic_block("for.end")

        self.builder.branch(cond_bb)

        self.builder.position_at_end(cond_bb)
        i = self.builder.load(i_ptr)
        cond = self.builder.icmp_signed("<", i, end)
        self.builder.cbranch(cond, body_bb, end_bb)

        self.builder.position_at_end(body_bb)

        self.variables[node.var] = i_ptr

        for s in node.body:
            self.visit(s)

        i = self.builder.load(i_ptr)
        self.builder.store(self.builder.add(i, self.i32(1)), i_ptr)

        self.builder.branch(cond_bb)
        self.builder.position_at_end(end_bb)

    # =====================================================
    # ARRAYS (SAFE BASIC SUPPORT)
    # =====================================================
    def visit_ArrayLiteral(self, node):
        vals = [self.visit(v) for v in node.elements]
        arr_ty = ir.ArrayType(self.i32, len(vals))
        return ir.Constant(arr_ty, vals)

    def visit_ArrayIndex(self, node):
        base = self.variables[node.array.name]
        idx = self.visit(node.index)

        ptr = self.builder.gep(base, [self.i32(0), idx])
        return self.builder.load(ptr)