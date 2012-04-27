"""
Utilities for renaming locals in scopes to the shortest possible names without
interfering with the global scope.
"""
from collections import Counter

from bigrig.ast import Name, VariableDeclaration
from bigrig.node import copy_node_attrs
from bigrig.visitor import NodeTransformer

from .scope_builder import Scope, ScopeBuildingVisitor, ScopeVisitor
from .name_generator import NameGenerator
from .utils import build_new_node

#
# ``with`` tracking scope
# 

class WithTrackingScopeMixin(object):
    """
    Adds a utility to mark ``with`` statement usage in scopes.
    """
    def __init__(self, *args, **kwargs):
        self.uses_with = False
        super(WithTrackingScopeMixin, self).__init__(*args, **kwargs)

    def mark_uses_with(self):
        self.uses_with = True
        if self.parent is not None:
            self.parent.mark_uses_with()

class WithTrackingScope(WithTrackingScopeMixin, Scope):
    """
    A concrete ``with`` tracking ``Scope`` subclass.
    """
    pass

class WithTrackingScopeBuildingVisitorMixin(object):
    """
    Marks ``with`` usage in a scope.
    """
    def visit_WithStatement(self, node):
        self.scope.mark_uses_with()
        return super(WithTrackingScopeBuildingVisitorMixin, self).generic_visit(node)

class WithTrackingScopeBuildingVisitor(WithTrackingScopeBuildingVisitorMixin, ScopeBuildingVisitor):
    """
    A concrete implementation of a ``with`` tracking scope visitor.
    """
    pass

#
# Reference tracking scope
#

class ReferenceScopeMixin(object):
    """
    Adds reference tracking information to symbols declared in scopes.
    """
    def __init__(self, *args, **kwargs):
        self.reference_counts = Counter()
        self.references = {}
        super(ReferenceScopeMixin, self).__init__(*args, **kwargs)

    def declare_reference(self, name):
        """
        Mark the name as referenced in this scope and its parents until
        the scope in which it is declared is hit, at which point we do some
        usage frequency accounting.
        """
        self.references[name] = self.resolve_name(name)
        if name in self.declarations:
            self.reference_counts[name] += 1
        elif self.parent is not None:
            self.parent.declare_reference(name)

class ReferenceAddingVisitorMixin(object):
    """
    Declares references for all seen ``Name`` nodes.
    """
    def visit_Name(self, node):
        self.scope.declare_reference(node.value)
        super(ReferenceAddingVisitorMixin, self).generic_visit(node)

class ReferenceAddingVisitor(ReferenceAddingVisitorMixin, ScopeVisitor):
    """
    A concrete implementation of a reference tracking visitor.
    """
    pass

#
# ``eval`` tracking scope
#

class EvalTrackingScopeMixin(object):
    """
    Adds ``eval`` call tracking to scopes.
    """
    def __init__(self, *args, **kwargs):
        self._uses_eval = False
        super(EvalTrackingScopeMixin, self).__init__(*args, **kwargs)

    def uses_eval(self):
        """
        Returns a boolean value representing whether or not ``eval`` is
        referenced in this scope or subscopes, but only if the name ``eval``
        has not been redefined in this or any parent scopes.
        """
        if self.has_declaration('eval') is not None:
            return False
        return self._uses_eval

    def mark_uses_eval(self):
        """
        Mark this scope and its parents as referencing the ``eval`` name.
        """
        self._uses_eval = True
        if self.parent is not None:
            self.parent.mark_uses_eval()

class EvalTrackingScope(EvalTrackingScopeMixin, Scope):
    """
    A concrete implementation of an ``eval`` reference tracking scope.
    """
    pass

class EvalTrackingScopeBuildingVisitorMixin(object):
    """
    Adds the ability for a visitor to mark ``eval`` reference tracking scopes.
    """
    scope_class = EvalTrackingScope

    def visit_Name(self, node):
        node = super(EvalTrackingScopeBuildingVisitorMixin, self).generic_visit(node)
        if node.value == u'eval':
            self.scope.mark_uses_eval()
        return node

#
# Rename scope
#

class RenameScopeMixin(object):
    """
    A scope that renames locally defined symbols if ``eval`` is not referenced
    or ``with`` statements are not used in this or any child scope.
    """
    def __init__(self, *args, **kwargs):
        self.original_to_new = {}
        self.new_to_original = {}
        super(RenameScopeMixin, self).__init__(*args, **kwargs)

    def is_protected(self):
        """
        A helper to determine whether symbols in this scope are allowed to be
        renamed.
        """
        return self.uses_eval() or self.uses_with or self.parent is None

    def get_name(self, name):
        """
        Get the new name for a given name or return the given if no new name
        exists.
        """
        if name in self.original_to_new:
            return self.original_to_new[name]
        elif self.parent is not None:
            return self.parent.get_name(name)
        return name

    def build_name_generator(self):
        return NameGenerator()

    def resolve_new_name(self, name):
        if name in self.new_to_original:
            return self.new_to_original[name]
        elif self.parent is not None:
            return self.parent.resolve_new_name(name)
        return None

    def generate_names(self):
        """
        Generates new names for all locally declared symbols.
        """
        # If we're not allowed to rename, bail
        if self.is_protected():
            return
        
        # Let's keep track of the new names for references used in this scope
        # so we don't stomp on them.
        disallowed = set()
        for ref in self.references:
            disallowed.add(self.get_name(ref))

        # Finally, for the locally defined symbols we generate the shortest
        # allowed names in order of usage frequency
        name_generator = NameGenerator()
        for name, count in self.reference_counts.most_common():
            new_name = name_generator.next()
            while new_name in disallowed:
                new_name = name_generator.next()
            self.original_to_new[name] = new_name
            self.new_to_original[new_name] = name


class RenameScope(
        RenameScopeMixin, ReferenceScopeMixin, EvalTrackingScopeMixin,
        WithTrackingScopeMixin, Scope
      ):
    """
    A concrete implementation of a local declaration renaming scope.
    """
    pass


class RenameScopeBuildingVisitor(
        WithTrackingScopeBuildingVisitorMixin,
        EvalTrackingScopeBuildingVisitorMixin,
        ScopeBuildingVisitor
      ):
    """
    A visitor that can build a tree scoped with ``RenameScope``.
    """
    scope_class = RenameScope


class RenameTransformer(NodeTransformer):
    """
    An abstract syntax tree transformer that returns a new tree with local
    declarations renamed if possible and references replaced with the correct
    new symbol names.
    """
    def __init__(self, scope=None):
        self.scope = scope
        super(RenameTransformer, self).__init__()

    def get_name(self, name):
        return self.scope.get_name(name)

    def visit_Program(self, node):
        self.scope = scope = node.scope
        statements = self.visit(node.statements)
        self.scope = scope.parent
        return build_new_node(node, statements)

    def visit_FunctionDeclaration(self, node):
        self.scope = scope = node.scope
        scope.generate_names()
        parameters = self.visit_Parameters(node.parameters)
        body = self.visit(node.body)
        self.scope = scope.parent
        name = self.get_name(node.name)
        return build_new_node(node, name, parameters, body)

    def visit_FunctionExpression(self, node):
        self.scope = scope = node.scope
        scope.generate_names()
        name = self.get_name(self.visit(node.name))
        parameters = self.visit_Parameters(node.parameters)
        body = self.visit(node.body)
        new_node = build_new_node(node, name, parameters, body)
        self.scope = scope.parent
        return new_node

    def visit_VariableDeclaration(self, node):
        new_node = self.generic_visit(node)
        name = self.get_name(new_node.name)
        NodeClass = new_node.__class__
        return_node = NodeClass(name, new_node.value)
        copy_node_attrs(node, return_node)
        return return_node

    def visit_Name(self, node):
        name = self.get_name(node.value)
        return build_new_node(node, name)

    def visit_Parameters(self, node):
        return [self.get_name(name) for name in node]

#
# Utilities
#

def add_rename_scopes(ast):
    """
    Transform the abstract syntax tree to contain rename scope information.
    """
    visitor = RenameScopeBuildingVisitor()
    new_ast = visitor.visit(ast)
    return new_ast

def add_references(ast):
    """
    Walk the tree adding reference tracking information to the scopes.
    """
    visitor = ReferenceAddingVisitor()
    visitor.visit(ast)
    return ast

def rename_scoped_tree(ast):
    """
    Use the rename scope information to rewrite references to their new,
    hopefully much shorter, names.
    """
    visitor = RenameTransformer()
    new_ast = visitor.visit(ast)
    return new_ast

def rename_locals(ast):
    """
    Transform the tree by performing a scoped tree rewriting pass, a reference
    tracking pass, and finally a tree rewriting pass.
    """
    new_ast = add_rename_scopes(ast)
    new_ast = add_references(new_ast)
    new_ast = rename_scoped_tree(new_ast)
    return new_ast
