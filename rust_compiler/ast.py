class ASTNode:
    # 抽象语法树（AST）的所有节点的基类
    # 定义了一个统一的打印方法，子类将覆盖（Override）它以实现各树形结构的递归打印
    def print_node(self, indent=0):
        pass

class Program(ASTNode):
    # 程序根节点，是整棵树的入口，通常包含一系列自上而下的顶级声明（如多个函数声明）
    def __init__(self, declarations):
        self.declarations = declarations  # 声明列表数组

    def print_node(self, indent=0):
        # 按照当前层级的缩进(indent)来打印带有缩进级别的节点名称
        print("  " * indent + "Program")
        # 遍历所有的声明，向下传递递增1的缩进级别
        for decl in self.declarations:
            decl.print_node(indent + 1)

class FunctionDecl(ASTNode):
    # 函数声明节点（例如: fn main(mut a: i32) -> i32 { ... } ）
    def __init__(self, name, params, ret_type, body):
        self.name = name       # 函数名（如 main）
        self.params = params   # 形参列表（由 ParamNode 组成的数组）
        self.ret_type = ret_type # 函数的返回类型节点，如没有可为空(None)
        self.body = body       # 函数体，通常是一个块语句(Block)节点

    def print_node(self, indent=0):
        print("  " * indent + f"FunctionDecl: {self.name}")
        # 依次打印形参列表的信息
        if self.params:
            print("  " * (indent + 1) + "Params:")
            for p in self.params:
                p.print_node(indent + 2)
        # 如果存在返回类型，则调用类型节点的打印
        if self.ret_type:
            print("  " * (indent + 1) + "ReturnType:")
            self.ret_type.print_node(indent + 2)
        # 打印函数的主体（Block块）
        print("  " * (indent + 1) + "Body:")
        self.body.print_node(indent + 2)

class LetStmt(ASTNode):
    # 变量声明语句节点 (例如: let mut a: i32 = 10;)
    def __init__(self, name, is_mut, type_, expr):
        self.name = name       # 变量名 (标识符字符串)
        self.is_mut = is_mut   # 布尔值，判断是否具有 mut 关键字
        self.type = type_      # 指定的类型信息 (如 TypeI32)，如果是隐式类型推导则为 None
        self.expr = expr       # 绑定的右值表达式（= 后的部分），如果只是声明无赋值则为 None

    def print_node(self, indent=0):
        print("  " * indent + f"LetStmt: mut={self.is_mut}, name={self.name}")
        if self.type:  # 如果显式带有类型
            self.type.print_node(indent + 1)
        if self.expr:  # 如果进行了初始赋值
            self.expr.print_node(indent + 1)

class Block(ASTNode):
    # 语句块节点（由 `{` 开头，`}` 结尾），包含一组顺序执行的语句
    def __init__(self, statements):
        self.statements = statements  # 块中所有语句对象的列表

    def print_node(self, indent=0):
        print("  " * indent + "Block")
        for stmt in self.statements:
            stmt.print_node(indent + 1)  # 递归调用块中每一条语句自己的缩进打印函数

class AssignStmt(ASTNode):
    # 基础的变量赋值语句节点（例如: a = 10;），不是第一次声明(Let)
    def __init__(self, lvalue, expr):
        self.lvalue = lvalue   # 等号左边的受体，通常也是个 ASTNode（比如 Identifer 节点）
        self.expr = expr       # 等号右边的产生结果的表达式节点

    def print_node(self, indent=0):
        print("  " * indent + "AssignStmt")
        self.lvalue.print_node(indent + 1)
        self.expr.print_node(indent + 1)

class ReturnStmt(ASTNode):
    # 函数的 return 返回语句节点
    def __init__(self, expr):
        self.expr = expr       # 返回的表达式内容；如果仅是 "return;" 则是 None

    def print_node(self, indent=0):
        print("  " * indent + "ReturnStmt")
        if self.expr:  # 若带有返回的实质内容，则向下打印该表达式结构
            self.expr.print_node(indent + 1)

class IfStmt(ASTNode):
    # If 条件分支语句节点
    def __init__(self, condition, body, else_body=None):
        self.condition = condition # 条件表达式节点（一般运算后是个布尔结果）
        self.body = body           # 条件为真时执行的分支代码块 (Block)
        self.else_body = else_body # 可选的 else 分支 (Block 或 IfStmt)

    def print_node(self, indent=0):
        print("  " * indent + "IfStmt")
        self.condition.print_node(indent + 1)  # 打印条件分支表达式
        self.body.print_node(indent + 1)       # 打印执行内容块
        if self.else_body:
            print("  " * (indent + 1) + "Else")
            self.else_body.print_node(indent + 2)

class WhileStmt(ASTNode):
    # While 循环语句节点
    def __init__(self, condition, body):
        self.condition = condition # 执行循环的条件控制表达式节点
        self.body = body           # 若满足条件则触发执行的循环体代码块 (Block)

    def print_node(self, indent=0):
        print("  " * indent + "WhileStmt")
        self.condition.print_node(indent + 1)
        self.body.print_node(indent + 1)

class ForStmt(ASTNode):
    # For 循环语句节点 (for [mut] name in iterable { ... })
    def __init__(self, name, is_mut, iterable, body):
        self.name = name
        self.is_mut = is_mut
        self.iterable = iterable
        self.body = body

    def print_node(self, indent=0):
        print("  " * indent + f"ForStmt: mut={self.is_mut}, name={self.name}")
        self.iterable.print_node(indent + 1)
        self.body.print_node(indent + 1)

class LoopStmt(ASTNode):
    # loop 语句节点 (loop { ... })
    def __init__(self, body):
        self.body = body

    def print_node(self, indent=0):
        print("  " * indent + "LoopStmt")
        self.body.print_node(indent + 1)

class BreakStmt(ASTNode):
    # break 语句节点
    def print_node(self, indent=0):
        print("  " * indent + "BreakStmt")

class ContinueStmt(ASTNode):
    # continue 语句节点
    def print_node(self, indent=0):
        print("  " * indent + "ContinueStmt")

class EmptyStmt(ASTNode):
    # 空的语句节点，例如单独的半角分号 `;`
    def print_node(self, indent=0):
        print("  " * indent + "EmptyStmt")

class NumberLit(ASTNode):
    # 表示硬编码的数字字面量终结节点
    def __init__(self, value):
        self.value = value     # 提取出的数值字符串，如 '123'

    def print_node(self, indent=0):
        print("  " * indent + f"NumberLit: {self.value}")

class Identifier(ASTNode):
    # 表示变量名或函数名这些自定义名称的标识符节点
    def __init__(self, name):
        self.name = name       # 标识符的具体名字，如 'x', 'my_func'

    def print_node(self, indent=0):
        print("  " * indent + f"Identifier: {self.name}")

class BinaryExpr(ASTNode):
    # 抽象出来的二元表达式（如加减法、比较、赋值右侧运算等 a < b，a + b，a * b）
    # 这是建立四则运算优先级的核心节点载体
    def __init__(self, op, left, right):
        self.op = op           # 操作符枚举或字符值（如 '+' 或 '=='）
        self.left = left       # 二元操作符左侧的子表达式树节点
        self.right = right     # 二元操作符右侧的子表达式树节点

    def print_node(self, indent=0):
        print("  " * indent + f"BinaryExpr: {self.op}")
        self.left.print_node(indent + 1)
        self.right.print_node(indent + 1)

class RefExpr(ASTNode):
    # 借用表达式节点 (&expr / &mut expr)
    def __init__(self, is_mut, target):
        self.is_mut = is_mut
        self.target = target

    def print_node(self, indent=0):
        print("  " * indent + f"RefExpr: mut={self.is_mut}")
        self.target.print_node(indent + 1)

class DerefExpr(ASTNode):
    # 解引用表达式节点 (*expr)
    def __init__(self, target):
        self.target = target

    def print_node(self, indent=0):
        print("  " * indent + "DerefExpr")
        self.target.print_node(indent + 1)

class RangeExpr(ASTNode):
    # 范围表达式节点 (expr .. expr)
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def print_node(self, indent=0):
        print("  " * indent + "RangeExpr")
        self.start.print_node(indent + 1)
        self.end.print_node(indent + 1)

class CallExpr(ASTNode):
    # 函数调用表达式节点 (例如 func(arg1, arg2) )
    def __init__(self, name, args):
        self.name = name     # 被调用的函数名字符串
        self.args = args     # 实参列表，是多个表达式节点组成的数组

    def print_node(self, indent=0):
        print("  " * indent + f"CallExpr: {self.name}")
        for arg in self.args:
            arg.print_node(indent + 1)

class TypeI32(ASTNode):
    # 特定的数据类型节点对于i32，作为声明里的类型标识符存在
    def print_node(self, indent=0):
        print("  " * indent + "Type: i32")

class TypeRef(ASTNode):
    # 引用类型节点 (&T / &mut T)
    def __init__(self, is_mut, inner_type):
        self.is_mut = is_mut
        self.inner_type = inner_type

    def print_node(self, indent=0):
        label = "Type: &mut" if self.is_mut else "Type: &"
        print("  " * indent + label)
        self.inner_type.print_node(indent + 1)

class ParamNode(ASTNode):
    # 函数头部专用的形参节点（如 mut x: i32）
    def __init__(self, is_mut, name, type_):
        self.is_mut = is_mut   # 表明参数是否可写修改
        self.name = name       # 传参的名字
        self.type = type_      # 要求的类型节点

    def print_node(self, indent=0):
        print("  " * indent + f"Param: {self.name}, mut={self.is_mut}")
        self.type.print_node(indent + 1)
