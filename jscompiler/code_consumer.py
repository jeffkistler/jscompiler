"""
Classes for consuming token events from code generators.
"""
from bigrig import token as t

LITERALS = frozenset((
    t.RETURN,
    t.NEW,
    t.DELETE,
    t.TYPEOF,
    t.NULL,
    t.THIS,
    t.FALSE,
    t.TRUE,
    t.THROW,
    t.IN,
    t.INSTANCEOF,
    t.TRY,
    t.FUNCTION,
    t.IF,
    t.ELSE,
    t.SWITCH,
    t.CASE,
    t.DEFAULT,
    t.WHILE,
    t.DO,
    t.FOR,
    t.BREAK,
    t.CONTINUE,
    t.VAR,
    t.WITH,
    t.CATCH,
    t.FINALLY,
    t.VOID,
    t.RESERVED,
    t.IDENTIFIER,
))

class BaseConsumer(object):
    """
    A base class for all consumer classes that simply passes all reported
    tokens to a generic method.
    """
    def report_token(self, token):
        raise NotImplemented()

    def report_number(self, token):
        self.report_token(token)

    def report_keyword(self, token):
        self.report_token(token)

    def report_literal(self, token):
        self.report_token(token)

    def report_identifier(self, token):
        self.report_token(token)

    def report_binary_op(self, token):
        self.report_token(token)

    def report_unary_op(self, token):
        self.report_token(token)

    def report_prefix_op(self, token):
        self.report_token(token)

    def report_postfix_op(self, token):
        self.report_token(token)

    def report_regexp(self, pattern):
        self.report_token(pattern)

class MinifiedPrintConsumer(BaseConsumer):
    """
    A consumer that prints to a stream with only necessary whitespace intact.
    """
    def __init__(self, stream):
        self.stream = stream
        self.last_token = None

    def last_was(self, type):
        return self.last_token and self.last_token.type == type

    def report_token(self, token):
        self.last_token = token
        self.stream.write(token.value)

    def report_space(self):
        self.report_token(t.Token(t.SPACE, u' '))

    def report_number(self, token):
        if self.last_token and self.last_token.type in LITERALS:
            self.report_space()
        self.report_token(token)

    def report_prefix_op(self, token):
        if token.type == t.INC and self.last_was(t.ADD):
            self.report_space()
        elif token.type == t.DEC and self.last_was(t.SUB):
            self.report_space()
        self.report_token(token)

    def report_unary_op(self, token):
        if (token.type == t.ADD and self.last_was(t.ADD)) or\
                (token.type == t.SUB and self.last_was(t.SUB)):
            self.report_space()
        self.report_token(token)

    def report_identifier(self, token):
        if self.last_token and self.last_token.type in LITERALS:
            self.report_space()
        self.report_token(token)

    def report_keyword(self, token):
        if self.last_token and self.last_token.type in LITERALS:
            self.report_space()
        self.report_token(token)

def make_print_consumer(stream, encoding='utf-8'):
    """
    Build a print consumer object for the given stream.
    """
    from codecs import getwriter
    StreamWriter = getwriter(encoding)
    writer = StreamWriter(stream)
    return MinifiedPrintConsumer(writer)

def print_string(ast, encoding='utf-8'):
    """
    Print an abstract syntax tree to a string.
    """
    from .code_generator import generate_code
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    stream = StringIO()
    consumer = make_print_consumer(stream, encoding)
    generate_code(ast, consumer)
    return stream.getvalue()

