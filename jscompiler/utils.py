"""
Utilities for working with abstract syntax tree nodes and values.
"""
from bigrig.utils import is_identifier_start, is_identifier_part
from bigrig.constants import RESERVED_NAMES, KEYWORDS
from bigrig.node import copy_node_attrs

DISALLOWED = set()
DISALLOWED.update(RESERVED_NAMES)
DISALLOWED.update(KEYWORDS)

def is_identifier_or_keyword(string):
    """
    Checks to see if a given string value is lexigraphically valid as an
    identifier or keyword.
    """
    if not string:
        return False
    num_chars = len(string)
    if not is_identifier_start(string[0]):
        return False
    if num_chars > 1:
        for char in string[1:]:
            if not is_identifier_part(char):
                return False
    return True

def is_valid_property_name(name):
    """
    Is the given name suitable for use as a property name?
    """
    if is_identifier_or_keyword(name):
        return name not in DISALLOWED
    return False

def build_new_node(old_node, *fields):
    """
    Build a new node of the same class and metadata as the given node, but
    with the given field values.
    """
    NodeClass = old_node.__class__
    new_node = NodeClass(*fields)
    copy_node_attrs(old_node, new_node)
    return new_node

def is_name(node, value):
    """
    Is the given node a ``Name`` with the given value?
    """
    if not isinstance(node, ast.Name):
        return False
    return node.value == value
