import re  # 导入正则表达式模块（虽然目前代码中未使用，但常用于更复杂的词法分析器中）
from compiler_token import Token, TokenType  # 从自定义的 compiler_token.py 模块中导入 Token 类和 TokenType 枚举类型

class LexerError(Exception):
    # 定义词法分析器专属的异常类，继承自 Python 内置的 Exception 类
    # 当词法分析过程中遇到无法识别的字符时，我们将抛出此异常
    pass

class Lexer:
    # Lexer（词法分析器）类，负责将原始源代码文本读入，并转化成一个个有意义的 Token (词法单元)
    def __init__(self, source_code: str):
        # 初始化词法分析器，接收源代码字符串作为输入
        self.source = source_code  # 将完整的源代码字符串保存在对象属性中
        self.pos = 0  # 初始化当前字符的索引位置号，指向源码字符串的开头（索引为0）
        self.line = 1  # 初始化当前所在的行号为1，用于在报错或记录Token时追踪位置
        # 初始化当前正在处理的字符
        # 如果源码不为空，取第一个字符；否则将其置为 None 表示已到文件末尾(EOF)
        self.current_char = self.source[self.pos] if self.source else None
        
        # 预先构建一个关键字字典，将形如 "if": TokenType.IF 的键值对存入字典
        # 这样在识别出标识符后，只需查表就能在 常数时间(O(1)) 内判断它是否是关键字
        self.keywords = {
            # 遍历 TokenType 枚举，筛选出名字不是 ID、NUM 和 EOF，并且其值都是字母或数字（支持 i32）的枚举项
            t.value: t for t in TokenType if t.name not in ["ID", "NUM", "EOF"] and t.value.isalnum()
        }
        
    def advance(self):
        # 使词法分析器的指针向前移动一个字符，并更新 current_char 和行号
        self.pos += 1  # 索引位置加 1
        if self.pos < len(self.source):  # 检查新的索引位置是否在源码长度范围内
            if self.current_char == '\n':  # 如果刚好越过了一个换行符
                self.line += 1  # 则将当前行号计数器加 1
            self.current_char = self.source[self.pos]  # 更新当前字符为新位置的字符
        else:
            # 如果索引位置已经超出或等于源码长度，说明已经读取完毕
            self.current_char = None  # 将当前字符设为 None 表示文件结尾

    def peek(self):
        # 向前"偷看"下一个字符，但不移动实际的 pos 指针
        # 这在处理双字符运算符（如 '==' 或 '>=') 时非常有用
        peek_pos = self.pos + 1  # 计算下一个字符的位置索引
        if peek_pos < len(self.source):  # 检查这个下一个位置是否仍然在源码范围内
            return self.source[peek_pos]  # 如果在范围内，返回下一个位置的字符
        return None  # 如果已经到了源码末尾，返回 None

    def skip_whitespace(self):
        # 跳过源码中连续出现的空白字符（空格、制表符、换行符等）
        # 只要当前字符不是 None，并且它是一个空白字符，循环就继续
        while self.current_char is not None and self.current_char.isspace():
            if self.current_char == '\n':  # 顺便检查它是不是换行符
                self.line += 1  # 如果是换行，更新行号追踪
            self.pos += 1  # 指针向后移动一位
            # 更新当前的 current_char，并且在越界的时候赋予 None
            self.current_char = self.source[self.pos] if self.pos < len(self.source) else None

    def skip_comment(self):
        # 跳过源代码中的注释内容（包括单行注释 '//' 和多行注释 '/* */'）
        # 第一种情况：单行注释，当前字符是 '/' 且下一个字符也是 '/'
        if self.current_char == '/' and self.peek() == '/':
            # 只要没到文件末尾且没遇到换行符，就一直跳过（忽略注释行的所有内容）
            while self.current_char is not None and self.current_char != '\n':
                self.advance()  # 读取并跳过下一个字符
            self.advance()  # 读到换行符时，再次 advance 跳过这个换行符，正式结束单行注释
        
        # 第二种情况：多行注释，当前字符是 '/' 且下一个字符是 '*'
        elif self.current_char == '/' and self.peek() == '*':
            self.advance()  # 吃掉第一个 '/'
            self.advance()  # 吃掉第二个 '*'
            # 开始一直读取并跳过内容，直到找到闭合符号 '*/'
            while self.current_char is not None:
                # 如果当前遇到 '*' 且下一个字符刚好是 '/'
                if self.current_char == '*' and self.peek() == '/':
                    self.advance()  # 吃掉 '*'
                    self.advance()  # 吃掉 '/'
                    break  # 多行注释结束，退出循环
                self.advance()  # 如果不是结束符号，则继续跳过当前注释里的字符

    def _id(self):
        # 负责解析识别标识符（如变量名、函数名）以及语言内置的关键字
        result = ''  # 定义一个空字符串记录累积组成的标识符名字
        start_line = self.line  # 记录标识符起始的行号
        # 当遇到字母数字或下划线时，将其视为标识符的一部分（Rust的变量名规则类似）
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char  # 把当前合法字符拼接到结果中
            self.advance()  # 将指针移动到下一个字符
        
        # 当完整读完一个词后，检查该词是否在关键字字典（如 if, let, fn 等）中
        # 如果是，则返回对应的关键字 TokenType，否则默认赋予 TokenType.ID（视作普通标识符）
        token_type = self.keywords.get(result, TokenType.ID)
        # 将解析好的类型、字符串具体值、起始行号打包放入一个 Token 对象并返回
        return Token(token_type, result, start_line)

    def _number(self):
        # 负责解析识别源代码中出现的连续十进制数字（数字字面量）
        result = ''  # 用于累积数字字符串的变量
        start_line = self.line  # 记录数字字面量开始的行号
        # 只要当前字符不是 None 且是单纯的数字 (0-9)
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char  # 把当前数字字符拼加进去
            self.advance()  # 指针移动到下一个字符取值
        # 构造一个类型始终为 NUM 的 Token，并承载提取出来的数字串返回
        return Token(TokenType.NUM, result, start_line)

    def next_token(self) -> Token:
        # 核心方法：作为对外接口，按顺序进行扫描并产生返回的下一个合法的 Token
        # 只要还有字符没读完，就保持一个主循环尝试获取一个 Token
        while self.current_char is not None:
            # 1. 遇到空格、回车等无实质意义的空白字符，直接跳过并重新继续循化
            if self.current_char.isspace():
                self.skip_whitespace()  # 调用跳过空白函数
                continue  # 跳过后直接进入下一轮循环，寻找正式的Token字符
                
            # 2. 遇到可能的注释符号：'//' 也就是当前 '/' 并且 偷看到下一个是 '/' 或 '*'
            if self.current_char == '/' and (self.peek() == '/' or self.peek() == '*'):
                self.skip_comment()  # 把注释这部分全部当作无意义的内容消耗跳过
                continue  # 继续下一轮循环
                
            # 3. 遇到英文字母或者下划线，说明应该切入解析标识符或关键字的分支
            if self.current_char.isalpha() or self.current_char == '_':
                return self._id()  # 把解析权交给 _id()，返回其拿到的Token对象
                
            # 4. 遇到纯数字开头，那就一定是正在写一个常数数字了
            if self.current_char.isdigit():
                return self._number()  # 将解析权交给 _number() 函数
                
            # 如果上面的都无法匹配，那现在极大概率遇到了操作符、界符等特殊单双字符
            char = self.current_char  # 保存当前的专门字符备用
            start_line = self.line  # 保持正确的起始行号以向 Token 提供坐标
            
            # --- 5. 开始检查复合运算符（即两个字符组成且拥有自己专有语义范围）---
            # 如果当前是 '=' 并且它后面紧跟的还是 '='
            if char == '=' and self.peek() == '=':
                self.advance(); self.advance()  # 消耗掉这两个连续字符
                return Token(TokenType.EQ, "==", start_line)  # 打包出 '==' Token
            # 如果当前是 '!' 并且它后面紧跟的是 '='
            if char == '!' and self.peek() == '=':
                self.advance(); self.advance()  # 同样消耗两个字符
                return Token(TokenType.NEQ, "!=", start_line)  # 打包出 '!=' (不等于)
            # 如果当前是 '<' 且紧跟 '='
            if char == '<' and self.peek() == '=':
                self.advance(); self.advance()  # 消耗字符
                return Token(TokenType.LE, "<=", start_line)  # 打包出 '<=' (小于等于)
            # 如果当前是 '>' 且紧跟 '='
            if char == '>' and self.peek() == '=':
                self.advance(); self.advance()  # 消耗字符
                return Token(TokenType.GE, ">=", start_line)  # 打包出 '>=' (大于等于)
            # 如果当前是 '-' 且紧跟 '>'
            if char == '-' and self.peek() == '>':
                self.advance(); self.advance()  # 消耗字符
                return Token(TokenType.ARROW, "->", start_line)  # 打包出 '->' (通常用于指定返回类型)

            # --- 6. 如果不是长复合符，查阅是否是常用的单字符运算符 ---
            # 定义一个查表字典，用来把单字符映射为枚举 TokenType
            simple_tokens = {
                '=': TokenType.ASSIGN, '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.MUL, '/': TokenType.DIV, '<': TokenType.LT, '>': TokenType.GT,
                '&': TokenType.AMP, '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE, '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET, ';': TokenType.SEMI, ':': TokenType.COLON,
                ',': TokenType.COMMA, '.': TokenType.DOT
            }
            
            # 如果该单一特殊字符能在允许的字典表中查到
            if char in simple_tokens:
                self.advance()  # 仅仅把这唯一的一个字符消耗吃掉即可
                # 打包并返回对应的类型（如 '+' -> TokenType.PLUS）
                return Token(simple_tokens[char], char, start_line)
                
            # 如果运行到这，证明当前遇到了词法分析器根本不认识的瞎写字符 (比如中文字符，未指定的特殊符)
            # 抛出 LexerError，指明哪个字符出了问题以及发生在哪行，协助调试
            raise LexerError(f"Unexpected character '{char}' at line {self.line}")

        # 如果 while 循环最终跑完并自然结束，意味着源代码所有的字符都已经读取殆尽（读到了文件尾部 None）
        # 返回我们自定义的特殊 EOF（End of File）以通知语法分析阶段（Parser）任务结束
        return Token(TokenType.EOF, "#", self.line)

    def tokenize_all(self):
        # 便利工具库：连续贪婪地调用 next_token 获取所有 Token
        tokens = []  # 准备一个空列表，用于收集所有的令牌
        while True:  # 开启死循环
            t = self.next_token()  # 不停地伸手要下一个 Token
            tokens.append(t)  # 将获取到的 Token 追加进入列表
            if t.type == TokenType.EOF:  # 如果获取到的恰好是 EOF (结束) 标记
                break  # 终止掉收集循环
        return tokens  # 将打包好满满一列表的源码 Token 全部返回给外部调用者使用
