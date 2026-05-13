import ast


class SemanticError(Exception):
    pass


class SemanticChecker:
    def __init__(self):
        self.scopes = []
        self.loop_depth = 0

    def check(self, program):
        self.scopes = [{}]
        self.loop_depth = 0
        self._check_program(program)

    def _push_scope(self):
        self.scopes.append({})

    def _pop_scope(self):
        self.scopes.pop()

    def _declare(self, name, is_mut):
        self.scopes[-1][name] = {"mut": is_mut, "type": None}

    def _declare_with_type(self, name, is_mut, type_info):
        self.scopes[-1][name] = {"mut": is_mut, "type": type_info}

    def _lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def _check_program(self, program):
        for decl in program.declarations:
            self._check_function(decl)

    def _check_function(self, func):
        self._push_scope()
        for param in func.params or []:
            param_type = self._type_from_ast(param.type)
            self._declare_with_type(param.name, param.is_mut, param_type)
        self._check_block_like(func.body)
        self._pop_scope()

    def _check_block_like(self, block):
        if isinstance(block, ast.BlockExpr):
            self._push_scope()
            for stmt in block.statements:
                self._check_statement(stmt)
            if block.tail_expr is not None:
                self._check_expr(block.tail_expr)
            self._pop_scope()
        elif isinstance(block, ast.Block):
            self._push_scope()
            for stmt in block.statements:
                self._check_statement(stmt)
            self._pop_scope()

    def _check_statement(self, stmt):
        if isinstance(stmt, ast.LetStmt):
            declared_type = None
            if stmt.type is not None:
                declared_type = self._type_from_ast(stmt.type)
            expr_type = None
            if stmt.expr is not None:
                expr_type = self._infer_expr_type(stmt.expr)
            if declared_type is not None and expr_type is not None:
                if not self._type_equal(declared_type, expr_type):
                    raise SemanticError(
                        f"Type mismatch in let '{stmt.name}': {self._type_str(declared_type)} vs {self._type_str(expr_type)}"
                    )
            final_type = declared_type if declared_type is not None else expr_type
            self._declare_with_type(stmt.name, stmt.is_mut, final_type)
            return
        if isinstance(stmt, ast.AssignStmt):
            self._check_assignment(stmt.lvalue)
            left_type = self._infer_lvalue_type(stmt.lvalue)
            right_type = self._infer_expr_type(stmt.expr)
            if left_type is not None and right_type is not None:
                if not self._type_equal(left_type, right_type):
                    raise SemanticError(
                        f"Type mismatch in assignment: {self._type_str(left_type)} vs {self._type_str(right_type)}"
                    )
            return
        if isinstance(stmt, ast.ReturnStmt):
            if stmt.expr is not None:
                self._check_expr(stmt.expr)
            return
        if isinstance(stmt, ast.IfStmt):
            self._check_expr(stmt.condition)
            self._check_block_like(stmt.body)
            if stmt.else_body is not None:
                if isinstance(stmt.else_body, ast.IfStmt):
                    self._check_statement(stmt.else_body)
                else:
                    self._check_block_like(stmt.else_body)
            return
        if isinstance(stmt, ast.WhileStmt):
            self._check_expr(stmt.condition)
            self.loop_depth += 1
            self._check_block_like(stmt.body)
            self.loop_depth -= 1
            return
        if isinstance(stmt, ast.ForStmt):
            iterable_type = self._infer_expr_type(stmt.iterable)
            if not self._is_iterable_type(iterable_type):
                raise SemanticError("For loop requires iterable (range or array)")
            self.loop_depth += 1
            self._push_scope()
            self._declare(stmt.name, stmt.is_mut)
            self._check_block_like(stmt.body)
            self._pop_scope()
            self.loop_depth -= 1
            return
        if isinstance(stmt, ast.LoopStmt):
            self.loop_depth += 1
            self._check_block_like(stmt.body)
            self.loop_depth -= 1
            return
        if isinstance(stmt, ast.BreakStmt):
            if stmt.expr is not None:
                self._infer_expr_type(stmt.expr)
            return
        if isinstance(stmt, ast.ContinueStmt):
            return
        if isinstance(stmt, ast.Block):
            self._check_block_like(stmt)
            return
        if isinstance(stmt, ast.BlockExpr):
            self._check_block_like(stmt)
            return
        self._check_expr(stmt)

    def _check_expr(self, expr):
        self._infer_expr_type(expr)

    def _infer_expr_type(self, expr):
        if expr is None:
            return None
        if isinstance(expr, ast.NumberLit):
            return self._type_i32()
        if isinstance(expr, ast.Identifier):
            info = self._lookup(expr.name)
            return info["type"] if info else None
        if isinstance(expr, ast.BinaryExpr):
            left = self._infer_expr_type(expr.left)
            right = self._infer_expr_type(expr.right)
            if left is not None and right is not None and self._type_equal(left, right):
                return left
            return self._type_i32()
        if isinstance(expr, ast.CallExpr):
            for arg in expr.args:
                self._infer_expr_type(arg)
            return None
        if isinstance(expr, ast.RefExpr):
            inner = self._infer_expr_type(expr.target)
            if inner is None:
                return None
            return self._type_ref(expr.is_mut, inner)
        if isinstance(expr, ast.DerefExpr):
            inner = self._infer_expr_type(expr.target)
            if inner and inner[0] == "ref":
                return inner[2]
            return None
        if isinstance(expr, ast.RangeExpr):
            self._infer_expr_type(expr.start)
            self._infer_expr_type(expr.end)
            return self._type_range(self._type_i32())
        if isinstance(expr, ast.ArrayLit):
            elem_type = None
            for elem in expr.elements:
                t = self._infer_expr_type(elem)
                if elem_type is None:
                    elem_type = t
                elif t is not None and not self._type_equal(elem_type, t):
                    raise SemanticError("Array literal element type mismatch")
            return self._type_array(elem_type, len(expr.elements))
        if isinstance(expr, ast.ArrayIndexExpr):
            arr_type = self._infer_expr_type(expr.array)
            self._infer_expr_type(expr.index)
            if arr_type and arr_type[0] == "array":
                return arr_type[1]
            return None
        if isinstance(expr, ast.IfExpr):
            self._infer_expr_type(expr.condition)
            then_type = self._infer_block_expr_type(expr.then_block)
            else_type = self._infer_block_expr_type(expr.else_block)
            if then_type is not None and else_type is not None and self._type_equal(then_type, else_type):
                return then_type
            return None
        if isinstance(expr, ast.LoopExpr):
            self.loop_depth += 1
            self._check_block_like(expr.body)
            self.loop_depth -= 1
            return None
        if isinstance(expr, ast.BlockExpr):
            return self._infer_block_expr_type(expr)
        return None

    def _infer_block_expr_type(self, block_expr):
        self._check_block_like(block_expr)
        if block_expr.tail_expr is None:
            return None
        return self._infer_expr_type(block_expr.tail_expr)

    def _infer_lvalue_type(self, lvalue):
        if isinstance(lvalue, ast.Identifier):
            info = self._lookup(lvalue.name)
            return info["type"] if info else None
        if isinstance(lvalue, ast.ArrayIndexExpr):
            arr_type = self._infer_expr_type(lvalue.array)
            self._infer_expr_type(lvalue.index)
            if arr_type and arr_type[0] == "array":
                return arr_type[1]
            return None
        if isinstance(lvalue, ast.DerefExpr):
            inner = self._infer_expr_type(lvalue.target)
            if inner and inner[0] == "ref":
                return inner[2]
        return None

    def _check_assignment(self, lvalue):
        if self.loop_depth <= 0:
            return
        name = self._base_identifier_name(lvalue)
        if not name:
            return
        info = self._lookup(name)
        if info and info["mut"] is False:
            raise SemanticError(f"Immutable variable '{name}' assigned in loop")

    def _base_identifier_name(self, node):
        if isinstance(node, ast.Identifier):
            return node.name
        if isinstance(node, ast.ArrayIndexExpr):
            return self._base_identifier_name(node.array)
        return None

    def _type_i32(self):
        return ("i32",)

    def _type_array(self, elem_type, size):
        return ("array", elem_type, size)

    def _type_ref(self, is_mut, inner):
        return ("ref", is_mut, inner)

    def _type_range(self, elem):
        return ("range", elem)

    def _type_from_ast(self, type_node):
        if isinstance(type_node, ast.TypeI32):
            return self._type_i32()
        if isinstance(type_node, ast.TypeRef):
            return self._type_ref(type_node.is_mut, self._type_from_ast(type_node.inner_type))
        if isinstance(type_node, ast.ArrayType):
            try:
                size = int(type_node.size)
            except (TypeError, ValueError):
                size = type_node.size
            return self._type_array(self._type_from_ast(type_node.elem_type), size)
        return None

    def _type_equal(self, left, right):
        return left == right

    def _type_str(self, type_info):
        if type_info is None:
            return "<unknown>"
        if type_info[0] == "i32":
            return "i32"
        if type_info[0] == "ref":
            prefix = "&mut " if type_info[1] else "&"
            return prefix + self._type_str(type_info[2])
        if type_info[0] == "array":
            return f"[{self._type_str(type_info[1])};{type_info[2]}]"
        if type_info[0] == "range":
            return "range"
        return "<unknown>"

    def _is_iterable_type(self, type_info):
        if type_info is None:
            return False
        if type_info[0] == "range":
            return True
        if type_info[0] == "array":
            return True
        return False
