# -*- coding=utf -*-

from ...expressions import ExpressionCompiler, Variable
from ...expressions import STANDARD_AGGREGATE_FUNCTIONS
from ...errors import ExpressionError
import sqlalchemy.sql as sql

SQL_FUNCTIONS = [
    # String
    "lower", "upper", "left", "right", "substr",
    "lpad", "rpad", "replace",
    "concat", "repeat", "position",

    # Math
    "round", "trunc", "floor", "ceil",
    "mod", "remainder",
    "sign",

    "pow", "exp", "log", "log10",
    "sqrt",
    "cos", "sin", "tan",

    # Date/time
    "extract",

    # Conditionals
    "coalesce", "nullif", "case",

    # TODO: add map(value, match1, result1, match2, result2, ..., default)
    # "map",
]

# Add SQL-only aggregate functions here
SQL_AGGREGATE_FUNCTIONS =  STANDARD_AGGREGATE_FUNCTIONS + []

SQL_ALL_FUNCTIONS = SQL_FUNCTIONS + SQL_AGGREGATE_FUNCTIONS;

SQL_VARIABLES = [
    "current_date", "current_time", "local_date", "local_time"
]

# TODO: lstrip, rstrip, strip -> trim
# TODO: like

class SQLExpressionContext(object):
    def __init__(self, cube, builder, aggregate, constants=None):
        """Creates a SQL expression compiler context for `cube`. `builder` is
        a SQL `QueryBuilder` object, `aggregate` is a flag where `True` means
        that the expression is expected to be an aggregate expression."""
        self.cube = cube
        self.builder = builder
        self.aggregate = aggregate

        if aggregate:
            self.attributes = cube.all_aggregate_attributes
        else:
            self.attributes = cube.all_attributes

        self.attribute_names = set(attr.ref() for attr in self.attributes)

        self.constants = constants or {}

    def resolve(self, name):
        """Resolve variable `name` – return either a column, variable from a
        dictionary or a SQL constant (in that order)."""

        if name in self.attribute_names:
            # Get the raw column
            result = self.builder.snowflake.column(name)
        elif name in self.constants:
            result = self.constants[name]
        elif name in SQL_VARIABLES:
            result = getattr(sql.func, name)()
        else:
            raise ExpressionError("Unknown expression variable '{}' "
                                  "in cube {}".format(name, cube))

        return result

    def function(self, name):
        """Return a SQL function"""
        # TODO: check for function existence (allowed functions)
        sql_func = getattr(sql.func, func)
        return sql_func(*args)


class SQLExpressionCompiler(ExpressionCompiler):
    def __init__(self, context):
        super(SQLExpressionCompiler, self).__init__(context)

    def compile_operator(self, context, operator, op1, op2):
        if operator == "*":
            result = op1 * op2
        elif operator == "/":
            result = op1 / op2
        elif operator == "%":
            result = op1 % op2
        elif operator == "+":
            result = op1 + op2
        elif operator == "-":
            result = op1 - op2
        elif operator == "&":
            result = op1 & op2
        elif operator == "|":
            result = op1 | op2
        elif operator == "<":
            result = op1 < op2
        elif operator == "<=":
            result = op1 <= op2
        elif operator == ">":
            result = op1 > op2
        elif operator == ">=":
            result = op1 >= op2
        elif operator == "=":
            result = op1 == op2
        elif operator == "!=":
            result = op1 != op2
        elif operator == "and":
            result = sql.expression.and_(op1, op2)
        elif operator == "or":
            result = sql.expression.or_(op1, op2)
        else:
            raise SyntaxError("Unknown operator '%s'" % operator)

        return result

    def compile_variable(self, context, variable):
        name = operand.name
        result = self.context.resolve(name)
        return result

    def compile_unary(self, context, operator, operand):
        if operator == "-":
            result =  (- operand)
        elif operator == "+":
            result =  (+ operand)
        elif operator == "~":
            result =  (~ operand)
        elif operator == "not":
            result = sql.expression.not_(operand)
        else:
            raise SyntaxError("Unknown unary operator '%s'" % operator)

        return result

    def compile_function(self, context, func, args):
        func = context.function(func.name)
        return func(**args)


class TemporaryFoo(object):

    def aggregate_expression(self, aggregate, coalesce_measure=False):
        """Returns an expression that performs the aggregation of measure
        `aggregate`. The result's label is the aggregate's name.  `aggregate`
        has to be `MeasureAggregate` instance.

        If aggregate function is post-aggregation calculation, then `None` is
        returned.

        Aggregation function names are case in-sensitive.

        If `coalesce_measure` is `True` then selected measure column is wrapped
        in ``COALESCE(column, 0)``.
        """
        # TODO: support aggregate.expression

        if aggregate.expression:
            compiler = SQLExpressionCompiler()
            expression = compiler.compile(aggregate.expressions, context)
            return expression

        # If there is no function specified, we consider the aggregate to be
        # computed in the mapping
        if not aggregate.function:
            # TODO: this should be depreciated in favor of aggreate.expression
            # TODO: Following expression should be raised instead:
            # raise ModelError("Aggregate '%s' has no function specified"
            #                 % str(aggregate))
            column = self.column(aggregate)
            return column

        function_name = aggregate.function.lower()
        function = self.browser.builtin_function(function_name, aggregate)

        if not function:
            return None

        expression = function(aggregate, self, coalesce_measure)

        return expression

