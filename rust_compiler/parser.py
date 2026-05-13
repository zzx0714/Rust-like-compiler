from compiler_token import TokenType
import ast

class ParserError(Exception):
    # 自定义语法分析错误：在识别出非预期的 Token 时抛出
    pass

class Parser:
    # 语法分析器：采用递归下降分析法（Recursive Descent Parsing）
    # 通过读取词法分析器(lexer)输出的一个个Token，去构建出具备层级结构的抽象语法树(AST)
    def __init__(self, lexer):
        self.lexer = lexer
        # 初始化时自动拿取第一个 Token
        self.current_token = self.lexer.next_token()

    def consume(self, token_type):
        # 消费指定的 Token：将当前持有的 Token 与期望的 Token 类型匹配测试
        # 若匹配成功，说明符合语法规则，则继续加载（向前游走）下一个 Token
        if self.current_token.type == token_type:
            self.current_token = self.lexer.next_token()
        else:
            # 否则，立即抛出错误信息，携带具体的行号和误匹配原因来停止分析过程
            raise ParserError(f"Expected {token_type.name}, got {self.current_token.type.name} at line {self.current_token.line}")

    def parse_program(self):
        # 整个解析的入口，作为程序的根节点（Program）
        declarations = []
        # 由于我们设计的Rust子集最外层只有各种函数定义，因此一直解析函数指到文件结尾标号EOF
        while self.current_token.type != TokenType.EOF:
            declarations.append(self.parse_function())
        return ast.Program(declarations)

    def parse_function(self):
        # 对应产生式：fn ID ( param_list ) [-> type] Block
        self.consume(TokenType.FN)         # "fn" 关键字
        name = self.current_token.value    # 获取函数名称
        self.consume(TokenType.ID)         # "ID" 标识符
        self.consume(TokenType.LPAREN)     # "(" 左括号
        params = self.parse_param_list()   # 调用形参解析方法，获取参数构成的列表
        self.consume(TokenType.RPAREN)     # ")" 右括号
        
        # 可选部分的返回类型，如果接下来遇到 "->" 箭头，则说明指明了返回类型
        ret_type = None
        if self.current_token.type == TokenType.ARROW:
            self.consume(TokenType.ARROW)
            ret_type = self.parse_type()   # 获取紧随其后的返回类型
            
        body = self.parse_block()          # 剩下的部分必定是函数体代码块
        # 组装返回相应的 AST 节点
        return ast.FunctionDecl(name, params, ret_type, body)

    def parse_param_list(self):
        # 解析函数定义头部的多个参数形参序列，例如：mut a:i32, b:i32
        params = []
        # 如果不是紧接着立刻遇到右括号')',说明有参数存在
        if self.current_token.type != TokenType.RPAREN:
            # 尝试获取可选的 `mut` 关键字
            is_mut = False
            if self.current_token.type == TokenType.MUT:
                is_mut = True
                self.consume(TokenType.MUT)
            name = self.current_token.value
            self.consume(TokenType.ID)       # 参数名
            self.consume(TokenType.COLON)    # 参数名和类型通过分号':'隔离
            type_ = self.parse_type()        # 解析类型对象
            params.append(ast.ParamNode(is_mut, name, type_))
            
            # 使用 while 不断检测接下来的逗号并处理同级别的后续参数
            while self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                is_mut = False
                if self.current_token.type == TokenType.MUT:
                    is_mut = True
                    self.consume(TokenType.MUT)
                name = self.current_token.value
                self.consume(TokenType.ID)
                self.consume(TokenType.COLON)
                type_ = self.parse_type()
                params.append(ast.ParamNode(is_mut, name, type_))
        return params

    def parse_type(self):
        # 检查是否是内置规定的已知类型标识符（当前项目只有i32）
        if self.current_token.type == TokenType.AMP:
            self.consume(TokenType.AMP)
            is_mut = False
            if self.current_token.type == TokenType.MUT:
                is_mut = True
                self.consume(TokenType.MUT)
            inner = self.parse_type()
            return ast.TypeRef(is_mut, inner)
        if self.current_token.type == TokenType.I32:
            self.consume(TokenType.I32)
            return ast.TypeI32()
        raise ParserError(f"Expected Type at line {self.current_token.line}")

    def parse_block(self):
        # `{ statement_list }` 块级作用域解析器
        self.consume(TokenType.LBRACE)   # "{" 左大括号
        statements = []
        # 块直到遇到右花括号 `}` 才会停止关闭，不断循环吞入各种内嵌语句
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            statements.append(self.parse_statement())
        self.consume(TokenType.RBRACE)   # "}" 右花括号，代表结束收口
        return ast.Block(statements)

    def parse_statement(self):
        # 大分拣中心，通过判断各种分支的开头关键字来指派给负责具体的解析函数
        if self.current_token.type == TokenType.SEMI:
            self.consume(TokenType.SEMI)      # 空语句 ';' 
            return ast.EmptyStmt()
        elif self.current_token.type == TokenType.RETURN:
            return self.parse_return_stmt()   # 遇到 return，切入返回值规则链
        elif self.current_token.type == TokenType.LET:
            return self.parse_let_stmt()      # 遇到 let，切入变量声明规则链
        elif self.current_token.type == TokenType.IF:
            return self.parse_if_stmt()       # 遇到 if 控制流分支
        elif self.current_token.type == TokenType.WHILE:
            return self.parse_while_stmt()    # 遇到 while 循环流分支
        elif self.current_token.type == TokenType.FOR:
            return self.parse_for_stmt()      # 遇到 for 循环流分支
        elif self.current_token.type == TokenType.LOOP:
            return self.parse_loop_stmt()     # 遇到 loop 循环流分支
        elif self.current_token.type == TokenType.BREAK:
            self.consume(TokenType.BREAK)
            self.consume(TokenType.SEMI)
            return ast.BreakStmt()
        elif self.current_token.type == TokenType.CONTINUE:
            self.consume(TokenType.CONTINUE)
            self.consume(TokenType.SEMI)
            return ast.ContinueStmt()
        else:
            # 没有明显语句头的情况下，我们默认它是以某个"表达式"(包含标识符修改)开始的值赋值算式
            expr = self.parse_expression()
            
            # 如果解析完这个前置表达式立刻遇上赋值符号 "="，说明这是一个由左值引导的更新赋值操作语句
            if self.current_token.type == TokenType.ASSIGN:
                self.consume(TokenType.ASSIGN)
                right = self.parse_expression()  # 解析赋值在右侧的表达式结果
                self.consume(TokenType.SEMI)
                return ast.AssignStmt(expr, right)
            
            # 或者该前置运算表达式纯粹是为了实现某个具有Side Effect的方法（例如独立成行的 func(2);）
            elif self.current_token.type == TokenType.SEMI:
                self.consume(TokenType.SEMI)
                return expr
                
            raise ParserError(f"Unexpected token {self.current_token.type.name} at line {self.current_token.line}")

    def parse_return_stmt(self):
        # return [expr] ;
        self.consume(TokenType.RETURN)
        expr = None
        # 当这不是立刻结束的分号，说明return携带了具体的返回计算值的内容
        if self.current_token.type != TokenType.SEMI:
            expr = self.parse_expression()
        self.consume(TokenType.SEMI)
        return ast.ReturnStmt(expr)

    def parse_let_stmt(self):
        # let [mut] ID [: type] [= expr] ;
        self.consume(TokenType.LET)
        is_mut = False
        if self.current_token.type == TokenType.MUT:
            is_mut = True
            self.consume(TokenType.MUT)
            
        name = self.current_token.value
        self.consume(TokenType.ID)
        
        type_ = None
        # 是否声明了它的确定类型
        if self.current_token.type == TokenType.COLON:
            self.consume(TokenType.COLON)
            type_ = self.parse_type()
            
        expr = None
        # 是否跟随了一个初始赋予的值
        if self.current_token.type == TokenType.ASSIGN:
            self.consume(TokenType.ASSIGN)
            expr = self.parse_expression()
            
        self.consume(TokenType.SEMI)
        return ast.LetStmt(name, is_mut, type_, expr)

    def parse_if_stmt(self):
        # if expr block
        self.consume(TokenType.IF)
        condition = self.parse_expression()  # 紧跟着的是真假判断条件表达式
        body = self.parse_block()            # 以及一个运行该逻辑的代码块
        else_body = None
        if self.current_token.type == TokenType.ELSE:
            self.consume(TokenType.ELSE)
            if self.current_token.type == TokenType.IF:
                else_body = self.parse_if_stmt()
            else:
                else_body = self.parse_block()
        return ast.IfStmt(condition, body, else_body)

    def parse_while_stmt(self):
        # while cond block
        self.consume(TokenType.WHILE)
        condition = self.parse_expression()
        body = self.parse_block()
        return ast.WhileStmt(condition, body)

    def parse_for_stmt(self):
        # for [mut] ID in iterable block
        self.consume(TokenType.FOR)
        is_mut = False
        if self.current_token.type == TokenType.MUT:
            is_mut = True
            self.consume(TokenType.MUT)
        name = self.current_token.value
        self.consume(TokenType.ID)
        self.consume(TokenType.IN)
        iterable = self.parse_iterable()
        body = self.parse_block()
        return ast.ForStmt(name, is_mut, iterable, body)

    def parse_loop_stmt(self):
        # loop block
        self.consume(TokenType.LOOP)
        body = self.parse_block()
        return ast.LoopStmt(body)

    def parse_iterable(self):
        # iterable -> expr .. expr
        start = self.parse_expression()
        self.consume(TokenType.DOTDOT)
        end = self.parse_expression()
        return ast.RangeExpr(start, end)

    # =============== 核心：四级优先级表达式层序解析 =============== #
    # 该块函数从高到低排列，巧妙解决左递归导致进入死循环（死堆栈）的经典难题
    # `parse_expression` 等级在最宏观的外层，它本质向下委托调取更低优先级的加减乘除与比较节点

    def parse_expression(self):
        # 表达式最顶层为逻辑与比较级别
        return self.parse_comparison()

    def parse_comparison(self):
        # 解析如： <=  != ==  一类具有对比性质的等级语句
        node = self.parse_addsub()  # 拿到属于下一优先级的基本表达式树块（如算术块）
        
        # 左结合性的体现运用到了一个平铺的 while 循环，而不是深层嵌套堆加（用来解决左递归）
        # 如果当前符号是比较符
        while self.current_token.type in (TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NEQ):
            op = self.current_token.value
            self.consume(self.current_token.type)
            # 通过获取到同级别的 `parse_addsub` 向右发展出 BinaryExpr 新根
            node = ast.BinaryExpr(op, node, self.parse_addsub())
        return node

    def parse_addsub(self):
        # 第三级优先级： 加、减法
        # 将左手边托付给处理优先级更高的项（乘、除部分）
        node = self.parse_term()
        # 继续捕获连续相加减：`A + B - C`
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token.value
            self.consume(self.current_token.type)
            # 重构出当前层级的 Binary 父节点
            node = ast.BinaryExpr(op, node, self.parse_term())
        return node

    def parse_term(self):
        # 第四优先级：乘、除法 (优先级强于加减法，因此它们最先被切分与合并聚合到一块)
        node = self.parse_factor()
        while self.current_token.type in (TokenType.MUL, TokenType.DIV):
            op = self.current_token.value
            self.consume(self.current_token.type)
            node = ast.BinaryExpr(op, node, self.parse_factor())
        return node

    def parse_factor(self):
        # 最底层因子层：只可能是一个原子不可分割项（比如纯数字字面量NUM，纯单体变量标识符ID）或者是个硬制提升优先级的括号(...)
        token = self.current_token
        # 借用表达式 & / &mut
        if token.type == TokenType.AMP:
            self.consume(TokenType.AMP)
            is_mut = False
            if self.current_token.type == TokenType.MUT:
                is_mut = True
                self.consume(TokenType.MUT)
            target = self.parse_factor()
            return ast.RefExpr(is_mut, target)
        # 解引用表达式 *
        if token.type == TokenType.MUL:
            self.consume(TokenType.MUL)
            target = self.parse_factor()
            return ast.DerefExpr(target)
        # 1. 如果它是单纯的数字
        if token.type == TokenType.NUM:
            self.consume(TokenType.NUM)
            return ast.NumberLit(token.value)
        # 2. 标识符
        elif token.type == TokenType.ID:
            name = token.value
            self.consume(TokenType.ID)
            
            # 若这个 ID 后恰巧连着一个左括号 '('，则这就不仅是一个单独拿出来当作值的简单变量，而是一个调用函数的算子 (类似 foo(...) 表达式)
            if self.current_token.type == TokenType.LPAREN:
                self.consume(TokenType.LPAREN)
                args = self.parse_arg_list()  # 读取所有实参
                self.consume(TokenType.RPAREN)
                return ast.CallExpr(name, args)  # 还原成调用型节点并返回
                
            return ast.Identifier(name)  # 若不带括号只是简单变量
            
        # 3. 遇到一个最高优先级的圆括号(...)
        elif token.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            # 让在最开始的源头表达式引擎替我们来对包裹在被括号圈禁里的东西开辟一种新生且完全独立的解析周期
            node = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return node
            
        # 若是以上三种类型之外的符号（比如突然蹦出一个不能计算的 '+'），肯定就是语法的彻底硬伤报错崩溃了
        raise ParserError(f"Unexpected factor token {token.type.name} at line {token.line}")

    def parse_arg_list(self):
        # 处理函数调用时传输的实质性的表达式参数组
        args = []
        if self.current_token.type != TokenType.RPAREN:
            # 第一项没有用逗号隔离，直接进行独立的算术逻辑评估
            args.append(self.parse_expression())
            # 后面的不断尝试越过 ',' 获取
            while self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                args.append(self.parse_expression())
        return args
