# -*- coding: utf-8 -*-
# Copyright © 2014, 2015 Casey Dahlin, John H. Dulaney
#
# This file is part of PyM.
#
# PyM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# PyM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# PyM.  If not, see <http://www.gnu.org/licenses/>.

import re

class KeyParser(object):
    """
    A class for parsing a key sequence
    """

    def __init__(self):
        def func(x): return x
        self.reset()
        self.filt = func

    def clone(self):
        raise NotImplementedError("Key Parser does not implement clone()")

    def offer(self, key):
        raise NotImplementedError("Key Parser does not implement offer()")

    def get_parse(self):
        raise NotImplementedError("Key Parser does not implement get_parse()")

    def reset(self):
        self.ready = True
        self.complete = False

    def deep_nest(self):
        return self.nest()

    def nest(self):
        return str(self)

    def __repr__(self):
        return "K'" + str(self) + "'"

class UnitKeyParser(KeyParser):
    """
    A KeyParser that wants a single key.
    """

    def __init__(self, key):
        KeyParser.__init__(self)
        self.key = key

    def clone(self):
        return UnitKeyParser(self.key)

    def offer(self, key):
        if not self.ready:
            return False
        self.ready = False
        self.complete = (self.key == key)
        return self.complete

    def get_parse(self):
        if self.complete:
            return self.filt(self.key)
        return None

    def __str__(self):
        if len(self.key) == 1 and not self.key in "<>#@?|()":
            return self.key
        return "<" + self.key + ">"

class PrintableKeyParser(KeyParser):
    """
    A parser for printable keys
    """
    def clone(self):
        return PrintableKeyParser()

    def offer(self, key):
        if not self.ready:
            return False

        self.ready = False

        if len(key) == 1:
            self.complete = True
            self.key = key

        return self.complete

    def get_parse(self):
        if self.complete:
            return self.filt(self.key)
        return None

    def __str__(self):
        return "@"

class NumberKeyParser(KeyParser):
    """
    A KeyParser that wants a number
    """
    def clone(self):
        return NumberKeyParser()

    def offer(self, key):
        if not self.ready:
            return False

        if not self.complete and key == "0":
            self.ready = False
        elif re.match(r'[0-9]', key):
            self.complete = True
            self.number *= 10
            self.number += int(key)
        else:
            self.ready = False

        return self.ready

    def get_parse(self):
        if self.complete:
            return self.filt(self.number)
        return None

    def reset(self):
        KeyParser.reset(self)
        self.number = 0

    def __str__(self):
        return "#"

class OptionalKeyParser(KeyParser):
    """
    A KeyParser that optionally matches another key parser
    """
    def __init__(self, other):
        self.other = other
        KeyParser.__init__(self)

    def clone(self):
        return OptionalKeyParser(self.other.clone())

    def offer(self, key):
        if not self.ready:
            return False

        ret = self.other.offer(key)

        self.ready = self.other.ready
        self.complete = self.other.complete or not self.ready

        return ret

    def get_parse(self):
        return self.filt(self.other.get_parse())

    def reset(self):
        KeyParser.reset(self)
        self.other.reset()

    def __str__(self):
        return self.other.deep_nest() + "?"

class SequenceKeyParser(KeyParser):
    """
    Parse a sequence of keys
    """
    def __init__(self, *others):
        self.others = others
        KeyParser.__init__(self)
        self.loc = 0

    def clone(self):
        return SequenceKeyParser(*[ x.clone() for x in self.others ])

    def reset(self):
        KeyParser.reset(self)
        self.loc = 0
        for o in self.others:
            o.reset()

    def get_parse(self):
        if not self.complete:
            return None

        return self.filt([ x.get_parse() for x in self.others ])

    def offer(self, key):
        if not self.ready:
            return False

        other = self.others[self.loc]
        ret = False

        while not ret:
            ret = other.offer(key)

            if other.ready:
                return True

            if not other.complete:
                self.ready = False
                return False

            self.loc += 1

            if self.loc >= len(self.others):
                self.complete = True
                self.ready = False
                return True

            other = self.others[self.loc]

        return True

    def deep_nest(self):
        return "(" + str(self) + ")"

    def __str__(self):
        return "".join([x.nest() for x in self.others])

class ChoiceKeyParser(KeyParser):
    """
    Select between several parses
    """
    def __init__(self, *others):
        self.others = others
        KeyParser.__init__(self)

    def clone(self):
        return ChoiceKeyParser(*[ x.clone() for x in self.others ])

    def reset(self):
        KeyParser.reset(self)
        for o in self.others:
            o.reset()

    def offer(self, key):
        if not self.ready:
            return False

        ret = False
        self.ready = False
        self.complete = False

        for o in self.others:
            ret = ret or o.offer(key)
            self.ready = self.ready or o.ready
            self.complete = self.complete or o.complete

        self.ready = self.ready and not self.complete

        return ret

    def get_parse(self):
        if not self.complete:
            return None

        for o in self.others:
            if o.complete:
                return self.filt(o.get_parse())
        raise # Unreachable

    def nest(self):
        return "(" + str(self) + ")"

    def __str__(self):
        return "|".join([x.nest() for x in self.others])

class InvalidKeyExpression(Exception):
    """
    Exception thrown when there is an error in parsing a key expression
    """
    pass

parse_macros = {}

def parse_key_expr(key_expr):
    """
    Parse a key expression identifying sequences of keys that might trigger an
    action.
    """

    stack = []
    escaped = False
    macroed = False

    def quiesce():
        sequence = []
        choose = []

        while len(stack) and stack[-1] != '(':
            item = stack.pop()

            if item == '|':
                if len(sequence) == 0:
                    raise InvalidKeyExpression("Empty choice")
                sequence.reverse()
                if len(sequence) == 1:
                    if isinstance(sequence[0], ChoiceKeyParser):
                        k = list(sequence[0].others)
                        k.reverse()
                        choose += k
                    else:
                        choose.append(*sequence)
                else:
                    choose.append(SequenceKeyParser(*sequence))
                sequence = []
            else:
                sequence.append(item)

        if len(sequence) == 0:
            raise InvalidKeyExpression("Empty choice")
        sequence.reverse()
        if len(sequence) == 1:
            choose.append(*sequence)
        else:
            choose.append(SequenceKeyParser(*sequence))
        choose.reverse()

        if len(choose) == 1:
            return choose[0]
        else:
            return ChoiceKeyParser(*choose)

    for k in key_expr:
        if k == ">" and not escaped:
            raise InvalidKeyExpression("Unmatched '>'")

        if k == ">" and len(stack[-1]) > 0:
            escaped = False
            stack[-1] = UnitKeyParser(stack[-1])
        elif macroed and k == "`":
            if not stack[-1] in parse_macros:
                raise InvalidKeyExpression("No such macro `"+stack[-1]+"`")
            macro = parse_macros[stack[-1]]
            stack[-1] = macro.clone()
            stack[-1].filt = macro.filt
            macroed = False
        elif escaped or macroed:
            stack[-1] += k
        elif k == "<":
            escaped = True
            stack.append("")
        elif k == "`":
            macroed = True
            stack.append("")
        elif k == "#":
            stack.append(NumberKeyParser())
        elif k == "@":
            stack.append(PrintableKeyParser())
        elif k == "?":
            if len(stack) == 0:
                raise InvalidKeyExpression("Unexpected '?' at start")
            if not isinstance(stack[-1], KeyParser):
                raise InvalidKeyExpression("Unexpected '?' following '"+k+"'")
            stack[-1] = OptionalKeyParser(stack[-1])
        elif k == "|" or k == "(":
            stack.append(k)
        elif k == ")":
            res = quiesce()
            if len(stack) == 0:
                raise InvalidKeyExpression("Unmatched ')'")
            stack[-1] = res
        else:
            stack.append(UnitKeyParser(k))

    if escaped:
        raise InvalidKeyExpression("Unmatched '`'")

    if macroed:
        raise InvalidKeyExpression("Unmatched '<'")

    ret = quiesce()

    if len(stack) == 0:
        return ret

    raise InvalidKeyExpression("Unmatched '('")

def key_macro(expr):
    """
    Define a new key macro
    """
    expr = parse_key_expr(expr)

    def deco(func):
        expr.filt = func
        name = func.__name__
        parse_macros[name] = expr
        return func
    return deco
