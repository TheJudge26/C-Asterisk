"""
codegen.py — LLVM IR code generator for C* via llvmlite.

Key fixes & additions vs. the previous version
───────────────────────────────────────────────
1. visit_ArrayIndex: robust GEP logic that distinguishes between
     • a fixed-size local array  ([N x T]*)   → needs double-index GEP
     • a pointer-to-element      (T*)          → single-index GEP
   This eliminates the TypeError crash on chained / parameter arrays.

2. Multidimensional arrays  ([[float]], etc.):
   • visit_ArrayLiteral builds nested ir.ArrayType constants recursively.
   • visit_ArrayIndex chains through multiple levels correctly.

3. Standard math library (sqrt, exp) properly linked from libm.

4. Level 6 Milestone 1: Formal i1 bool type and Boolean literal support.
5. Level 6 Milestone 2: Tensor Addition (A + B) generates nested LLVM IR loops.
6. Level 6 Milestone 3: Comparisons return formal i1 booleans.
"""

import llvmlite.ir       as ir
import llvmlite.binding  as llvm

from tokens import TokenType
from parser import (
    Program, Function, Call, BinaryOp, VarDecl, Assignment,
    ArrayIndex, Variable, Number, FloatNode, Boolean, Return, Print,
    ArrayLiteral, While, If,
)


class CodeGenError(Exception):
    pass


class LLVMCodeGenerator:

    def __init__(self):
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        self.module = ir.Module(name="cstar_module")
        self.module.triple = llvm.get_default_triple()

        self.builder:   ir.IRBuilder | None = None
        self.variables: dict                = {}     # name → alloca ptr

        # ---- primitive IR types
        self.i32_type   = ir.IntType(32)
        self.float_type = ir.DoubleType()
        self.bool_type  = ir.IntType(1)  # Milestone 1: Added for Level 6
        self.i8_ptr     = ir.IntType(8).as_pointer()

        # ---- printf (variadic)
        printf_ty   = ir.FunctionType(self.i32_type, [self.i8_ptr], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

        # printf format string: "%f\n\0"
        self._fmt_bytes = bytearray(b"%f\n\0")

        # ---- libm math functions
        math_ty      = ir.FunctionType(self.float_type, [self.float_type])
        self.fn_sqrt = ir.Function(self.module, math_ty, name="sqrt")
        self.fn_exp  = ir.Function(self.module, math_ty, name="exp")

    # ═══════════════════════════════════════════════════════════════
    #  Type helpers
    # ═══════════════════════════════════════════════════════════════

    def _llvm_type(self, type_str: str) -> ir.Type:
        """Recursively convert a C* type string to an llvmlite IR type."""
        if type_str == "int":
            return self.i32_type
        if type_str == "float":
            return self.float_type
        if type_str == "bool":
            return self.bool_type
        if type_str.startswith("["):
            inner = type_str[1:-1]
            # For function parameter types, arrays decay to pointer-to-element
            return self._llvm_type(inner).as_pointer()
        raise CodeGenError(f"Unknown type: '{type_str}'")

    def _elem_type(self, type_str: str) -> ir.Type:
        """Return the element LLVM type for an array C* type string."""
        if not type_str.startswith("["):
            raise CodeGenError(f"Not an array type: '{type_str}'")
        return self._llvm_type(type_str[1:-1])

    # ═══════════════════════════════════════════════════════════════
    #  Visitor dispatch
    # ═══════════════════════════════════════════════════════════════

    def generate(self, ast):
        self._visit(ast)

    def _visit(self, node):
        if node is None:
            return None
        method = getattr(self, f"_visit_{type(node).__name__}", None)
        if method is None:
            raise CodeGenError(f"No codegen rule for '{type(node).__name__}'")
        return method(node)

    # ═══════════════════════════════════════════════════════════════
    #  Top-level program → main()
    # ═══════════════════════════════════════════════════════════════

    def _visit_Program(self, node: Program):
        main_fn = ir.Function(
            self.module,
            ir.FunctionType(self.i32_type, []),
            name="main",
        )
        entry_block = main_fn.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)

        # Allocate + store the printf format string
        fmt_arr_ty  = ir.ArrayType(ir.IntType(8), len(self._fmt_bytes))
        self._fmt_ptr = self.builder.alloca(fmt_arr_ty, name="fmt")
        self.builder.store(
            ir.Constant(fmt_arr_ty, self._fmt_bytes),
            self._fmt_ptr,
        )

        for stmt in node.statements:
            self._visit(stmt)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.i32_type, 0))

    # ═══════════════════════════════════════════════════════════════
    #  Function declaration
    # ═══════════════════════════════════════════════════════════════

    def _visit_Function(self, node: Function):
        # Build parameter LLVM types (arrays decay to pointers)
        param_types = [self._llvm_type(p["type"]) for p in node.params]
        ret_type    = self._llvm_type(node.return_type)
        fn_type     = ir.FunctionType(ret_type, param_types)
        func        = ir.Function(self.module, fn_type, name=node.name)

        # Save outer state
        old_builder   = self.builder
        old_variables = self.variables.copy()

        entry_block   = func.append_basic_block(name="entry")
        self.builder  = ir.IRBuilder(entry_block)
        self.variables = {}

        for ir_arg, param in zip(func.args, node.params):
            ir_arg.name = param["name"]
            ptr = self.builder.alloca(ir_arg.type, name=param["name"])
            self.builder.store(ir_arg, ptr)
            self.variables[param["name"]] = ptr

        for stmt in node.body:
            self._visit(stmt)

        # Restore outer state
        self.variables = old_variables
        self.builder   = old_builder

    # ═══════════════════════════════════════════════════════════════
    #  Calls (including built-in math)
    # ═══════════════════════════════════════════════════════════════

    def _visit_Call(self, node: Call):
        if node.name == "sqrt":
            arg = self._coerce_float(self._visit(node.args[0]))
            return self.builder.call(self.fn_sqrt, [arg])
        if node.name == "exp":
            arg = self._coerce_float(self._visit(node.args[0]))
            return self.builder.call(self.fn_exp, [arg])

        func = self.module.globals.get(node.name)
        if func is None:
            raise CodeGenError(f"Undefined function '{node.name}'")

        args = []
        for a in node.args:
            v = self._visit(a)
            # Decay a fixed-size local array to a pointer before passing
            v = self._decay_to_pointer(v)
            args.append(v)
        return self.builder.call(func, args)

    # ═══════════════════════════════════════════════════════════════
    #  Binary operations & Tensor Addition
    # ═══════════════════════════════════════════════════════════════

    def _visit_BinaryOp(self, node: BinaryOp):
        l = self._visit(node.left)
        r = self._visit(node.right)

        # Milestone 2: Tensor Addition (Level 6 Logic)
        if node.op == TokenType.PLUS and isinstance(l.type, ir.PointerType) and isinstance(l.type.pointee, ir.ArrayType):
            return self._generate_tensor_addition(l, r)

        # Promote int → float if either side is float
        if l.type == self.float_type or r.type == self.float_type:
            l = self._coerce_float(l)
            r = self._coerce_float(r)
            is_float = True
        else:
            is_float = False

        op = node.op
        if op == TokenType.PLUS:
            return self.builder.fadd(l, r) if is_float else self.builder.add(l, r)
        if op == TokenType.MINUS:
            return self.builder.fsub(l, r) if is_float else self.builder.sub(l, r)
        if op == TokenType.MULTIPLY:
            return self.builder.fmul(l, r) if is_float else self.builder.mul(l, r)
        if op == TokenType.DIVIDE:
            return self.builder.fdiv(l, r) if is_float else self.builder.sdiv(l, r)

        # Milestone 3: Comparisons return formal i1 (bool)
        if op in (TokenType.GREATER, TokenType.LESS, TokenType.EQUAL_EQUAL):
            ops_map = {
                TokenType.GREATER:    ">",
                TokenType.LESS:       "<",
                TokenType.EQUAL_EQUAL: "==",
            }
            predicate = ops_map[op]
            if is_float:
                return self.builder.fcmp_ordered(predicate, l, r)
            else:
                return self.builder.icmp_signed(predicate, l, r)

        raise CodeGenError(f"Unknown binary operator: {op}")

    def _generate_tensor_addition(self, array_a, array_b):
        """Level 6 Milestone: Loop generation for matrix addition."""
        size = array_a.type.pointee.count
        res_ptr = self.builder.alloca(array_a.type.pointee, name="sum_res")
        idx_ptr = self.builder.alloca(self.i32_type, name="i")
        self.builder.store(ir.Constant(self.i32_type, 0), idx_ptr)
        
        cond_b = self.builder.append_basic_block("loop.cond")
        body_b = self.builder.append_basic_block("loop.body")
        end_b = self.builder.append_basic_block("loop.end")
        
        self.builder.branch(cond_b)
        self.builder.position_at_end(cond_b)
        curr_idx = self.builder.load(idx_ptr)
        cmp = self.builder.icmp_signed("<", curr_idx, ir.Constant(self.i32_type, size))
        self.builder.cbranch(cmp, body_b, end_b)
        
        self.builder.position_at_end(body_b)
        a_ptr = self.builder.gep(array_a, [ir.Constant(self.i32_type, 0), curr_idx])
        b_ptr = self.builder.gep(array_b, [ir.Constant(self.i32_type, 0), curr_idx])
        sum_val = self.builder.fadd(self.builder.load(a_ptr), self.builder.load(b_ptr))
        res_elem_ptr = self.builder.gep(res_ptr, [ir.Constant(self.i32_type, 0), curr_idx])
        self.builder.store(sum_val, res_elem_ptr)
        
        self.builder.store(self.builder.add(curr_idx, ir.Constant(self.i32_type, 1)), idx_ptr)
        self.builder.branch(cond_b)
        
        self.builder.position_at_end(end_b)
        return self.builder.load(res_ptr)

    # ═══════════════════════════════════════════════════════════════
    #  Variable declaration & assignment
    # ═══════════════════════════════════════════════════════════════

    def _visit_VarDecl(self, node: VarDecl):
        val = self._visit(node.value)
        ptr = self.builder.alloca(val.type, name=node.name)
        self.builder.store(val, ptr)
        self.variables[node.name] = ptr

    def _visit_Assignment(self, node: Assignment):
        val = self._visit(node.value)
        ptr = self.variables[node.name]
        self.builder.store(val, ptr)

    # ═══════════════════════════════════════════════════════════════
    #  Array literals
    # ═══════════════════════════════════════════════════════════════

    def _visit_ArrayLiteral(self, node: ArrayLiteral):
        """CodeGen: Builds the actual LLVM memory for the array."""
        elements = [self._visit(el) for el in node.elements]
        elem_ty = elements[0].type
        arr_ty = ir.ArrayType(elem_ty, len(elements))
        
        # Level 6 Fix: Build in memory if math (like -0.2) is present
        if any(not isinstance(e, ir.Constant) for e in elements):
            tmp_ptr = self.builder.alloca(arr_ty, name="arr_literal_tmp")
            for i, val in enumerate(elements):
                idx = ir.Constant(self.i32_type, i)
                zero = ir.Constant(self.i32_type, 0)
                ptr = self.builder.gep(tmp_ptr, [zero, idx], inbounds=True)
                self.builder.store(val, ptr)
            return self.builder.load(tmp_ptr)
            
        return ir.Constant(arr_ty, elements)

    # ═══════════════════════════════════════════════════════════════
    #  Array indexing — PRESERVED ORIGINAL FIX
    # ═══════════════════════════════════════════════════════════════

    def _visit_ArrayIndex(self, node: ArrayIndex):
        """Emit a GEP + load for base[index]."""
        # Load the base variable's storage pointer
        base_storage = self.variables.get(self._base_name(node.name))
        if base_storage is None:
            # base is the result of a previous ArrayIndex (already an IR value)
            base_val = self._visit_array_base(node.name)
        else:
            base_val = None   # we'll handle it below

        idx = self._visit(node.index)

        if base_val is not None:
            # base_val should already be a pointer to element
            elem_ptr = self.builder.gep(base_val, [idx], inbounds=True)
            return self.builder.load(elem_ptr)

        # base_storage is the alloca pointer
        pointee_ty = base_storage.type.pointee  # what the alloca holds

        if isinstance(pointee_ty, ir.ArrayType):
            # Case A: [N x T]* — use double-index GEP
            zero     = ir.Constant(self.i32_type, 0)
            elem_ptr = self.builder.gep(base_storage, [zero, idx], inbounds=True)
            return self.builder.load(elem_ptr)
        else:
            # Case B / C: T** (or T*) — load the pointer first, then GEP
            inner_ptr = self.builder.load(base_storage)   # → T*
            elem_ptr  = self.builder.gep(inner_ptr, [idx], inbounds=True)
            return self.builder.load(elem_ptr)

    def _base_name(self, node) -> str | None:
        """Return the variable name if node is a Variable, else None."""
        from parser import Variable as VarNode
        return node.name if isinstance(node, VarNode) else None

    def _visit_array_base(self, node):
        """Visit an ArrayIndex node but return the element pointer."""
        from parser import Variable as VarNode, ArrayIndex as AINode

        if isinstance(node, VarNode):
            storage = self.variables[node.name]
            pointee = storage.type.pointee
            if isinstance(pointee, ir.ArrayType):
                zero = ir.Constant(self.i32_type, 0)
                # Return the array pointer itself so caller can index further
                return self.builder.gep(storage, [zero, zero], inbounds=True)
            else:
                return self.builder.load(storage)   # T*

        if isinstance(node, AINode):
            # Recursively get a pointer into the sub-array
            idx     = self._visit(node.index)
            base    = self._visit_array_base(node.name)
            return self.builder.gep(base, [idx], inbounds=True)

        raise CodeGenError(f"Unexpected base in array index chain: {type(node).__name__}")

    # ═══════════════════════════════════════════════════════════════
    #  Leaf nodes
    # ═══════════════════════════════════════════════════════════════

    def _visit_Variable(self, node: Variable):
        ptr = self.variables.get(node.name)
        if ptr is None:
            raise CodeGenError(f"Undefined variable '{node.name}'")
        return self.builder.load(ptr)

    def _visit_Number(self,    node: Number):    return ir.Constant(self.i32_type,   node.value)
    def _visit_FloatNode(self, node: FloatNode): return ir.Constant(self.float_type, node.value)
    def _visit_Boolean(self,   node: Boolean):   return ir.Constant(self.bool_type,  1 if node.value else 0)

    # ═══════════════════════════════════════════════════════════════
    #  Control flow
    # ═══════════════════════════════════════════════════════════════

    def _visit_While(self, node: While):
        cond_block = self.builder.append_basic_block("while.cond")
        body_block = self.builder.append_basic_block("while.body")
        end_block  = self.builder.append_basic_block("while.end")

        self.builder.branch(cond_block)
        self.builder.position_at_end(cond_block)

        cond_val = self._visit(node.condition)
        # Level 6: Use _to_bool helper
        cmp = self._to_bool(cond_val)

        self.builder.cbranch(cmp, body_block, end_block)
        self.builder.position_at_end(body_block)

        for stmt in node.body:
            self._visit(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_block)

        self.builder.position_at_end(end_block)

    def _visit_If(self, node: If):
        cond_val = self._visit(node.condition)
        cmp = self._to_bool(cond_val)

        then_block = self.builder.append_basic_block("if.then")
        else_block = self.builder.append_basic_block("if.else")
        merge_block = self.builder.append_basic_block("if.merge")

        self.builder.cbranch(cmp, then_block, else_block)

        self.builder.position_at_end(then_block)
        for stmt in node.body:
            self._visit(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)

        self.builder.position_at_end(else_block)
        if node.else_body:
            for stmt in node.else_body:
                self._visit(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)

        self.builder.position_at_end(merge_block)

    # ═══════════════════════════════════════════════════════════════
    #  Output & return
    # ═══════════════════════════════════════════════════════════════

    def _visit_Return(self, node: Return):
        self.builder.ret(self._visit(node.value))

    def _visit_Print(self, node: Print):
        val = self._visit(node.value)
        val = self._coerce_float(val)           
        fmt = self.builder.bitcast(self._fmt_ptr, self.i8_ptr)
        self.builder.call(self.printf, [fmt, val])

    # ═══════════════════════════════════════════════════════════════
    #  Utilities
    # ═══════════════════════════════════════════════════════════════

    def _coerce_float(self, val: ir.Value) -> ir.Value:
        """Convert an i32 to double if necessary."""
        if val.type == self.i32_type:
            return self.builder.sitofp(val, self.float_type)
        return val

    def _to_bool(self, val: ir.Value) -> ir.Value:
        """Helper to convert any type to an i1 boolean for branching."""
        if val.type == self.bool_type:
            return val
        if val.type == self.float_type:
            return self.builder.fcmp_ordered("!=", val, ir.Constant(self.float_type, 0.0))
        return self.builder.icmp_signed("!=", val, ir.Constant(self.i32_type, 0))

    def _decay_to_pointer(self, val: ir.Value) -> ir.Value:
        """If val is a fixed-size array value [N x T], GEP to its first element."""
        if isinstance(val.type, ir.ArrayType):
            # val is a constant array — we need to alloca it first
            tmp = self.builder.alloca(val.type)
            self.builder.store(val, tmp)
            zero = ir.Constant(self.i32_type, 0)
            return self.builder.gep(tmp, [zero, zero], inbounds=True)
        return val

    # ═══════════════════════════════════════════════════════════════
    #  JIT execution
    # ═══════════════════════════════════════════════════════════════

    def execute(self):
        llvm_ir  = str(self.module)
        mod      = llvm.parse_assembly(llvm_ir)
        mod.verify()

        target   = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        engine   = llvm.create_mcjit_compiler(mod, target_machine)
        engine.finalize_object()
        engine.run_static_constructors()

        import ctypes
        main_ptr = engine.get_function_address("main")
        ctypes.CFUNCTYPE(ctypes.c_int)(main_ptr)()