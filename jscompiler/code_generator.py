"""
An abstract syntax tree walker that generates the minimal set of tokens
that results in the same tree and reports these tokens to a token
consumer.
"""
from bigrig import ast
from bigrig import token as t
from bigrig.visitor import NodeVisitor

from .precedence import precedence as get_precedence

NEEDS_SEMICOLON = (
    ast.DoWhileStatement,
    ast.ExpressionStatement,
    ast.ContinueStatement,
    ast.BreakStatement,
    ast.ReturnStatement,
    ast.VariableStatement,
)

BODY_MAY_NEED_SEMICOLON = (
    ast.WhileStatement, # body
    ast.WithStatement, # statement
    ast.ForStatement, # body
    ast.ForInStatement, # body
)

BINARY_OP_TO_TYPE = {
    u'=': t.ASSIGN,
    u'|=': t.ASSIGN_BITOR,
    u'^=': t.ASSIGN_BITXOR,
    u'&=': t.ASSIGN_BITAND,
    u'<<=': t.ASSIGN_LSH,
    u'>>=': t.ASSIGN_RSH,
    u'>>>=': t.ASSIGN_URSH,
    u'+=': t.ASSIGN_ADD,
    u'-=': t.ASSIGN_SUB,
    u'*=': t.ASSIGN_MUL,
    u'/=': t.ASSIGN_DIV,
    u'%=': t.ASSIGN_MOD,
    u',': t.COMMA,
    u'||': t.OR,
    u'&&': t.AND,
    u'|': t.BITOR,
    u'^': t.BITXOR,
    u'&': t.BITAND,
    u'<<': t.LSH,
    u'>>': t.RSH,
    u'>>>': t.URSH,
    u'+': t.ADD,
    u'-': t.SUB,
    u'*': t.MUL,
    u'/': t.DIV,
    u'%': t.MOD,
    u'==': t.EQ,
    u'!=': t.NE,
    u'===': t.SHEQ,
    u'!==': t.SHNE,
    u'<': t.LT,
    u'>': t.GT,
    u'<=': t.LE,
    u'>=': t.GE,
    u'instanceof': t.INSTANCEOF,
    u'in': t.IN,
}

UNARY_OP_TO_TYPE = {
    u'delete': t.DELETE,
    u'void': t.VOID,
    u'typeof': t.TYPEOF,
    u'++': t.INC,
    u'--': t.DEC,
    u'+': t.ADD,
    u'-': t.SUB,
    u'~': t.BITNOT,
    u'!': t.NOT,
}

class CodeGenerator(NodeVisitor):
    """
    Generates the minimal sequence of tokens that could result in
    an identical abstract syntax tree to the one visited.
    """
    def __init__(self, consumer=None):
        self.consumer = consumer
        self.marked_for_parens = set()
        super(CodeGenerator, self).__init__()

    def generate(self, ast):
        """
        The main entrypoint for walking a tree.
        """
        self.visit(ast)
        self.report_token(t.EOF, u'')

    #
    # Token utilities
    #

    def make_token(self, type, value):
        return t.Token(type, value)

    def report_token(self, type, value):
        token = self.make_token(type, value)
        if self.consumer:
            self.consumer.report_token(token)

    def report_number(self, value):
        token = self.make_token(t.DECIMAL, value)
        if self.consumer:
            self.consumer.report_number(token)

    def report_keyword(self, value):
        token = self.make_token(t.KEYWORD_TO_TYPE[value], value)
        if self.consumer:
            self.consumer.report_keyword(token)

    def report_identifier(self, value):
        token = self.make_token(t.IDENTIFIER, value)
        if self.consumer:
            self.consumer.report_identifier(token)

    def report_binary_op(self, value):
        if value in t.KEYWORD_TO_TYPE:
            self.report_keyword(value)
        else:
            type = BINARY_OP_TO_TYPE[value]
            token = self.make_token(type, value)
            if self.consumer:
                self.consumer.report_binary_op(token)

    def report_unary_op(self, value):
        if value in t.KEYWORD_TO_TYPE:
            self.report_keyword(value)
        else:
            type = UNARY_OP_TO_TYPE[value]
            token = self.make_token(type, value)
            if self.consumer:
                self.consumer.report_unary_op(token)

    def report_prefix_op(self, op):
        type = UNARY_OP_TO_TYPE[op]
        token = self.make_token(type, op)
        if self.consumer:
            self.consumer.report_prefix_op(token)

    def report_postfix_op(self, op):
        type = UNARY_OP_TO_TYPE[op]
        token = self.make_token(type, op)
        if self.consumer:
            self.consumer.report_postfix_op(token)

    def report_regexp(self, pattern):
        token = self.make_token(t.REGEXP, pattern)
        if self.consumer:
            self.consumer.report_regexp(token)

    def report_literal(self, value):
        type = t.LITERAL_TO_TYPE[value]
        token = self.make_token(type, value)
        if self.consumer:
            self.consumer.report_literal(token)

    #
    # Node utilities
    #

    def precedence(self, node):
        return get_precedence(node)

    def parenthesize(self, node):
        self.report_literal(u'(')
        self.visit(node)
        self.report_literal(u')')

    def needs_semicolon(self, node):
        if isinstance(node, BODY_MAY_NEED_SEMICOLON):
            node = getattr(node, 'body', getattr(node, 'statement', node))
        if isinstance(node, ast.IfStatement):
            if node.else_statement:
                node = node.else_statement
            elif node.then_statement:
                node = node.then_statement
            return True
        if isinstance(node, NEEDS_SEMICOLON):
            return True
        return False

    def maybe_semicolon(self, node):
        self.visit(node)
        if self.needs_semicolon(node):
            self.report_literal(u';')

    def maybe_parens(self, node, parent):
        parent_precedence = self.precedence(parent)
        child_precedence = self.precedence(node)
        if child_precedence < parent_precedence:
            self.parenthesize(node)
        else:
            self.visit(node)

    #
    # Generic
    #

    def visit_comma_list(self, node):
        last_index = len(node) - 1
        for i, element in enumerate(node):
            self.visit(element)
            if i < last_index:
                self.report_literal(u',')

    def visit_statement_list(self, statements):
        last_index = len(statements) - 1
        for i, statement in enumerate(statements):
            if i < last_index:
                self.maybe_semicolon(statement)
            else:
                self.visit(statement)

    def visit_unicode(self, node):
        self.report_identifier(node)

    #
    # Nodes
    #

    def visit_ArrayLiteral(self, node):
        self.report_literal(u'[')
        self.visit_comma_list(node.elements)
        self.report_literal(u']')

    def visit_Assignment(self, node):
        self.maybe_parens(node.target, node)
        self.report_binary_op(node.op)
        self.maybe_parens(node.value, node)

    def visit_BinaryOperation(self, node):
        self.maybe_parens(node.left, node)
        self.report_binary_op(node.op)
        right = node.right
        if self.precedence(right) <= self.precedence(node):
            self.parenthesize(right)
        else:
            self.visit(right)

    def visit_Block(self, node):
        self.report_literal(u'{')
        self.visit_statement_list(node.statements)
        self.report_literal(u'}')

    def visit_BracketProperty(self, node):
        self.maybe_parens(node.object, node)
        self.report_literal(u'[')
        self.visit(node.key)
        self.report_literal(u']')

    def visit_BreakStatement(self, node):
        self.report_keyword(u'break')

    def visit_CallExpression(self, node):
        self.maybe_parens(node.expression, node)
        self.report_literal(u'(')
        self.visit_comma_list(node.arguments)
        self.report_literal(u')')

    def visit_CaseClause(self, node):
        if node.label:
            self.report_keyword(u'case')
            self.visit(node.label)
        else:
            self.report_keyword(u'default')
        self.report_literal(u':')
        self.visit_statement_list(node.statements)

    def visit_CompareOperation(self, node):
        self.maybe_parens(node.left, node)
        self.report_binary_op(node.op)
        self.maybe_parens(node.right, node)

    def visit_Conditional(self, node):
        self.maybe_parens(node.condition, node)
        self.report_literal(u'?')
        self.maybe_parens(node.then_expression, node)
        self.report_literal(u':')
        self.maybe_parens(node.else_expression, node)

    def visit_ContinueStatement(self, node):
        self.report_keyword(u'continue')
        if node.target:
            self.visit(node.target)

    def visit_DeleteOperation(self, node):
        self.report_keyword(u'delete')
        self.visit(node.expression)

    def visit_DoWhileStatement(self, node):
        self.report_keyword(u'do')
        self.maybe_semicolon(node.body)
        self.report_keyword(u'while')
        self.parenthesize(node.condition)

    def visit_DotProperty(self, node):
        self.maybe_parens(node.object, node)
        self.report_literal(u'.')
        self.visit(node.key)

    def visit_Elision(self, node):
        pass

    def visit_EmptyStatement(self, node):
        self.report_literal(u';')

    def visit_ExpressionStatement(self, node):
        # Look if the leftmost node lexically is a FunctionExpression or
        # ObjectLiteral, if so mark it for parens
        def mark_leftmost_for_parens(node):
            left = None
            if isinstance(node, ast.PropertyAccess):
                left = node.object
            elif isinstance(node, (ast.PostfixCountOperation, ast.CallExpression)):
                left = node.expression
            elif isinstance(node, (ast.BinaryOperation, ast.CompareOperation)):
                left = node.left
            elif isinstance(node, ast.Assignment):
                left = node.target
            if self.precedence(node) > self.precedence(left):
                return
            if isinstance(left, (ast.FunctionExpression, ast.ObjectLiteral)):
                self.marked_for_parens.add(left)
                return
            elif left is not None:
                return mark_leftmost_for_parens(left)
        expression = node.expression
        mark_leftmost_for_parens(expression)
        self.visit(expression)

    def visit_FalseNode(self, node):
        self.report_keyword(u'false')

    def visit_ForInStatement(self, node):
        self.report_keyword(u'for')
        self.report_literal(u'(')
        self.visit(node.each)
        self.report_keyword(u'in')
        self.visit(node.enumerable)
        self.report_literal(u')')
        self.visit(node.body)

    def visit_ForStatement(self, node):
        self.report_keyword(u'for')
        self.report_literal(u'(')
        initialize = node.initialize
        if isinstance(initialize, ast.CompareOperation) and\
                initialize.op == u'in':
            self.parenthesize(initialize)
        else:
            self.visit(initialize)
        self.report_literal(u';')
        self.visit(node.condition)
        self.report_literal(u';')
        self.visit(node.next)
        self.report_literal(u')')
        self.visit(node.body)

    def visit_FunctionDeclaration(self, node):
        self.report_keyword(u'function')
        self.visit(node.name)
        self.report_literal(u'(')
        self.visit_comma_list(node.parameters)
        self.report_literal(u')')
        self.report_literal(u'{')
        self.visit_statement_list(node.body)
        self.report_literal(u'}')

    def visit_FunctionExpression(self, node):
        parens = node in self.marked_for_parens
        if parens:
            self.report_literal(u'(')
        self.report_keyword(u'function')
        self.visit(node.name)
        self.report_literal(u'(')
        self.visit_comma_list(node.parameters)
        self.report_literal(u')')
        self.report_literal(u'{')
        self.visit_statement_list(node.body)
        self.report_literal(u'}')
        if parens:
            self.report_literal(u')')
            self.marked_for_parens.discard(node)

    def visit_IfStatement(self, node):
        self.report_keyword(u'if')
        self.parenthesize(node.condition)
        self.visit(node.then_statement)
        if node.else_statement:
            if self.needs_semicolon(node.then_statement):
                self.report_literal(u';')
            self.report_keyword(u'else')
            self.visit(node.else_statement)

    def visit_LabelledStatement(self, node):
        self.report_identifier(node.label)
        self.report_literal(u':')
        self.visit(node.statement)

    def visit_Name(self, node):
        self.report_identifier(node.value)

    def visit_NewExpression(self, node):
        self.report_keyword(u'new')
        self.maybe_parens(node.expression, node)
        if node.arguments is not None:
            self.report_literal(u'(')
            self.visit_comma_list(node.arguments)
            self.report_literal(u')')
    
    def visit_NullNode(self, node):
        self.report_keyword(u'null')

    def visit_NumberLiteral(self, node):
        self.report_number(node.value)

    def visit_ObjectLiteral(self, node):
        parens = node in self.marked_for_parens
        if parens:
            self.report_literal(u'(')
        self.report_literal(u'{')
        self.visit_comma_list(node.properties)
        self.report_literal(u'}')
        if parens:
            self.report_literal(u')')
            self.marked_for_parens.remove(node)
    
    def visit_ObjectProperty(self, node):
        self.visit(node.name)
        self.report_literal(u':')
        self.visit(node.value)

    def visit_PostfixCountOperation(self, node):
        self.maybe_parens(node.expression, node)
        self.report_postfix_op(node.op)

    def visit_PrefixCountOperation(self, node):
        self.report_prefix_op(node.op)
        self.maybe_parens(node.expression, node)

    def visit_Program(self, node):
        self.visit_statement_list(node.statements)

    def visit_PropertyName(self, node):
        self.report_identifier(node.value)

    def visit_RegExpLiteral(self, node):
        self.report_regexp(node.pattern)
        if node.flags:
            self.report_identifier(node.flags)

    def visit_ReturnStatement(self, node):
        self.report_keyword(u'return')
        self.visit(node.expression)

    def visit_SourceElements(self, node):
        self.visit_statement_list(node.statements)

    def visit_StringLiteral(self, node):
        self.report_token(t.STRING, node.value)

    def visit_SwitchStatement(self, node):
        self.report_keyword(u'switch')
        self.parenthesize(node.expression)
        self.report_literal(u'{')
        cases = node.cases
        last_index = len(cases) - 1
        for i, case in enumerate(cases):
            self.visit(case)
            if i < last_index:
                if case.statements[-1:] and\
                        self.needs_semicolon(case.statements[-1]):
                    self.report_literal(u';')
        self.report_literal(u'}')

    def visit_ThisNode(self, node):
        self.report_keyword(u'this')

    def visit_Throw(self, node):
        self.report_keyword(u'throw')
        self.visit(node.exception)

    def visit_TrueNode(self, node):
        self.report_keyword(u'true')

    def visit_TryStatement(self, node):
        self.report_keyword(u'try')
        self.visit(node.try_block)
        if node.catch_var:
            self.report_keyword(u'catch')
            self.parenthesize(node.catch_var)
            self.visit(node.catch_block)
        if node.finally_block:
            self.report_keyword(u'finally')
            self.visit(node.finally_block)

    def visit_TypeofOperation(self, node):
        self.report_keyword(u'typeof')
        self.maybe_parens(node.expression, node)

    def visit_UnaryOperation(self, node):
        self.report_unary_op(node.op)
        self.maybe_parens(node.expression, node)

    def visit_VariableDeclaration(self, node):
        self.report_identifier(node.name)
        if node.value:
            self.report_literal(u'=')
            # TODO: should maybe parenthesize here
            self.visit(node.value)

    def visit_VariableStatement(self, node):
        self.report_keyword(u'var')
        self.visit_comma_list(node.declarations)

    def visit_VoidOperation(self, node):
        self.report_keyword(u'void')
        self.maybe_parens(node.expression, node)

    def visit_WhileStatement(self, node):
        self.report_keyword(u'while')
        self.parenthesize(node.condition)
        self.visit(node.body)

    def visit_WithStatement(self, node):
        self.report_keyword(u'with')
        self.parenthesize(node.expression)
        self.visit(node.statement)

def generate_code(ast, consumer=None):
    """
    Generate tokens for a given abstract syntax tree and report them to the
    given token consumer.
    """
    generator = CodeGenerator(consumer)
    generator.generate(ast)
