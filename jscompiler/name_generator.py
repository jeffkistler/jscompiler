import string

from bigrig.utils import is_identifier_start, is_identifier_part

IDENTIFIER_START_CHARS = unicode(string.ascii_letters + "$_")
IDENTIFIER_CHARS = unicode(IDENTIFIER_START_CHARS + string.digits)
DISALLOWED_NAMES = frozenset((
    u'as', u'is', u'do', u'if', u'in', u'for', u'int', u'new', u'try', u'use', u'var'
))

def build_names_list(disallowed):
    possible_names = []
    for first in IDENTIFIER_START_CHARS:
        possible_names.append(first)
    for first in IDENTIFIER_START_CHARS:
        for second in IDENTIFIER_CHARS:
            ident = u'%s%s' % (first, second)
            if ident in disallowed:
                continue
            possible_names.append(ident)
    for first in IDENTIFIER_START_CHARS:
        for second in IDENTIFIER_CHARS:
            for third in IDENTIFIER_CHARS:
                ident = u'%s%s%s' % (first, second, third)
                if ident in disallowed:
                    continue
                possible_names.append(ident)
    return possible_names

SHORTNAMES = build_names_list(DISALLOWED_NAMES)

def is_identifier(string):
    if not len(string):
        return False
    if not is_identifier_start(string[0]):
        return False
    for char in string[1:]:
        if not is_identifier_part(char):
            return False
    return True


class NameGenerator(object):
    def __init__(self, name_list=SHORTNAMES, index=0):
        self.name_list = name_list
        self.index = index

    def next(self):
        name = self.name_list[self.index]
        self.index += 1
        return name
