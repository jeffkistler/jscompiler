"""
A base name scope class and utilities for walking and transforming scoped
abstract syntax trees.
"""
from collections import OrderedDict

from bigrig import ast
from bigrig.node import copy_node_attrs
from bigrig.visitor import NodeTransformer, NodeVisitor

#
# Base Scope class
#

class Scope(object):
    """
    A function or global name scope.
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.declarations = OrderedDict()
        self.function_declarations = OrderedDict()
        self.parameter_declarations = OrderedDict()
        self.variable_declarations = OrderedDict()

    def declare_symbol(self, name, node):
        self.declarations[name] = node

    def declare_function(self, name, node):
        self.function_declarations[name] = node
        self.declare_symbol(name, node)

    def declare_parameter(self, name, node):
        self.parameter_declarations[name] = node
        self.declare_symbol(name, node)

    def declare_variable(self, name, node):
        self.variable_declarations[name] = node
        self.declare_symbol(name, node)

    def resolve_name(self, name):
        if name in self.declarations:
            return self
        elif self.parent is not None:
            return self.parent.resolve_name(name)
        return None

    def has_declaration(self, name):
        return self.resolve_name(name) is not None

    def declared_in_scope(self, name):
        return name in self.declarations

#
# Scoped Nodes
#

class FunctionDeclaration(ast.FunctionDeclaration):
    abstract = False
    attributes = ('scope',)

class FunctionExpression(ast.FunctionExpression):
    abstract = False
    attributes = ('scope',)

class Program(ast.Program):
    abstract = False
    attributes = ('scope',)

#
# Scope Builder
#

class ScopeBuildingVisitor(NodeTransformer):
    """
    Walk the tree building scoped nodes along the way.
    """
    scope_class = Scope
    program_class = Program
    function_declaration_class = FunctionDeclaration
    function_expression_class = FunctionExpression
    variable_declaration_class = ast.VariableDeclaration

    def __init__(self, scope=None):
        self.scope = scope or self.scope_class()
        super(ScopeBuildingVisitor, self).__init__()

    def push_scope(self):
        self.scope = self.scope_class(self.scope)
        return self.scope

    def pop_scope(self):
        scope = self.scope
        self.scope = scope.parent
        return scope

    def create_program(self, statements):
        return self.program_class(
            statements, scope=self.pop_scope()
        )

    def visit_Program(self, node):
        """
        Attach a scope to the program node if there isn't one.
        """
        self.push_scope()
        statements = self.visit(node.statements)
        program = self.create_program(statements)
        copy_node_attrs(node, program)
        return program

    def create_function_expression(self, name, parameters, body):
        return self.function_expression_class(
            name, parameters, body, scope=self.pop_scope()
        )

    def visit_FunctionExpression(self, node):
        """
        If named, this will add the function node to its own scope.
        """
        name = self.visit(node.name)
        scope = self.push_scope()
        if name:
            scope.declare_function(name, node)
        new_parameters = []
        for parameter in node.parameters:
            scope.declare_parameter(parameter, node)
            new_parameters.append(parameter)
        new_body = self.visit(node.body)
        new_function = self.create_function_expression(
            name, new_parameters, new_body
        )
        copy_node_attrs(node, new_function)
        return new_function

    def create_function_declaration(self, name, parameters, body):
        return self.function_declaration_class(
            name, parameters, body, scope=self.pop_scope()
        )

    def visit_FunctionDeclaration(self, node):
        """
        Adds the function to current scope and creates a new top level scope
        for the declared function.
        """
        name = self.visit(node.name)
        self.scope.declare_function(name, node)
        scope = self.push_scope()
        new_parameters = []
        for parameter in node.parameters:
            scope.declare_parameter(parameter, node)
            new_parameters.append(parameter)
        new_body = self.visit(node.body)
        new_function = self.create_function_declaration(
            name, new_parameters, new_body
        )
        copy_node_attrs(node, new_function)
        return new_function

    def create_variable_declaration(self, name, value):
        return self.variable_declaration_class(name, value)

    def visit_VariableDeclaration(self, node):
        """
        Declare the name in the current scope.
        """
        name = self.visit(node.name)
        value = self.visit(node.value)
        self.scope.declare_variable(name, value)
        new_declaration = self.create_variable_declaration(name, value)
        copy_node_attrs(node, new_declaration)
        return new_declaration

def add_scopes(ast):
    """
    Transform the abstract syntax tree into one with function scopes.
    """
    visitor = ScopeBuildingVisitor()
    new_ast = visitor.visit(ast)
    return new_ast

#
# Visitor base classes
#

class ScopeVisitor(NodeVisitor):
    """
    A base class for a tree visitor that keeps track of current scope.
    """
    def __init__(self, scope=None):
        self.scope = scope
        super(ScopeVisitor, self).__init__()

    def visit_scope_node(self, node):
        self.scope = node.scope
        self.generic_visit(node)
        self.scope = self.scope.parent

    visit_FunctionDeclaration = visit_scope_node
    visit_FunctionExpression = visit_scope_node
    visit_Program = visit_scope_node

class ScopedNodeTransformer(NodeTransformer):
    """
    A base class for a tree transformer that keeps track of current scope.
    """
    def __init__(self, scope=None):
        self.scope = scope
        super(ScopedNodeTransformer, self).__init__()

    def visit_scope_node(self, node):
        self.scope = node.scope
        new_node = self.generic_visit(node)
        self.scope = self.scope.parent
        return new_node

    visit_FunctionDeclaration = visit_scope_node
    visit_FunctionExpression = visit_scope_node
    visit_Program = visit_scope_node

    
