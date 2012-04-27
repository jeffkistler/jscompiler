from bigrig import ast

BINARY_OPS = {
    # Assignment
    u'=': 2,
    u'|=': 2,
    u'^=': 2,
    u'&=': 2,
    u'<<=': 2,
    u'>>=': 2,
    u'>>>=': 2,
    u'+=': 2,
    u'-=': 2,
    u'*=': 2,
    u'/=': 2,
    u'%=': 2,
    # Binary Operators
    u',': 1,
    u'||': 4,
    u'&&': 5,
    u'|': 6,
    u'^': 7,
    u'&': 8,
    u'<<': 11,
    u'>>': 11,
    u'>>>': 11,
    u'+': 12,
    u'-': 12,
    u'*': 13,
    u'/': 13,
    u'%': 13,
    # Comparison Operators
    u'==': 9,
    u'!=': 9,
    u'!==': 9,
    u'===': 9,
    u'<': 10,
    u'>': 10,
    u'<=': 10,
    u'>=': 10,
    u'instanceof': 10,
    u'in': 10,
}

UNARY_OPS = {
    u'!': 14,
    u'~': 14,
    u'+': 14,
    u'-': 14,
}

NODE_TYPE_TO_PRECEDENCE = {
    ast.TypeofOperation: 14,
    ast.DeleteOperation: 14,
    ast.VoidOperation: 14,
    ast.PrefixCountOperation: 15,
    ast.PostfixCountOperation: 15,
    ast.Conditional: 3,
    ast.CallExpression: 16,
    ast.DotProperty: 17,
    ast.BracketProperty: 17,
    ast.NewExpression: 17,
}

def precedence(node):
    try:
        if node.__class__ in NODE_TYPE_TO_PRECEDENCE:
            return NODE_TYPE_TO_PRECEDENCE[node.__class__]
        elif isinstance(node, ast.UnaryOperation):
            return UNARY_OPS[node.op]
        return BINARY_OPS[node.op]
    except (KeyError, AttributeError):
        return 20
