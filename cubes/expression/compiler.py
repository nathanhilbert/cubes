# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from .grammar import ExpressionParser, ExpressionSemantics

__all__ = [
        "ExpressionCompiler",
    ]


import json

class ASTNode(object):
    pass

class Atom(ASTNode):
    pass

class FunctionCall(Atom):
    def __init__(self, name, args):
        self.args = args
        self.name = name

    def __str__(self):
        return "%s(%s)" % (self.name, ", ".join(str(a) for a in self.args))

class VariableReference(Atom):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return ".".join(self.name)

    def __repr__(self):
        return self.__str__()

class Literal(Atom):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "%s" % str(self.value)

class UnaryOperator(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def __str__(self):
        return "({} {})".format(str(self.op), str(self.operand))

    def __repr__(self):
        return self.__str__()

class BinaryOperator(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __str__(self):
        return "({} {} {})".format(str(self.left), str(self.op), str(self.right))
    def __repr__(self):
        return self.__str__()

class Semantics(object):
    def NUMBER(self, ast):
        try:
            value = int(ast)
        except ValueError:
            value = float(ast)

        return Literal(value)

    def STRING(self, ast):
        return Literal(str(ast))

    def _default(self, ast, *args, **kwargs):
        if not args:
            return ast

        if isinstance(ast, ASTNode):
            return ast

        if not ast[1]:
            return ast[0]

        if args[0] == "binary":
            # AST: [left, [operator, right, operator, right, ...]]
            left = ast[0]
            op = ast[1][0]

            ops = ast[1][0::2]
            rights = ast[1][1::2]

            for op, right in zip(ops, rights):
                left = BinaryOperator(op, left, right)

            return left

        elif args[0] == "unary":
            # AST: [operator, right]
            op = ast[0]
            operand = ast[1]
            return UnaryOperator(op, operand)
        else:
            raise Exception("Unknown args %s" % args)

    def atom(self, ast):
        if ast.value is not None:
            return ast["value"]
        elif ast.ref is not None:
            if ast.get("args"):
                return FunctionCall(ast.ref, ast.args)
            else:
                return ast.ref
        elif ast.expr is not None:
            return ast.expr
        else:
            raise Exception("Unhandled AST: %s" % ast)

    def reference(self, ast):
        return VariableReference(ast)

class ExpressionCompiler(object):
    def __init__(self):
        pass

    def compile(self, text):
        parser = ExpressionParser()

        ast = parser.parse(text,
                rule_name="start",
                comments_re="#.*",
                ignorecase=False,
                semantics=Semantics())

        return ast
