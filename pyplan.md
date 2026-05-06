# 类Rust词法语法分析器项目计划

## 一、项目概述
用 Python 实现一个类Rust语言的词法分析器和语法分析器，仅完成必做语法规则。

## 二、必做语法规则清单
需要实现的产生式规则编号：
0.1 变量属性（mut）
0.2 类型（i32）
0.3 左值（ID）
1.1 基础程序（函数声明、语句块）
1.2 语句（空语句、语句串）
1.3 返回语句（return、return表达式）
1.4 函数输入（形参列表：mut ID : 类型）
1.5 函数输出（-> 类型）
2.0 变量声明（let mut ID、let mut ID : 类型）
2.1 变量声明语句
2.2 赋值语句（左值 = 表达式）
3.1 基本表达式（NUM、左值、括号）
3.2 比较运算（< <= > >= == !=）
3.3 加减运算（+ -）
3.4 乘除运算（* /）
3.5 函数调用（ID(实参列表)）
4.1 if语句（if 表达式 语句块，不含else）
5.0 循环语句（入口规则）
5.1 while循环（while 表达式 语句块）

## 三、项目文件结构
rust_compiler/
├── main.py # 主入口，读取文件、调用lexer和parser、输出结果
├── token.py # Token类型定义
├── lexer.py # 词法分析器
├── parser.py # 语法分析器（递归下降）
├── ast.py # AST节点定义
├── test_cases/ # 测试用例文件夹
│ ├── test_01.txt # 基础空程序
│ ├── test_02.txt # return语句
│ ├── test_03.txt # 函数参数和返回
│ ├── test_04.txt # 变量声明
│ ├── test_05.txt # 赋值语句
│ ├── test_06.txt # 表达式和比较
│ ├── test_07.txt # 函数调用
│ ├── test_08.txt # if语句
│ ├── test_09.txt # while循环
│ └── test_10.txt # 综合测试
└── output/ # 输出结果存放

text

## 四、词法分析器（lexer.py）功能需求
1. 支持的Token类型：
   - 关键字：fn, let, mut, i32, if, else, while, return, for, in, loop, break, continue
   - 标识符：字母开头，后跟字母或数字（不能与关键字相同）
   - 数值：数字序列
   - 运算符/界符：= + - * / == > >= < <= != & ( ) { } [ ] ; : , -> .
   - 注释：// 行注释、/* */ 块注释
   - 结束符：#

2. 关键处理规则：
   - 忽略空白字符（空格、换行、制表符）
   - 跳过注释内容
   - if123 识别为标识符（一个Token）
   - if=123 识别为三个Token：if、=、123
   - 所有Token需记录所在行号，用于错误定位

3. 核心方法：
   - next_token(): 返回下一个Token
   - peek_token(): 查看当前Token但不消耗
   - tokenize_all(): 返回整个Token列表

## 五、语法分析器（parser.py）功能需求
1. 实现方式：递归下降分析，每个非终结符对应一个解析函数

2. 产生式改写要点：
   - 消除左递归（表达式相关产生式）
   - 表达式按优先级分层：Factor → Term(乘除) → AddSub → Comparison → Expression
   - 运算符左结合性用while循环实现

3. 核心解析函数：
   - parse_program()          # 程序入口
   - parse_declaration()      # 声明
   - parse_function()         # 函数声明
   - parse_function_header()  # 函数头
   - parse_param_list()       # 形参列表
   - parse_block()            # 语句块
   - parse_statement()        # 语句分发
   - parse_return_stmt()      # return语句
   - parse_let_stmt()         # let声明语句
   - parse_assign_stmt()      # 赋值语句
   - parse_if_stmt()          # if语句
   - parse_while_stmt()       # while语句
   - parse_expression()       # 表达式（最高层）
   - parse_comparison()       # 比较表达式
   - parse_addsub()           # 加减表达式
   - parse_term()             # 乘除项
   - parse_factor()           # 因子（NUM/ID/括号/函数调用）
   - parse_lvalue()           # 左值
   - parse_arg_list()         # 实参列表
   - parse_var_attribute()    # 变量属性（mut/空）
   - parse_type()             # 类型（i32）

4. 错误处理：
   - 遇到语法错误时输出错误信息和行号
   - 尝试错误恢复（如跳过直到分号或右花括号）

## 六、AST节点类型（ast.py）
1. 语句节点：
   - Program（程序根节点）
   - FunctionDecl（函数声明）
   - Block（语句块）
   - ReturnStmt（返回语句）
   - LetStmt（变量声明语句）
   - AssignStmt（赋值语句）
   - ExprStmt（表达式语句）
   - IfStmt（if语句）
   - WhileStmt（while语句）
   - EmptyStmt（空语句）

2. 表达式节点：
   - NumberLit（数字字面量）
   - Identifier（标识符）
   - BinaryExpr（二元运算）
   - UnaryExpr（一元运算）
   - CallExpr（函数调用）
   - ParenExpr（括号表达式）

3. 类型节点：
   - TypeI32
   - VarAttribute（mut/不可变）

4. 打印方法：
   - 每个AST节点需实现打印方法，以树状结构输出分析结果

## 七、主程序（main.py）功能
1. 接收命令行参数：输入文件路径
2. 读取源文件内容
3. 调用词法分析器，输出Token列表
4. 调用语法分析器，输出AST树形结构
5. 如果分析成功，打印"分析成功"
6. 如果有错误，打印所有错误信息

运行示例：
```bash
python main.py test_cases/test_01.txt
八、测试用例覆盖
每个测试用例对应一个或多个必做规则：

test_01: 空函数体 (规则1.1)

test_02: return/return; (规则1.3)

test_03: 带参数和返回值的函数 (规则1.4,1.5)

test_04: let变量声明 (规则2.0,2.1)

test_05: 赋值语句 (规则2.2)

test_06: 表达式、比较、加减、乘除 (规则3.1-3.4)

test_07: 函数调用 (规则3.5)

test_08: if语句 (规则4.1)

test_09: while循环 (规则5.0,5.1)

test_10: 综合测试

九、开发建议
先实现token.py，定义所有Token类型

再实现lexer.py，用测试用例验证Token输出正确

然后实现ast.py，定义AST节点

最后实现parser.py，逐步添加语法规则

每添加一个语法规则，立即用对应测试用例验证

注意表达式优先级和左递归消除

处理边界情况：空语句块、空形参列表、嵌套表达式等

十、环境要求
Python 3.10+

VS Code + Python扩展

不使用第三方库，纯标准库实现

源代码文件使用UTF-8编码

十一、目标交付物
完整源代码（5个.py文件）

测试用例（10个.txt文件）

运行结果截屏或输出日志

设计文档（含词法状态转换图、语法分析流程）

报告PPT