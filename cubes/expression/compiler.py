# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from expressions import Compiler, Variable

__all__ = [
        "ExpressionCompiler",
    ]


class ExpressionCompiler(Compiler):
    def __init__(self, context=None):
        self.context = context

    def _compile_literal(self, context, literal):
        return Literal(literal)

    def _compile_variable(self, context, reference):
        return VariableReference(reference)

    def _compile_operator(self, context, operator, left, right):
        return BinaryOperator(operator, left, right)

    def _compile_unary(self, context, operator, operand):
        return UnaryOperator(operator, operand)

    def _compile_function(self, conext, function, args):
        return FunctionCall(function, args)

    def _finalize(self, context, obj):
        return obj
