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
        self.classes = {}

        self.i32 = ir.IntType(32)
        self.f64 = ir.DoubleType()
        self.i8_ptr = ir.IntType(8).as_pointer()

        printf_ty = ir.FunctionType(self.i32, [self.i8_ptr], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")
        # Link the C math library 'exp' function
        exp_ty = ir.FunctionType(self.f64, [self.f64])
        self.exp_func = ir.Function(self.module, exp_ty, name="exp")
    
        # The C function takes a string (char*) and an integer (int), and returns a float pointer (double*)
        csv_ty = ir.FunctionType(self.f64.as_pointer(), [self.i8_ptr, self.i32])
        self.load_csv_func = ir.Function(self.module, csv_ty, name="load_csv_native")
        

        self.sqrt_func = ir.Function(self.module, exp_ty, name="sqrt")
        self.log_func = ir.Function(self.module, exp_ty, name="log")
        
        pow_ty = ir.FunctionType(self.f64, [self.f64, self.f64])
        self.pow_func = ir.Function(self.module, pow_ty, name="pow")
        

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

    # ============
    # VARIABLES 
    # =========
    def visit_VarDecl(self, node):
        val = self.visit(node.value)
        # allocate memory based on the ACTUAL type of the value
        ptr = self.builder.alloca(val.type, name=node.name)
        self.variables[node.name] = ptr
        self.builder.store(val, ptr)

    def visit_Assignment(self, node):
        if getattr(node, "target", None):
        
            ptr = self.get_ptr(node.target)
        else:
            
            if node.name not in self.variables:
                raise Exception(f"Undefined variable {node.name}")
            ptr = self.variables[node.name]
        val = self.visit(node.value)
        self.builder.store(val, ptr)

    def visit_Variable(self, node):
        if node.name not in self.variables:
            raise Exception(f"Undefined variable {node.name}")
        return self.builder.load(self.variables[node.name])
    
    def visit_ExpressionStatement(self, node):
        return self.visit(node.expression)

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

    # =====
    # PRINT
    # =========
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

    # ============
    # CONTROL FLOW
    # ==============
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

    # =============
    # FUNCTIONS 
    # =============
    def visit_Function(self, node):
        ret_ty = self.f64 if node.return_type == "float" else self.i32

        # dynamically determine parameter types
        param_types = []
        for p in node.params:
            if p["type"] == "float":
                param_types.append(self.f64)
            elif p["type"] in self.classes:
                
                param_types.append(self.classes[p["type"]]["type"].as_pointer())
            else:
                param_types.append(self.i32)

        fn_type = ir.FunctionType(ret_ty, param_types)
        func = ir.Function(self.module, fn_type, name=node.name)

        block = func.append_basic_block("entry")
        old_builder = self.builder
        old_vars = self.variables.copy()

        self.builder = ir.IRBuilder(block)
        self.variables = {}

        for i, p in enumerate(node.params):
            if p["name"] == "self":
                
                self.variables[p["name"]] = func.args[i]
            else:
                ptr = self.builder.alloca(param_types[i], name=p["name"])
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
    # CALLS (LEN & METHODS)
    # =====================================================
    def visit_Call(self, node):
        
        # 1. Handle Method Calls (e.g. n.calculate())
        if getattr(node, "object", None) is not None:
            obj_ptr = self.variables[node.object.name]
            class_name = obj_ptr.type.pointee.name
            
            func_name = f"{class_name}_{node.name}"
            func = self.module.globals.get(func_name)
            
            args = [obj_ptr] + [self.visit(a) for a in node.args]
            return self.builder.call(func, args)
        
        # handle load_csv built-in function
        if node.name == "load_csv":
            filename = self.visit(node.args[0])
            num_values = self.visit(node.args[1])
            return self.builder.call(self.load_csv_func, [filename, num_values])

        if node.name in self.classes:
            class_info = self.classes[node.name]
            ptr = self.builder.alloca(class_info["type"], name=f"new_{node.name}")
            
            for i, default_node in enumerate(class_info["defaults"]):
                if default_node: 
                    val = self.visit(default_node) 
                    field_ptr = self.builder.gep(ptr, [self.i32(0), self.i32(i)], inbounds=True)
                    
                    
                    if isinstance(val.type, ir.ArrayType) and isinstance(field_ptr.type.pointee, ir.PointerType):
                        
                        temp_arr = self.builder.alloca(val.type)
                        self.builder.store(val, temp_arr)
                        
                        val = self.builder.bitcast(temp_arr, field_ptr.type.pointee)
                    
                    
                    self.builder.store(val, field_ptr) 
            
            return self.builder.load(ptr)

        
        if node.name == "len":
            arg = self.visit(node.args[0])
            if isinstance(arg.type, ir.ArrayType):
                length = arg.type.count
            elif hasattr(arg.type, "pointee") and isinstance(arg.type.pointee, ir.ArrayType):
                length = arg.type.pointee.count
            else:
                length = 0 
            return ir.Constant(self.i32, length)

        
        if node.name in ["exp", "sqrt", "log"]:
            arg = self.visit(node.args[0])
            if arg.type != self.f64:
                arg = self.builder.sitofp(arg, self.f64)
                
            if node.name == "exp":
                return self.builder.call(self.exp_func, [arg])
            elif node.name == "sqrt":
                return self.builder.call(self.sqrt_func, [arg])
            elif node.name == "log":
                return self.builder.call(self.log_func, [arg])

        if node.name == "pow":
            base = self.visit(node.args[0])
            exp_val = self.visit(node.args[1])
            if base.type != self.f64:
                base = self.builder.sitofp(base, self.f64)
            if exp_val.type != self.f64:
                exp_val = self.builder.sitofp(exp_val, self.f64)
            return self.builder.call(self.pow_func, [base, exp_val])

        
        func = self.module.globals.get(node.name)
        if func is None:
            raise Exception(f"Undefined function {node.name}")

        args = [self.visit(a) for a in node.args]
        return self.builder.call(func, args)
    
    

    # ===============
    # MEMBER ACCESS
    # ===============
    def visit_MemberAccess(self, node):
        """Pulls a specific field out of an object (e.g. obj.field)."""
        obj_ptr = self.variables[node.object.name]
        class_name = obj_ptr.type.pointee.name
        
        field_idx = self.classes[class_name]["indices"][node.member]
        
        ptr = self.builder.gep(obj_ptr, [self.i32(0), self.i32(field_idx)], inbounds=True)
        return self.builder.load(ptr)

    # ==========
    # FOR LOOPS 
    # ==========
    
    def visit_For(self, node):
        limit_val = self.visit(node.iterable) 
        start = ir.Constant(self.i32, 0)
        i_ptr = self.builder.alloca(self.i32, name=node.var)
        self.builder.store(start, i_ptr)

        self.variables[node.var] = i_ptr # register loop variable

        cond_bb = self.builder.append_basic_block("for.cond")
        body_bb = self.builder.append_basic_block("for.body")
        end_bb = self.builder.append_basic_block("for.end")

        self.builder.branch(cond_bb)
        self.builder.position_at_end(cond_bb)
        i = self.builder.load(i_ptr)
        cond = self.builder.icmp_signed("<", i, limit_val)
        self.builder.cbranch(cond, body_bb, end_bb)

        self.builder.position_at_end(body_bb)
        for s in node.body:
            self.visit(s)

        i = self.builder.load(i_ptr)
        self.builder.store(self.builder.add(i, self.i32(1)), i_ptr)
        self.builder.branch(cond_bb)
        self.builder.position_at_end(end_bb)

    # ============================
    # MULTI-DIMENSIONAL ARRAYS 
    # ===========================
    def get_ptr(self, node):
        """Recursively finds the exact memory address for variables, class fields, and chained array indices."""
        if type(node).__name__ == "Variable":
            return self.variables[node.name]
            
        elif type(node).__name__ == "MemberAccess":
            obj_ptr = self.variables[node.object.name]
            class_name = obj_ptr.type.pointee.name
            field_idx = self.classes[class_name]["indices"][node.member]
            return self.builder.gep(obj_ptr, [self.i32(0), self.i32(field_idx)], inbounds=True)
            
        elif type(node).__name__ == "ArrayIndex":
            base_ptr = self.get_ptr(node.array)
            idx = self.visit(node.index)
            
            
            if isinstance(base_ptr.type.pointee, ir.PointerType):
                actual_ptr = self.builder.load(base_ptr)
                return self.builder.gep(actual_ptr, [idx], inbounds=True)
            else:
                
                return self.builder.gep(base_ptr, [self.i32(0), idx], inbounds=True)
            
            
        raise Exception(f"Cannot get pointer for {type(node).__name__}")

    def visit_ArrayIndex(self, node):
        """Pulls a value out of an array at a specific index."""
       
        ptr = self.get_ptr(node)
        return self.builder.load(ptr) 


    def visit_ClassDecl(self, node):
        """Defines a new Object Struct in memory."""
        class_type = self.module.context.get_identified_type(node.name)
        
        field_types = []
        field_indices = {}
        field_defaults = [] 
        
        index = 0
        for member in node.body:
            if type(member).__name__ == "VarDecl":
                if member.type_annotation == "float":
                    ll_type = self.f64
                elif member.type_annotation == "int":
                    ll_type = self.i32
                elif type(member.value).__name__ == "ArrayLiteral":
                    base_type = self.f64 if "float" in member.type_annotation else self.i32
                    
                    
                    dims = []
                    curr = member.value
                    while type(curr).__name__ == "ArrayLiteral":
                        dims.append(len(curr.elements))
                        curr = curr.elements[0] if len(curr.elements) > 0 else None
                        
                    
                    if type(member).__name__ == "VarDecl":
                      if member.type_annotation == "float":
                       ll_type = self.f64
                elif member.type_annotation == "int":
                    ll_type = self.i32
                
                
                elif member.type_annotation == "[float]":
                    ll_type = self.f64.as_pointer()
                
                
                elif type(member.value).__name__ == "ArrayLiteral":
                    base_type = self.f64 if "float" in member.type_annotation else self.i32
                    
                else:
                    ll_type = self.i8_ptr 
                
                field_types.append(ll_type)
                field_indices[member.name] = index
                field_defaults.append(member.value) 
                index += 1
                
        class_type.set_body(*field_types)
        
        self.classes[node.name] = {
            "type": class_type,
            "indices": field_indices,
            "defaults": field_defaults 
        }

        
        old_builder = self.builder
        
        
        for member in node.body:
            if type(member).__name__ == "Function":
                
                member.name = f"{node.name}_{member.name}"
                
                self.visit(member) 
                
        
        self.builder = old_builder
        

    def visit_MemberAccess(self, node):
        """Pulls a specific field out of an object (e.g. obj.field)."""
        
        obj_ptr = self.variables[node.object.name]
        
        
        class_name = obj_ptr.type.pointee.name
        
        
        field_idx = self.classes[class_name]["indices"][node.member]
        
        
        ptr = self.builder.gep(obj_ptr, [self.i32(0), self.i32(field_idx)], inbounds=True)
        return self.builder.load(ptr)

    
    
    def execute(self):
        llvm_ir = str(self.module)
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()

        target_machine = llvm.Target.from_default_triple().create_target_machine()
        with llvm.create_mcjit_compiler(mod, target_machine) as ee:
            ee.finalize_object()
            func_ptr = ee.get_function_address("main")
            
            from ctypes import CFUNCTYPE, c_int
            cfunc = CFUNCTYPE(c_int)(func_ptr)
            
            print("\n--- Running Program ---")
            result = cfunc()
            print(f"--- Program Exited with code {result} ---")

    
    # =====================================================
    # ARRAYS (DYNAMIC MEMORY)
    # =====================================================
    def visit_ArrayLiteral(self, node):
        elements = [self.visit(el) for el in node.elements]
        if not elements:
            return ir.Constant(ir.ArrayType(self.i32, 0), [])

        elem_ty = elements[0].type
        arr_ty = ir.ArrayType(elem_ty, len(elements))

        # --- THE LLVM MEMORY OPTIMIZATION  ---
        # If the array is purely raw numbers (like our massive CSV dataset)
        # we skip the 40,000 store instructions and package it instantly
        if all(isinstance(val, ir.Constant) for val in elements):
            return ir.Constant(arr_ty, elements)
        
        # Build array dynamically on the stack 
        tmp_ptr = self.builder.alloca(arr_ty, name="arr_literal_tmp")
        for i, val in enumerate(elements):
            idx = ir.Constant(self.i32, i)
            zero = ir.Constant(self.i32, 0)
            ptr = self.builder.gep(tmp_ptr, [zero, idx], inbounds=True)
            self.builder.store(val, ptr)
            
        return self.builder.load(tmp_ptr)
    
    def execute(self):
        """Compiles the IR and runs the main function."""
        
        llvm_ir = str(self.module)
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()

        
        target_machine = llvm.Target.from_default_triple().create_target_machine()

        
        pto = llvm.create_pipeline_tuning_options(speed_level=3)
        pb = llvm.create_pass_builder(target_machine, pto)
        pm = pb.getModulePassManager()
        pm.run(mod, pb)
        

        
        with llvm.create_mcjit_compiler(mod, target_machine) as ee:
            ee.finalize_object()
            
            
            func_ptr = ee.get_function_address("main")
            
           
            from ctypes import CFUNCTYPE, c_int
            import time  
            
            cfunc = CFUNCTYPE(c_int)(func_ptr)
            
            print("\n--- Running Program ---")
            
            start_time = time.time() 
            result = cfunc()
            end_time = time.time() 
            
            print(f"--- Program Exited with code {result} ---")
            print(f".cstar took: {end_time - start_time:.6f} seconds")
            return result
    
    #testing something 

    def save_object(self, filename):
        """Compiles the LLVM IR down to a native Object File (.obj / .o)."""
        
        llvm_ir = str(self.module)
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()
        
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()

    
        obj_code = target_machine.emit_object(mod)

        with open(filename, "wb") as f:
            f.write(obj_code)
            
        print(f"Native Object File saved to: {filename}")