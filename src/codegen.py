import llvmlite.ir as ir
import llvmlite.binding as llvm
from tokens import TokenType
from parser import (
    Program, Function, Print, Number, BinaryOp, 
    VarDecl, Variable, Assignment, If, While, 
    Return, ArrayLiteral, ArrayIndex, FloatNode, Call, StringNode, BoolNode, For,
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
        # self.printf_format = bytearray(b"%f\n\00")
        self.string_type = ir.IntType(8).as_pointer()

        
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
    # String Addition
    def create_format_string(self, format_str):
        fmt = bytearray(format_str.encode("utf8"))

        string_type = ir.ArrayType(ir.IntType(8), len(fmt))

        global_fmt = ir.GlobalVariable(
            self.module,
            string_type,
            name=f"fmt_{len(self.module.globals)}"
        )

        global_fmt.global_constant = True
        global_fmt.initializer = ir.Constant(string_type, fmt)

        zero = ir.Constant(self.i32_type, 0)

        return self.builder.gep(global_fmt, [zero, zero])
    
    # Bool Addition
    def visit_BoolNode(self, node):
        return ir.Constant(
            self.i32_type,
            1 if node.value else 0
        )


    def visit_FloatNode(self, node):
        return ir.Constant(self.float_type, float(node.value))

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method defined in LLVMCodeGenerator")

    def visit_Program(self, node):
        main_type = ir.FunctionType(self.i32_type, [])
        main_func = ir.Function(self.module, main_type, name="main")
        block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        # self.fmt_ptr = self.builder.alloca(ir.ArrayType(ir.IntType(8), len(self.printf_format)))
        # self.builder.store(ir.Constant(ir.ArrayType(ir.IntType(8), len(self.printf_format)), self.printf_format), self.fmt_ptr)
        for stmt in node.statements: self.visit(stmt)
        if not self.builder.block.is_terminated: self.builder.ret(ir.Constant(self.i32_type, 0))

    def visit_StringNode(self, node):
        string_value = node.value + "\0"

        string_bytes = bytearray(string_value.encode("utf8"))
        string_type = ir.ArrayType(ir.IntType(8), len(string_bytes))

        global_str = ir.GlobalVariable(
            self.module,
            string_type,
            name=f"str_{len(self.module.globals)}"
        )

        global_str.global_constant = True
        global_str.initializer = ir.Constant(string_type, string_bytes)

        zero = ir.Constant(self.i32_type, 0)

        return self.builder.gep(global_str, [zero, zero])

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
        
        if node.type_annotation.startswith("["):
            elem_ty = self.float_type if "float" in node.type_annotation else self.i32_type
            alloca_type = ir.ArrayType(elem_ty, len(node.value.elements))

        else:
            if node.type_annotation == "float":
                alloca_type = self.float_type
            elif node.type_annotation == "string":
                alloca_type = self.string_type
            else:
                alloca_type = self.i32_type
        
        ptr = self.builder.alloca(alloca_type, name=node.name)
        self.variables[node.name] = ptr

        value = self.visit(node.value)
        self.builder.store(value, ptr)

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

    def visit_For(self, node):
        if isinstance(node.iterable, Call) and node.iterable.name == "range":
            # Range
            start = self.visit(node.iterable.args[0])
            end = self.visit(node.iterable.args[1])

            i_ptr = self.builder.alloca(self.i32_type, name=node.var)
            self.builder.store(start, i_ptr)

            loop_cond = self.builder.append_basic_block("for.cond")
            loop_body = self.builder.append_basic_block("for.body")
            loop_end = self.builder.append_basic_block("for.end")

            self.builder.branch(loop_cond)

            # condition
            self.builder.position_at_end(loop_cond)
            i_val = self.builder.load(i_ptr)
            cond = self.builder.icmp_signed("<", i_val, end)
            self.builder.cbranch(cond, loop_body, loop_end)

            # body
            self.builder.position_at_end(loop_body)

            self.variables[node.var] = i_ptr

            for stmt in node.body:
                self.visit(stmt)

            # increment
            i_val = self.builder.load(i_ptr)
            new_val = self.builder.add(i_val, ir.Constant(self.i32_type, 1))
            self.builder.store(new_val, i_ptr)

            self.builder.branch(loop_cond)

            self.builder.position_at_end(loop_end)
            return
        
        # ARRAY LOOP
        array_ptr = self.visit(node.iterable)

        data_ptr_ptr = self.builder.gep(
            array_ptr,
            [ir.Constant(self.i32_type, 0),
            ir.Constant(self.i32_type, 0)]
        )

        data_ptr = self.builder.load(data_ptr_ptr)

        size_ptr = self.builder.gep(
            array_ptr,
            [ir.Constant(self.i32_type, 0),
            ir.Constant(self.i32_type, 1)]
        )

        size = self.builder.load(size_ptr)

        i_ptr = self.builder.alloca(self.i32_type, name=node.var)
        self.builder.store(ir.Constant(self.i32_type, 0), i_ptr)

        loop_cond = self.builder.append_basic_block("arr.cond")
        loop_body = self.builder.append_basic_block("arr.body")
        loop_end = self.builder.append_basic_block("arr.end")

        self.builder.branch(loop_cond)

        self.builder.position_at_end(loop_cond)
        i_val = self.builder.load(i_ptr)
        cond = self.builder.icmp_signed("<", i_val, size)
        self.builder.cbranch(cond, loop_body, loop_end)

        self.builder.position_at_end(loop_body)

        idx = self.builder.load(i_ptr)
        elem_ptr = self.builder.gep(data_ptr, [ir.Constant(self.i32_type, 0), idx])
        elem = self.builder.load(elem_ptr)

        # bind loop variable to element
        var_ptr = self.builder.alloca(self.i32_type, name=node.var)
        self.builder.store(elem, var_ptr)
        self.variables[node.var] = var_ptr

        for stmt in node.body:
            self.visit(stmt)

        i_val = self.builder.load(i_ptr)
        new_val = self.builder.add(i_val, ir.Constant(self.i32_type, 1))
        self.builder.store(new_val, i_ptr)

        self.builder.branch(loop_cond)

        self.builder.position_at_end(loop_end)

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
        value = self.visit(node.value)

        if value.type == self.i32_type:
            fmt = self.create_format_string("%d\n\0")

        elif value.type == self.float_type:
            fmt = self.create_format_string("%f\n\0")

        elif value.type == self.string_type:
            fmt = self.create_format_string("%s\n\0")

        else:
            raise Exception(f"Unsupported print type: {value.type}")

        self.builder.call(self.printf, [fmt, value])

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