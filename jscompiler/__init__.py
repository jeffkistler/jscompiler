"""
An experimental JavaScript-to-JavaScript compiler.
"""
__title__ = 'jscompiler'
__version__ = '0.1-pre'
__license__ = 'BSD'

def write_ast(ast, outfile):
    """
    Write an abstract syntax tree to a file.
    """
    from .code_consumer import make_print_consumer
    from .code_generator import generate_code
    consumer = make_print_consumer(outfile)
    generate_code(ast, consumer)

def parse_input(input):
    """
    Parse the file from the given input file object and return an abstract
    syntax tree.
    """
    from .locator_parser import make_file_parser
    parser = make_file_parser(input)
    return parser.parse()

def optimize_ast(ast):
    """
    Optimize the AST, returning an AST object.
    """
    from .rename import rename_locals
    return rename_locals(ast)

def write_ast(ast, outfile):
    """
    Write the optimized AST to the given file object.
    """
    from .code_consumer import make_print_consumer
    from .code_generator import generate_code
    consumer = make_print_consumer(outfile)
    generate_code(ast, consumer)

def main(argv):
    import sys
    with open(argv[1], 'rb') as infile:
        try:
            ast = parse_input(infile)
        except:
            return 1
        ast = optimize_ast(ast)
        write_ast(ast, sys.stdout)
    return 0
    
