import sys
from lexer import Lexer
from parser import Parser, ParserError
from semantic import SemanticChecker, SemanticError
import traceback

def main():
    # 检查是否能够从命令行参数中获取到对应的代码源文件路径
    if len(sys.argv) < 2:
        print("Usage: python main.py <test_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    # 【文件输入阶段】加载目标的Rust代码文件内容用于解析
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    print("--- 词法分析 ---")
    # 【词法分析阶段】对源码进行扫描生成 Token 序列
    lexer = Lexer(source_code)
    try:
        # 获取所有切分完毕的 Token 并一一打印展示
        tokens = lexer.tokenize_all()
        for t in tokens:
            print(t)
    except Exception as e:
        # 如果抛出非法字符错误，抛出异常终止程序
        print(f"词法分析失败: {e}")
        sys.exit(1)

    print("\n--- 语法分析 ---")
    # 【语法分析阶段】依据生成的Token创建具有层次结构的 AST (抽象语法树)
    # 这里我们重新实例化一个 lexer 给 Parser，因为上一个 lexer 的指针已经游走到文件尾部了
    lexer = Lexer(source_code)
    parser = Parser(lexer)
    
    try:
        # 启动自顶向下的解析递归
        ast_root = parser.parse_program()
        # 成功拿到并输出整棵缩进风格的树结构
        ast_root.print_node()
        print("\n语法分析成功")

        checker = SemanticChecker()
        checker.check(ast_root)
        print("语义分析成功")
    except ParserError as e:
        # 捕捉在语法分析匹配中出现的各种不符合语法规则的错误抛出
        print(f"语法分析失败: {e}")
    except SemanticError as e:
        print(f"语义分析失败: {e}")
    except Exception as e:
        # 意料之外的系统型错误
        print(f"未知错误: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # 作为程序的入口调用方法
    main()
