"""
An experimental JavaScript-to-JavaScript compiler.
"""
__title__ = 'jscompiler'
__version__ = '0.1-pre'
__license__ = 'BSD'


def process_args(argv=None):
    """
    Parse configuration arguments.
    """
    import sys
    import argparse
    DESCRIPTION = 'Minify JavaScript.'
    parser = argparse.ArgumentParser(prog=__title__, description=DESCRIPTION)
    parser.add_argument(
        '-v', '--version', action='version', version='%%(prog)s %s' % __version__
    )
    parser.add_argument(
        '-r', '--rename-locals', action='store_true', dest='rename',
        help='Rename local variables to shorter names when possible.'
    )
    parser.add_argument(
        '-o', '--output', type=argparse.FileType('wb'), dest='output',
        default=sys.stdout, metavar='FILENAME',
        help='The file to write the output to. Defaults to stdout.'
    )
    parser.add_argument(
        'input', metavar='FILENAME', type=argparse.FileType('rb'), nargs=1,
        help='The file to minify.'
    )
    if argv:
        options = parser.parse_args(argv)
    else:
        options = parser.parse_args()
    return options


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


def rename_ast(ast):
    """
    Rename locals in the AST, returning an AST object.
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


def main(argv=None):
    """
    Minify a file.
    """
    import sys
    from bigrig.parser import ParseException
    try:
        options = process_args(argv)
    except Exception, e:
        return 1
    try:
        ast = parse_input(options.input[0])
        if options.rename:
            ast = rename_ast(ast)
        write_ast(ast, options.output)
    except ParseException, e:
        sys.stderr.write(str(e))
        return 1
    except Exception, e:
        return 1
    return 0
    
