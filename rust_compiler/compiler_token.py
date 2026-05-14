from enum import Enum

class TokenType(Enum):
    # 该枚举类定义了语言中可能出现的所有 Token 的类型
    # Keywords (保留字/关键字)
    FN = "fn"          # 函数声明关键字
    LET = "let"        # 变量声明关键字
    MUT = "mut"        # 可变变量修饰符
    I32 = "i32"        # 32位整型类型标识符
    IF = "if"          # if 分支语句关键字
    ELSE = "else"      # else 分支语句关键字 (暂时不用但预留)
    WHILE = "while"    # while 循环关键字
    RETURN = "return"  # 返回语句关键字
    FOR = "for"        # for 循环关键字 (拓展备用)
    IN = "in"          # in 关键字 (拓展备用)
    LOOP = "loop"      # loop 循环关键字 (拓展备用)
    BREAK = "break"    # 打断循环关键字 (拓展备用)
    CONTINUE = "continue"# 继续循环关键字 (拓展备用)

    # Identifiers & Literals (标识符与字面量)
    ID = "ID"          # 变量名、函数名等标识符
    NUM = "NUM"        # 数字类型的字面量

    # Operators & Delimiters (运算符与界符)
    ASSIGN = "="       # 赋值等号
    PLUS = "+"         # 加号
    MINUS = "-"        # 减号
    MUL = "*"          # 乘号
    DIV = "/"          # 除号
    EQ = "=="          # 判断相等符号
    GT = ">"           # 大于号
    GE = ">="          # 大于等于号
    LT = "<"           # 小于号
    LE = "<="          # 小于等于号
    NEQ = "!="         # 判断不等符号
    AMP = "&"          # 借用/引用符号 (拓展备用)
    LPAREN = "("       # 左小括号
    RPAREN = ")"       # 右小括号
    LBRACE = "{"       # 左大括号
    RBRACE = "}"       # 右大括号
    LBRACKET = "["     # 左中括号 (拓展备用)
    RBRACKET = "]"     # 右中括号 (拓展备用)
    SEMI = ";"         # 分号，通常用于语句结束
    COLON = ":"        # 冒号，通常用于类型声明
    COMMA = ","        # 逗号，分隔参数
    ARROW = "->"       # 箭头符号，通常用于表示函数返回类型
    DOTDOT = ".."      # 范围运算符 (for range)
    DOT = "."          # 点操作符，用于访问成员等 (拓展备用)

    EOF = "#"          # End Of File，指示源代码解析完毕的标识位

class Token:
    # Token 类是词法分析器输出的基本单位
    # 它将源代码中的一段字符串打包为一个拥有具体类型（TokenType）、取值和行号信息的对象
    def __init__(self, type_: TokenType, value: str, line: int):
        self.type = type_   # 当前Token的枚举类型（如 TokenType.NUM）
        self.value = value  # 当前Token的具体字符串取值（如 "123", "fn", "+" 等）
        self.line = line    # 该Token在源文件中开始的行号，这对于语法分析在报错时精准定位非常重要

    def __repr__(self):
        # 提供一个可读的字符串表示形式，方便调试或用 print 直接打印出 Token 信息
        return f"Token({self.type.name}, '{self.value}', Line: {self.line})"
