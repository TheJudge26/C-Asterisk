import llvmlite.ir as ir
import llvmlite.binding as llvm
from tokens import TokenType
from parser import (
    Program, Function, Print, Number, BinaryOp, 
    VarDecl, Variable, Assignment, If, While, 
    Return, ArrayLiteral, ArrayIndex, FloatNode, Call 
)

class LLVMCodeGenerator:
    def __init__(self):
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self.module = ir.Module(name="cstar_module")
        self.module.triple = llvm.get_default_triple()
        self.builder = None
        self.variables = {}
        self.i32_type = ir.IntType(32)
        self.float_type = ir.DoubleType() 
        printf_ty = ir.FunctionType(self.i32_type, [ir.IntType(8).as_pointer()], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")
        self.printf_format = bytearray(b"%f\n\00")

    def generate(self, ast):
        self.visit(ast)
        print("\n--- GENERATED LLVM IR (NATIVE MACHINE CODE) ---")
        print(str(self.module))
        print("-----------------------------------------------")

    def visit(self, node):
        if node is None: return None
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def visit_FloatNode(self, node):
        return ir.Constant(self.float_type, float(node.value))

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method defined in LLVMCodeGenerator")

    def visit_Program(self, node):
        main_type = ir.FunctionType(self.i32_type, [])
        main_func = ir.Function(self.module, main_type, name="main")
        block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.fmt_ptr = self.builder.alloca(ir.ArrayType(ir.IntType(8), len(self.printf_format)))
        self.builder.store(ir.Constant(ir.ArrayType(ir.IntType(8), len(self.printf_format)), self.printf_format), self.fmt_ptr)
        for stmt in node.statements: self.visit(stmt)
        if not self.builder.block.is_terminated: self.builder.ret(ir.Constant(self.i32_type, 0))

    def visit_Function(self, node):
        llvm_param_types = []
        for p in node.params: # FIXED: Handle array parameters as pointers
            if p['type'].startswith("["):
                elem_type = self.float_type if "float" in p['type'] else self.i32_type
                llvm_param_types.append(elem_type.as_pointer())
            else:
                llvm_param_types.append(self.float_type if p['type'] == "float" else self.i32_type)

        return_ty = self.float_type if node.return_type == "float" else self.i32_type
        func_ty = ir.FunctionType(return_ty, llvm_param_types)
        func = ir.Function(self.module, func_ty, name=node.name)
        block = func.append_basic_block(name="entry")
        old_builder, old_vars = self.builder, self.variables.copy()
        self.builder = ir.IRBuilder(block)
        for i, p in enumerate(node.params):
            arg_val = func.args[i]
            ptr = self.builder.alloca(arg_val.type, name=p['name'])
            self.builder.store(arg_val, ptr)
            self.variables[p['name']] = ptr
        for stmt in node.body: self.visit(stmt)
        self.variables, self.builder = old_vars, old_builder
        return func

    def visit_Return(self, node):
        self.builder.ret(self.visit(node.value))

    def visit_Call(self, node):
        func = self.module.globals.get(node.name)
        args = []
        for arg_node in node.args:
            if isinstance(arg_node, Variable): # FIXED: Pointer Decay logic
                ptr = self.variables[arg_node.name]
                if isinstance(ptr.type.pointee, ir.ArrayType):
                    args.append(self.builder.gep(ptr, [ir.Constant(self.i32_type, 0), ir.Constant(self.i32_type, 0)]))
                else: args.append(self.builder.load(ptr))
            else: args.append(self.visit(arg_node))
        return self.builder.call(func, args)

    def visit_VarDecl(self, node):
        value = self.visit(node.value)
        if node.type_annotation.startswith("["):
            elem_ty = self.float_type if "float" in node.type_annotation else self.i32_type
            alloca_type = ir.ArrayType(elem_ty, len(node.value.elements))
        else: alloca_type = self.float_type if node.type_annotation == "float" else self.i32_type
        ptr = self.builder.alloca(alloca_type, name=node.name)
        self.builder.store(value, ptr)
        self.variables[node.name] = ptr

    def visit_Assignment(self, node):
        self.builder.store(self.visit(node.value), self.variables[node.name])

    def visit_Variable(self, node):
        return self.builder.load(self.variables[node.name])

    def visit_Number(self, node): return ir.Constant(self.i32_type, int(node.value))

    def visit_BinaryOp(self, node):
        l, r = self.visit(node.left), self.visit(node.right)
        is_f = l.type == self.float_type or r.type == self.float_type
        if node.op == TokenType.PLUS: return self.builder.fadd(l, r) if is_f else self.builder.add(l, r)
        elif node.op == TokenType.MINUS: return self.builder.fsub(l, r) if is_f else self.builder.sub(l, r)
        elif node.op == TokenType.MULTIPLY: return self.builder.fmul(l, r) if is_f else self.builder.mul(l, r)
        elif node.op == TokenType.DIVIDE: return self.builder.fdiv(l, r) if is_f else self.builder.sdiv(l, r)
        elif node.op in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
            op = {TokenType.GREATER: ">", TokenType.LESS: "<", TokenType.EQUAL_EQUAL: "=="}[node.op]
            cmp = self.builder.fcmp_ordered(op, l, r) if is_f else self.builder.icmp_signed(op, l, r)
            return self.builder.zext(cmp, self.i32_type)

    def visit_If(self, node):
        cond = self.builder.icmp_signed("!=", self.visit(node.condition), ir.Constant(self.i32_type, 0))
        then_b = self.builder.append_basic_block("if.then")
        else_b = self.builder.append_basic_block("if.else") if node.else_body else None
        end_b = self.builder.append_basic_block("if.end")
        self.builder.cbranch(cond, then_b, else_b if else_b else end_b)
        self.builder.position_at_end(then_b)
        for s in node.body: self.visit(s)
        if not self.builder.block.is_terminated: self.builder.branch(end_b)
        if else_b:
            self.builder.position_at_end(else_b)
            for s in node.else_body: self.visit(s)
            if not self.builder.block.is_terminated: self.builder.branch(end_b)
        self.builder.position_at_end(end_b)

    def visit_While(self, node):
        cond_b, body_b, end_b = [self.builder.append_basic_block(n) for n in ["w.cond", "w.body", "w.end"]]
        self.builder.branch(cond_b)
        self.builder.position_at_end(cond_b)
        cmp = self.builder.icmp_signed("!=", self.visit(node.condition), ir.Constant(self.i32_type, 0))
        self.builder.cbranch(cmp, body_b, end_b)
        self.builder.position_at_end(body_b)
        for s in node.body: self.visit(s)
        self.builder.branch(cond_b)
        self.builder.position_at_end(end_b)

    def visit_ArrayLiteral(self, node):
        vals = [self.visit(el) for el in node.elements]
        return ir.Constant(ir.ArrayType(vals[0].type, len(node.elements)), vals) if vals else ir.Constant(ir.ArrayType(self.i32_type, 0), [])

    def visit_ArrayIndex(self, node): # FIXED: Support both local arrays and parameters
        base_ptr = self.variables[node.name]
        actual_ptr = self.builder.load(base_ptr)
        idx = self.visit(node.index)
        if isinstance(actual_ptr.type, ir.PointerType) and not isinstance(actual_ptr.type.pointee, ir.ArrayType):
            e_ptr = self.builder.gep(actual_ptr, [idx])
        else: e_ptr = self.builder.gep(base_ptr, [ir.Constant(self.i32_type, 0), idx])
        return self.builder.load(e_ptr)

    def visit_Print(self, node):
        fmt = self.builder.bitcast(self.fmt_ptr, ir.IntType(8).as_pointer())
        self.builder.call(self.printf, [fmt, self.visit(node.value)])

    def execute(self):
        target = llvm.Target.from_default_triple().create_target_machine()
        mod = llvm.parse_assembly(str(self.module))
        mod.verify()
        engine = llvm.create_mcjit_compiler(mod, target)
        engine.finalize_object()
        engine.run_static_constructors()
        import ctypes
        cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(engine.get_function_address("main"))
        print("\n================ START OF PROGRAM ================")
        cfunc()
        print("================ END OF PROGRAM ==================\n")